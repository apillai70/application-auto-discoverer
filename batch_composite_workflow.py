
#!/usr/bin/env python3
"""
Modified batch_composite_workflow.py with hash tracking to avoid reprocessing unchanged files
"""

import subprocess
import sys
import glob
import hashlib
import json
from pathlib import Path
import argparse
import time
from datetime import datetime

def find_app_code_files(data_dir="data"):
    """Find all App_Code_* CSV files in the data directory"""
    pattern = str(Path(data_dir) / "App_Code_*.csv")
    files = glob.glob(pattern)
    return sorted(files)

def extract_app_name(filename):
    """Extract application name from App_Code_XXXXX.csv"""
    stem = Path(filename).stem
    if stem.startswith("App_Code_"):
        return stem.replace("App_Code_", "").strip()
    return stem.strip()

def calculate_file_hash(file_path):
    """Calculate SHA-256 hash of a file"""
    hash_sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception as e:
        print(f"Error calculating hash for {file_path}: {e}")
        return None

def load_processed_hashes(hash_file="processed_files.json"):
    """Load previously processed file hashes"""
    try:
        if Path(hash_file).exists():
            with open(hash_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading hash file: {e}")
    return {}

def save_processed_hashes(hashes, hash_file="processed_files.json"):
    """Save processed file hashes"""
    try:
        with open(hash_file, 'w') as f:
            json.dump(hashes, f, indent=2)
    except Exception as e:
        print(f"Error saving hash file: {e}")

def should_process_file(file_path, processed_hashes):
    """Check if file needs processing based on hash comparison"""
    file_path_str = str(file_path)
    current_hash = calculate_file_hash(file_path)
    
    if current_hash is None:
        return True, "error_calculating_hash"
    
    if file_path_str not in processed_hashes:
        return True, "new"
    
    if processed_hashes[file_path_str] != current_hash:
        return True, "modified"
    
    return False, "unchanged"

def run_batch_analysis(data_dir="data", output_base="batch_analysis_results"):
    """Run composite analysis for all App_Code files with hash tracking"""
    
    # Load previously processed hashes
    processed_hashes = load_processed_hashes()
    
    # Find all App_Code files
    app_files = find_app_code_files(data_dir)
    
    if not app_files:
        print(f"No App_Code_* files found in {data_dir}")
        return False
    
    print(f"Found {len(app_files)} App_Code files to check:")
    
    # Check which files need processing
    files_to_process = []
    skipped_files = []
    
    for file_path in app_files:
        should_process, reason = should_process_file(file_path, processed_hashes)
        app_name = extract_app_name(file_path)
        
        if should_process:
            files_to_process.append((file_path, app_name, reason))
            status = "NEW" if reason == "new" else "MODIFIED" if reason == "modified" else "ERROR"
            print(f"  {len(files_to_process)}. {Path(file_path).name} -> {app_name} [{status}]")
        else:
            skipped_files.append((file_path, app_name))
            print(f"  SKIP {Path(file_path).name} -> {app_name} [UNCHANGED]")
    
    print(f"\nProcessing {len(files_to_process)} files, skipping {len(skipped_files)} unchanged files")
    
    if not files_to_process:
        print("No files need processing. All files are up to date.")
        return True
    
    print("\n" + "="*80)
    print("BATCH COMPOSITE ARCHITECTURE ANALYSIS")
    print("="*80)
    
    results_summary = []
    successful_analyses = 0
    failed_analyses = 0
    start_time = time.time()
    
    # Process only the files that need it
    for i, (file_path, app_name, reason) in enumerate(files_to_process, 1):
        filename = Path(file_path).name
        
        print(f"\n[{i}/{len(files_to_process)}] Processing: {app_name} ({reason})")
        print(f"File: {filename}")
        print("-" * 50)
        
        # Create output directory for this application
        output_dir = Path(output_base) / f"{app_name}_analysis"
        
        # Run the composite workflow for this file
        file_start_time = time.time()
        try:
            result = subprocess.run([
                sys.executable, "complete_composite_workflow.py",
                "--input", filename,
                "--output-dir", str(output_dir)
            ], capture_output=True, text=True, timeout=600, encoding='utf-8', errors='replace')
            
            file_time = time.time() - file_start_time
            
            if result.returncode == 0:
                # Update hash on successful processing
                current_hash = calculate_file_hash(file_path)
                if current_hash:
                    processed_hashes[str(file_path)] = current_hash
                    save_processed_hashes(processed_hashes)
                    print(f"SUCCESS: {app_name} analysis completed in {file_time:.1f}s ({file_time/60:.1f}min)")
                    print(f"         Hash updated to track completion")
                else:
                    print(f"SUCCESS: {app_name} analysis completed in {file_time:.1f}s ({file_time/60:.1f}min)")
                    print(f"         Warning: Could not update hash")
                
                successful_analyses += 1
                status = "SUCCESS"
                error_msg = ""
            else:
                print(f"FAILED: {app_name} analysis failed after {file_time:.1f}s")
                print(f"   Error: {result.stderr[:200]}...")
                failed_analyses += 1
                status = "FAILED"
                error_msg = result.stderr[:500]
        
        except subprocess.TimeoutExpired:
            file_time = time.time() - file_start_time
            print(f"TIMEOUT: {app_name} analysis timed out after {file_time:.1f}s")
            failed_analyses += 1
            status = "TIMEOUT"
            error_msg = "Analysis timed out after 10 minutes"
        
        except Exception as e:
            file_time = time.time() - file_start_time
            print(f"ERROR: {app_name} analysis crashed after {file_time:.1f}s: {e}")
            failed_analyses += 1
            status = "ERROR"
            error_msg = str(e)
        
        # Record results
        results_summary.append({
            'app_name': app_name,
            'filename': filename,
            'status': status,
            'processing_time_seconds': file_time,
            'processing_time_minutes': file_time/60,
            'output_dir': str(output_dir),
            'error': error_msg,
            'reason': reason
        })
        
        # Progress update with timing
        elapsed = time.time() - start_time
        avg_time_per_file = elapsed / i
        remaining_files = len(files_to_process) - i
        estimated_remaining = remaining_files * avg_time_per_file
        
        print(f"\nProgress Summary:")
        print(f"   Files completed: {i}/{len(files_to_process)} ({i/len(files_to_process)*100:.1f}%)")
        print(f"   Current file time: {file_time:.1f}s ({file_time/60:.1f}min)")
        print(f"   Average time per file: {avg_time_per_file:.1f}s ({avg_time_per_file/60:.1f}min)")
        print(f"   Total elapsed: {elapsed/60:.1f} minutes")
        print(f"   Estimated remaining: {estimated_remaining/60:.1f} minutes")
        print(f"   Success rate so far: {successful_analyses/i*100:.1f}%")
        
        if remaining_files > 0:
            next_file_path, next_app_name, next_reason = files_to_process[i]
            print(f"   Next App ID: {next_app_name} ({next_reason})")
        
        print("   " + "="*50)
    
    # Generate batch summary report (including skipped files info)
    total_time = time.time() - start_time
    generate_batch_summary(results_summary, output_base, total_time, 
                          successful_analyses, failed_analyses, 
                          len(skipped_files), len(app_files))
    
    print("\n" + "="*80)
    print("BATCH ANALYSIS COMPLETED")
    print("="*80)
    print(f"Total files found: {len(app_files)}")
    print(f"Files processed: {len(files_to_process)}")
    print(f"Files skipped (unchanged): {len(skipped_files)}")
    print(f"Successful analyses: {successful_analyses}")
    print(f"Failed analyses: {failed_analyses}")
    if len(files_to_process) > 0:
        print(f"Success rate: {successful_analyses/len(files_to_process)*100:.1f}%")
    print(f"Total processing time: {total_time/60:.1f} minutes")
    if len(files_to_process) > 0:
        print(f"Average time per processed file: {total_time/len(files_to_process):.1f} seconds")
    
    return successful_analyses > 0

def generate_batch_summary(results_summary, output_base, total_time, 
                          successful_analyses, failed_analyses, skipped_count, total_count):
    """Generate comprehensive batch analysis summary with skip information"""
    
    output_dir = Path(output_base)
    output_dir.mkdir(exist_ok=True)
    
    summary_file = output_dir / "batch_analysis_summary.md"
    
    with open(summary_file, 'w') as f:
        f.write("# Batch Composite Architecture Analysis Summary\n\n")
        f.write(f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Total Applications Found:** {total_count}\n")
        f.write(f"**Applications Processed:** {len(results_summary)}\n")
        f.write(f"**Applications Skipped (Unchanged):** {skipped_count}\n")
        f.write(f"**Successful Analyses:** {successful_analyses}\n")
        f.write(f"**Failed Analyses:** {failed_analyses}\n")
        if len(results_summary) > 0:
            f.write(f"**Success Rate:** {successful_analyses/len(results_summary)*100:.1f}%\n")
        f.write(f"**Total Processing Time:** {total_time/60:.1f} minutes\n\n")
        
        # Processing summary
        f.write("## 📊 Processing Summary\n\n")
        f.write(f"- **New files:** {len([r for r in results_summary if r.get('reason') == 'new'])}\n")
        f.write(f"- **Modified files:** {len([r for r in results_summary if r.get('reason') == 'modified'])}\n")
        f.write(f"- **Unchanged files (skipped):** {skipped_count}\n\n")
        
        # Successful analyses
        successful_apps = [r for r in results_summary if r['status'] == 'SUCCESS']
        if successful_apps:
            f.write("## Successful Analyses\n\n")
            for result in successful_apps:
                f.write(f"### {result['app_name']}\n")
                f.write(f"- **File:** {result['filename']}\n")
                f.write(f"- **Reason:** {result.get('reason', 'unknown')}\n")
                f.write(f"- **Output:** `{result['output_dir']}`\n")
                f.write(f"- **Processing Time:** {result['processing_time_minutes']:.1f} minutes\n\n")
        
        # Failed analyses
        failed_apps = [r for r in results_summary if r['status'] != 'SUCCESS']
        if failed_apps:
            f.write("## Failed Analyses\n\n")
            for result in failed_apps:
                f.write(f"### {result['app_name']}\n")
                f.write(f"- **File:** {result['filename']}\n")
                f.write(f"- **Reason:** {result.get('reason', 'unknown')}\n")
                f.write(f"- **Status:** {result['status']}\n")
                f.write(f"- **Error:** {result['error'][:200]}...\n\n")
        
        # Next steps
        f.write("## Next Steps\n\n")
        f.write("1. Review failed analyses and check input data quality\n")
        f.write("2. Examine individual application reports in their respective directories\n")
        f.write("3. Compare architectural patterns across applications\n")
        f.write("4. Identify common integration patterns and potential optimization opportunities\n")
        f.write("5. To force reprocessing of unchanged files, delete `processed_files.json`\n")
    
    print(f"\n📊 Batch summary report generated: {summary_file}")
    
    # Generate a CSV summary for easy analysis
    csv_file = output_dir / "batch_results.csv"
    with open(csv_file, 'w') as f:
        f.write("app_name,filename,status,output_dir,has_error,reason,processing_time_minutes\n")
        for result in results_summary:
            has_error = "Yes" if result['error'] else "No"
            reason = result.get('reason', 'unknown')
            processing_time = result.get('processing_time_minutes', 0)
            f.write(f"{result['app_name']},{result['filename']},{result['status']},{result['output_dir']},{has_error},{reason},{processing_time:.2f}\n")
    
    print(f"📈 Results CSV generated: {csv_file}")
    
def main():
    parser = argparse.ArgumentParser(description="Batch composite architecture analysis for multiple App_Code files")
    parser.add_argument("--data-dir", default="data", help="Directory containing App_Code files")
    parser.add_argument("--output-dir", default="batch_analysis_results", help="Base output directory")
    parser.add_argument("--preview", action="store_true", help="Preview files to be processed without running analysis")
    parser.add_argument("--filter", help="Filter files by application name pattern (e.g., 'WEB' to process only App_Code_*WEB*)")
    parser.add_argument("--limit", type=int, help="Limit number of files to process (for testing)")
    
    args = parser.parse_args()
    
    if args.preview:
        app_files = find_app_code_files(args.data_dir)
        
        if args.filter:
            app_files = [f for f in app_files if args.filter.upper() in Path(f).stem.upper()]
        
        if args.limit:
            app_files = app_files[:args.limit]
        
        print(f"Files to be processed ({len(app_files)}):")
        for i, file_path in enumerate(app_files, 1):
            app_name = extract_app_name(file_path)
            print(f"  {i:3d}. {Path(file_path).name} -> {app_name}")
        return 0
    
    # Apply filters if specified
    if args.filter or args.limit:
        app_files = find_app_code_files(args.data_dir)
        
        if args.filter:
            app_files = [f for f in app_files if args.filter.upper() in Path(f).stem.upper()]
            print(f"Filtered to {len(app_files)} files matching '{args.filter}'")
        
        if args.limit:
            app_files = app_files[:args.limit]
            print(f"Limited to first {len(app_files)} files")
        
        # Temporarily write filtered list and modify find function
        # This is a bit hacky but works for the filtering
        global _filtered_files
        _filtered_files = app_files
        
        def find_app_code_files_filtered(data_dir):
            return _filtered_files
        
        # Replace the function temporarily
        import __main__
        __main__.find_app_code_files = find_app_code_files_filtered
    
    success = run_batch_analysis(args.data_dir, args.output_dir)
    
    if success:
        print("\n🌟 Batch analysis completed with some successful results!")
        return 0
    else:
        print("\n💥 Batch analysis completed but no files were successfully processed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())