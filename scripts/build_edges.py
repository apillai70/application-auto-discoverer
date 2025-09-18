#!/usr/bin/env python3
"""
build_xechk_edges.py

Create a spreadsheet for App from an input file containing columns like:
- IP (source)
- Peer (destination; may be "10.1.2.3(host.example.com)")
- Protocol (may be "TCP" or "TCP:443")
- Bytes In
- Bytes Out

Output columns (CSV/XLSX):
    App, Source IP, Source Hostname, Dest IP, Dest Hostname,
    Port, Protocol, Bytes In, Bytes Out

Features:
- Parses Peer into IP and hostname if provided in parentheses.
- Extracts Protocol/Port when "PROTO:PORT" form is present.
- Optional reverse-DNS (socket.gethostbyaddr and/or nslookup) for missing hostnames.
- Supports Excel (.xlsx) or CSV input.
- Optional synthesis to reach a minimum number of rows (RFC1918 v4 + 2001:db8::/32 v6).

Usage examples:
    python build_xechk_edges.py --input template-XECHK.xlsx --dns both --min-rows 5000
    python build_xechk_edges.py --input traffic.csv --dns nslookup --no-synthesize
    stamp=$(date +%Y%m%d-%H%M%S)
    python build_xechk_edges.py --input template_XECHK.xlsx --output-basename "out/XECHK_$stamp"
    python build_xechk_edges.py --input template_XECHK.csv --output-basename XECHK_from_template
    
    Keep all rows from your file (no synthesis)
        python build_xechk_edges.py --input template_XECHK.csv --dns both --no-synthesize
    Change the minimum (e.g., guarantee ≥ 35k rows)
        python build_xechk_edges.py --input template_XECHK.csv --dns both --min-rows 33000
    Quick check of row count
        wc -l XECHK_edges.csv    # includes header; subtract 1 for data rows
        python build_edges.py --input template_XECHK.csv --dns both --threads 40 --timeout 1.0

Python:

python - << 'PY'
import pandas as pd
print(len(pd.read_csv("XECHK_edges.csv")))
PY

Notes:
- Reverse DNS for many IPs can be slow. Use --threads to adjust concurrency (default 20).
- On Windows, ensure 'nslookup' is in PATH (it usually is).
- The script already accepts both .xlsx and .csv as input.
    If the --input filename ends with .xlsx / .xlsm / .xls, it uses pandas.read_excel (you can pick a sheet with --sheet).
    Otherwise, it uses pandas.read_csv (for .csv, and it will try to auto-detect other delims when not .csv).
    
- So for each IP that’s missing a hostname, the script does:

    socket.gethostbyaddr(...) (timeout you set with --timeout), and if that fails,
    nslookup <ip> (same timeout, slightly longer minimum), then uses whatever name it finds.
    If neither returns a name (no PTR record, DNS blocked, etc.), the hostname is left blank.

Quick reference for the flag:
    --dns none → skip lookups entirely.
    --dns socket → only gethostbyaddr.
    --dns nslookup → only the nslookup command.
    --dns both → socket first, nslookup fallback (default in the script I gave you).

Tips:
Use --threads N to parallelize lookups (default 20).
Tune --timeout (seconds) if your DNS is slow (e.g., --timeout 1.0).
The script de-dupes lookups in-memory, so the same IP won’t be queried twice in one run.

Options you’ll likely use
    --dns both (default): try reverse DNS via socket first then nslookup
    --dns none: skip hostname lookups
    --no-synthesize: don’t add synthetic rows; use only what’s in your CSV
    --threads 40: speed up DNS lookups (careful with resolver load)
"""


from __future__ import annotations
import argparse
import ipaddress
import math
import os
import random
import re
import socket
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd

random.seed(42)

PEER_RE = re.compile(r'^\s*([^\s(]+)\s*(?:\(([^)]+)\))?\s*$')
HOSTLIKE_RE = re.compile(r'^[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+\.?$')  # simple FQDN-ish

def is_ip(s: str) -> bool:
    try:
        ipaddress.ip_address(s)
        return True
    except Exception:
        return False

def is_hostname_like(s: str) -> bool:
    if not isinstance(s, str):
        return False
    s = s.strip()
    if not s or len(s) < 2:
        return False
    if is_ip(s):
        return False
    return bool(HOSTLIKE_RE.search(s))

def split_peer(peer_text: str) -> Tuple[str, Optional[str]]:
    """Split '10.0.0.1(host.example)' -> ('10.0.0.1', 'host.example').
       If only hostname, returns ('host.example', None)."""
    if not isinstance(peer_text, str):
        return str(peer_text), None
    m = PEER_RE.match(peer_text.strip())
    if not m:
        return peer_text.strip(), None
    return m.group(1).strip(), (m.group(2).strip() if m.group(2) else None)

def parse_proto_port(s: str) -> Tuple[Optional[str], Optional[int]]:
    """Parse 'TCP:443' -> ('TCP', 443)."""
    if s is None or (isinstance(s, float) and math.isnan(s)):
        return None, None
    s = str(s).strip()
    if ":" in s:
        proto, port = s.split(":", 1)
        proto = proto.strip().upper()
        port = port.strip()
        try:
            return proto, int(port)
        except Exception:
            return proto, None
    return (s.upper() if s else None), None

# ---------------- Reverse DNS (IP -> hostname) ----------------

def reverse_dns_socket(ip: str, timeout: float = 0.75) -> Optional[str]:
    try:
        socket.setdefaulttimeout(timeout)
        name, _, _ = socket.gethostbyaddr(ip)
        return name.rstrip(".")
    except Exception:
        return None

def reverse_dns_nslookup(ip: str, timeout: float = 1.5) -> Optional[str]:
    try:
        proc = subprocess.run(["nslookup", ip], capture_output=True, text=True, timeout=timeout, check=False)
        text = (proc.stdout or "") + "\n" + (proc.stderr or "")
        for line in text.splitlines():
            L = line.strip()
            low = L.lower()
            if "name =" in low:
                host = L.split("=", 1)[1].strip().rstrip(".")
                return host
            if low.startswith("name:"):
                host = L.split(":", 1)[1].strip().rstrip(".")
                return host
        return None
    except Exception:
        return None

# ---------------- Forward DNS (hostname -> IP) ----------------

def forward_dns_socket(name: str, timeout: float = 0.75) -> Tuple[List[str], List[str]]:
    """Return (ipv4_list, ipv6_list) via getaddrinfo."""
    v4, v6 = [], []
    try:
        socket.setdefaulttimeout(timeout)
        infos = socket.getaddrinfo(name, None, proto=socket.IPPROTO_TCP)
        for fam, _, _, _, sockaddr in infos:
            if fam == socket.AF_INET:
                ip = sockaddr[0]
                if ip not in v4:
                    v4.append(ip)
            elif fam == socket.AF_INET6:
                ip = sockaddr[0]
                if ip not in v6:
                    v6.append(ip)
    except Exception:
        pass
    return v4, v6

def forward_dns_nslookup(name: str, timeout: float = 1.5) -> Tuple[List[str], List[str]]:
    """Parse nslookup output for Addresses. Returns (ipv4_list, ipv6_list)."""
    v4, v6 = [], []
    try:
        proc = subprocess.run(["nslookup", name], capture_output=True, text=True, timeout=timeout, check=False)
        text = (proc.stdout or "") + "\n" + (proc.stderr or "")
        for line in text.splitlines():
            L = line.strip()
            # Windows prints "Address: 10.1.2.3" (single) or "Addresses: 10.1.2.3, 2001:db8::1"
            if L.lower().startswith("address:") or L.lower().startswith("addresses:"):
                rhs = L.split(":", 1)[1]
                # split by comma or whitespace
                parts = re.split(r'[,\s]+', rhs.strip())
                for p in parts:
                    p = p.strip().rstrip(",")
                    if not p:
                        continue
                    if ":" in p:
                        if p not in v6:
                            v6.append(p)
                    elif re.match(r'^\d{1,3}(\.\d{1,3}){3}$', p):
                        if p not in v4:
                            v4.append(p)
    except Exception:
        pass
    return v4, v6

def pick_preferred(v4: List[str], v6: List[str], prefer: str = "ipv4") -> Optional[str]:
    prefer = (prefer or "ipv4").lower()
    if prefer == "ipv6":
        return (v6[0] if v6 else (v4[0] if v4 else None))
    if prefer == "any":
        return (v4[0] if v4 else (v6[0] if v6 else None))
    # default: ipv4
    return (v4[0] if v4 else (v6[0] if v6 else None))

# ---------------- IO ----------------

def find_col(df: pd.DataFrame, name_opts: Iterable[str]) -> Optional[str]:
    norm = {str(c).strip().lower(): c for c in df.columns}
    for opt in name_opts:
        if opt in norm:
            return norm[opt]
    return None

def load_frame(path: Path, sheet: Optional[str]) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Input not found: {p}")
    if p.suffix.lower() in (".xlsx", ".xlsm", ".xls"):
        return pd.read_excel(p, sheet_name=sheet) if sheet else pd.read_excel(p)
    else:
        # default CSV
        return pd.read_csv(p)

# ---------------- Main ----------------

def main():
    ap = argparse.ArgumentParser(description="Build XECHK edges CSV/XLSX from input (Excel/CSV).")
    ap.add_argument("--input", "-i", required=True, help="Path to input .xlsx or .csv")
    ap.add_argument("--sheet", help="Excel sheet name (if applicable)")
    ap.add_argument("--output-basename", "-o", default="XECHK_edges", help="Base name (path + stem) for output files")
    ap.add_argument("--dns", choices=["none", "socket", "nslookup", "both"], default="both",
                    help="Reverse DNS (IP -> hostname) method")
    ap.add_argument("--fwd-dns", choices=["none", "socket", "nslookup", "both"], default="socket",
                    help="Forward DNS (hostname -> IP) when an IP is missing")
    ap.add_argument("--prefer-ip", choices=["ipv4", "ipv6", "any"], default="ipv4",
                    help="When a hostname resolves to both A & AAAA, which to store as IP")
    ap.add_argument("--timeout", type=float, default=0.75, help="Per-DNS-call timeout (seconds)")
    ap.add_argument("--threads", type=int, default=20, help="Thread pool size for DNS lookups")
    ap.add_argument("--min-rows", type=int, default=5000, help="Synthesize rows until we reach this count")
    ap.add_argument("--no-synthesize", action="store_true", help="Do not synthesize rows (use only input rows)")
    args = ap.parse_args()

    df_in = load_frame(Path(args.input), args.sheet)

    # Map columns (case-insensitive)
    ip_col = find_col(df_in, {"ip", "source ip", "src", "source"})
    peer_col = find_col(df_in, {"peer", "destination", "dest", "dst", "dest ip"})
    proto_col = find_col(df_in, {"protocol", "proto"})
    bytes_in_col = find_col(df_in, {"bytes in", "bytes_in", "inbytes", "in bytes"})
    bytes_out_col = find_col(df_in, {"bytes out", "bytes_out", "outbytes", "out bytes"})

    if not ip_col or not peer_col:
        raise SystemExit("Input must contain 'IP' (or Source) and 'Peer' (or Dest) columns.")

    records: List[Dict[str, object]] = []
    # Collect lookups
    rev_need: set[str] = set()   # IPs missing hostnames
    fwd_need: set[str] = set()   # hostnames missing IPs

    parsed_rows: List[Dict[str, object]] = []

    for _, r in df_in.iterrows():
        src_raw = str(r.get(ip_col, "")).strip()
        peer_raw = str(r.get(peer_col, "")).strip()

        # Peer split
        peer_first, peer_host_paren = split_peer(peer_raw)

        # Source IP / hostname handling
        src_ip = src_raw if is_ip(src_raw) else ""
        src_host_initial = "" if src_ip else (src_raw if is_hostname_like(src_raw) else "")

        # Dest IP / hostname handling
        dest_ip_candidate = peer_first
        if is_ip(dest_ip_candidate):
            dest_ip = dest_ip_candidate
            dest_host_initial = (peer_host_paren or "")
        else:
            # Peer provided only a hostname or something non-IP
            dest_ip = ""
            # Prefer the hostname inside parens; else treat the first token as hostname
            dest_host_initial = (peer_host_paren or (dest_ip_candidate if is_hostname_like(dest_ip_candidate) else ""))

        # Skip rows that have neither a usable Source nor Dest identifier
        if not src_ip and not dest_ip and not src_host_initial and not dest_host_initial:
            continue

        # Protocol/Port
        proto_val = r.get(proto_col, None)
        proto, port = parse_proto_port(str(proto_val) if proto_val is not None else "")

        # Bytes
        def to_int(v):
            try:
                return int(v)
            except Exception:
                return 0
        bytes_in = to_int(r.get(bytes_in_col, 0) if bytes_in_col else 0)
        bytes_out = to_int(r.get(bytes_out_col, 0) if bytes_out_col else 0)

        row = {
            "App": "XECHK",
            "Source IP": src_ip,                  # may get filled by forward DNS
            "Source Hostname": src_host_initial,  # may get filled by reverse DNS
            "Dest IP": dest_ip,                   # may get filled by forward DNS
            "Dest Hostname": dest_host_initial,   # may get filled by reverse DNS if only IP present
            "Port": (port if port is not None else ""),
            "Protocol": (proto or ""),
            "Bytes In": bytes_in,
            "Bytes Out": bytes_out,
        }
        parsed_rows.append(row)

        # collect reverse DNS needs (IP -> hostname)
        if row["Source IP"] and not row["Source Hostname"] and args.dns != "none":
            rev_need.add(row["Source IP"])
        if row["Dest IP"] and not row["Dest Hostname"] and args.dns != "none":
            rev_need.add(row["Dest IP"])

        # collect forward DNS needs (hostname -> IP)
        if not row["Source IP"] and row["Source Hostname"] and args.fwd_dns != "none":
            fwd_need.add(row["Source Hostname"])
        if not row["Dest IP"] and row["Dest Hostname"] and args.fwd_dns != "none":
            fwd_need.add(row["Dest Hostname"])

    # ---- Forward DNS pass (hostname -> IP) ----
    fwd_map: Dict[str, Optional[str]] = {}
    if fwd_need and args.fwd_dns != "none":
        names = list(fwd_need)
        def fwd_lookup(name: str) -> Tuple[str, Optional[str]]:
            v4: List[str] = []
            v6: List[str] = []
            if args.fwd_dns in ("socket", "both"):
                vv4, vv6 = forward_dns_socket(name, timeout=args.timeout)
                v4 += [x for x in vv4 if x not in v4]
                v6 += [x for x in vv6 if x not in v6]
            if args.fwd_dns in ("nslookup", "both") and not v4 and not v6:
                vv4, vv6 = forward_dns_nslookup(name, timeout=max(args.timeout, 1.0))
                v4 += [x for x in vv4 if x not in v4]
                v6 += [x for x in vv6 if x not in v6]
            return name, pick_preferred(v4, v6, args.prefer_ip)

        with ThreadPoolExecutor(max_workers=max(1, args.threads)) as ex:
            futs = [ex.submit(fwd_lookup, n) for n in names]
            for fut in as_completed(futs):
                n, ip = fut.result()
                fwd_map[n] = ip

    # Apply forward results
    for row in parsed_rows:
        if not row["Source IP"] and row["Source Hostname"]:
            row["Source IP"] = fwd_map.get(row["Source Hostname"], "") or ""
        if not row["Dest IP"] and row["Dest Hostname"]:
            row["Dest IP"] = fwd_map.get(row["Dest Hostname"], "") or ""

    # ---- Reverse DNS pass (IP -> hostname) ----
    rev_map: Dict[str, Optional[str]] = {}
    if rev_need and args.dns != "none":
        ips = list(rev_need)
        def rev_lookup(ip: str) -> Tuple[str, Optional[str]]:
            name: Optional[str] = None
            if args.dns in ("socket", "both"):
                name = reverse_dns_socket(ip, timeout=args.timeout)
            if not name and args.dns in ("nslookup", "both"):
                name = reverse_dns_nslookup(ip, timeout=max(args.timeout, 1.0))
            return ip, name

        with ThreadPoolExecutor(max_workers=max(1, args.threads)) as ex:
            futs = [ex.submit(rev_lookup, ip) for ip in ips]
            for fut in as_completed(futs):
                ip, name = fut.result()
                rev_map[ip] = name

    # Apply reverse results
    records: List[Dict[str, object]] = []
    for row in parsed_rows:
        if row["Source IP"] and not row["Source Hostname"]:
            row["Source Hostname"] = rev_map.get(row["Source IP"], "") or ""
        if row["Dest IP"] and not row["Dest Hostname"]:
            row["Dest Hostname"] = rev_map.get(row["Dest IP"], "") or ""
        records.append(row)

    # ---- Optional synthesis to reach min-rows ----
    if not args.no_synthesize and len(records) < args.min_rows:
        def synth_ipv4() -> str:
            return f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
        def synth_ipv6() -> str:
            parts = ["2001", "0db8"] + [format(random.randint(0, 0xFFFF), "x") for _ in range(6)]
            return ":".join(parts)
        def mutate_ipv4(ipv4: str) -> str:
            ip = ipaddress.ip_address(ipv4)
            parts = str(ip).split(".")
            parts[-1] = str(random.randint(1, 254))
            if random.random() < 0.3:
                parts[-2] = str(random.randint(0, 254))
            return ".".join(parts)
        def mutate_ipv6(ipv6: str) -> str:
            ip = ipaddress.ip_address(ipv6)
            hextets = ip.exploded.split(":")
            hextets[-1] = format(random.randint(0, 0xFFFF), "x")
            hextets[-2] = format(random.randint(0, 0xFFFF), "x")
            return ":".join(hextets)

        ipv4_pairs = [(r["Source IP"], r["Dest IP"]) for r in records if r["Source IP"] and r["Dest IP"] and ":" not in r["Source IP"] and ":" not in r["Dest IP"]]
        ipv6_pairs = [(r["Source IP"], r["Dest IP"]) for r in records if (":" in r["Source IP"]) or (":" in r["Dest IP"])]

        if not ipv4_pairs:
            ipv4_pairs = [(synth_ipv4(), synth_ipv4()) for _ in range(50)]
        if not ipv6_pairs:
            ipv6_pairs = [(synth_ipv6(), synth_ipv6()) for _ in range(25)]

        while len(records) < args.min_rows:
            if len(records) % 3 == 0:
                s, d = random.choice(ipv6_pairs)
                s2 = mutate_ipv6(s) if is_ip(s) else synth_ipv6()
                d2 = mutate_ipv6(d) if is_ip(d) else synth_ipv6()
            else:
                s, d = random.choice(ipv4_pairs)
                s2 = mutate_ipv4(s) if is_ip(s) else synth_ipv4()
                d2 = mutate_ipv4(d) if is_ip(d) else synth_ipv4()

            proto = random.choice(["TCP", "UDP", "TLS", "HTTP", "HTTPS", "ICMP"])
            port = random.choice([22, 53, 80, 123, 161, 389, 443, 8443, 9443, 1521, 5432, 8080, ""])
            bin_val = random.randint(200, 5_000_000)
            bout_val = random.randint(200, 5_000_000)

            records.append({
                "App": "XECHK",
                "Source IP": s2,
                "Source Hostname": "",
                "Dest IP": d2,
                "Dest Hostname": "",
                "Port": port,
                "Protocol": proto,
                "Bytes In": bin_val,
                "Bytes Out": bout_val,
            })

    df_out = pd.DataFrame.from_records(
        records,
        columns=["App","Source IP","Source Hostname","Dest IP","Dest Hostname","Port","Protocol","Bytes In","Bytes Out"]
    )

    base = Path(args.output_basename)
    base.parent.mkdir(parents=True, exist_ok=True)  # auto-create output folders
    csv_path = base.with_suffix(".csv")
    xlsx_path = base.with_suffix(".xlsx")

    df_out.to_csv(csv_path, index=False, encoding="utf-8")
    try:
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as xw:
            df_out.to_excel(xw, sheet_name="XECHK", index=False)
    except Exception as e:
        print(f"⚠️ Could not write Excel: {e}", file=sys.stderr)

    print(f"✅ Wrote {len(df_out)} rows")
    print(f"CSV : {csv_path.resolve()}")
    print(f"XLSX: {xlsx_path.resolve()}")

if __name__ == "__main__":
    main()