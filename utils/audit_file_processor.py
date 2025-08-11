# utils/audit_file_processor.py - Utilities for Processing Stored Audit Files

import json
import gzip
import csv
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Generator, Optional, Tuple
from collections import defaultdict, Counter
import asyncio
import aiofiles
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass
import numpy as np

@dataclass
class AuditAnalysis:
    """Results of audit file analysis"""
    total_events: int
    date_range: Tuple[datetime, datetime]
    event_types: Dict[str, int]
    authentication_results: Dict[str, int]
    risk_levels: Dict[str, int]
    top_users: List[Tuple[str, int]]
    top_ips: List[Tuple[str, int]]
    geographic_distribution: Dict[str, int]
    hourly_distribution: Dict[int, int]
    suspicious_patterns: List[Dict[str, Any]]

class AuditFileProcessor:
    """Utility class for processing and analyzing stored audit files"""
    
    def __init__(self, base_path: str = "essentials/audit"):
        self.base_path = Path(base_path)
        self.events_dir = self.base_path / "events"
        self.reports_dir = self.base_path / "reports"
        self.temp_dir = self.base_path / "temp"
        
        # Ensure directories exist
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def read_audit_file(self, file_path: Path) -> Generator[Dict[str, Any], None, None]:
        """Read audit events from a file (supports json, jsonl, and compressed files)"""
        try:
            if file_path.suffix == '.gz':
                # Handle compressed files
                with gzip.open(file_path, 'rt') as f:
                    if '.jsonl' in file_path.name:
                        # Compressed JSONL
                        for line in f:
                            line = line.strip()
                            if line:
                                try:
                                    yield json.loads(line)
                                except json.JSONDecodeError:
                                    continue
                    else:
                        # Compressed JSON
                        content = f.read()
                        if content.strip():
                            events = json.loads(content)
                            if isinstance(events, list):
                                for event in events:
                                    yield event
                            else:
                                yield events
            
            elif file_path.suffix == '.jsonl':
                # JSONL format
                with open(file_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                yield json.loads(line)
                            except json.JSONDecodeError:
                                continue
            
            elif file_path.suffix == '.json':
                # Regular JSON
                with open(file_path, 'r') as f:
                    content = f.read()
                    if content.strip():
                        events = json.loads(content)
                        if isinstance(events, list):
                            for event in events:
                                yield event
                        else:
                            yield events
                            
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
    
    def get_files_in_date_range(self, start_date: datetime, end_date: datetime) -> List[Path]:
        """Get all audit files within a date range"""
        files = []
        
        current_date = start_date.replace(day=1)  # Start from beginning of month
        
        while current_date <= end_date:
            year_month_dir = self.events_dir / f"{current_date.year:04d}" / f"{current_date.month:02d}"
            
            if year_month_dir.exists():
                # Find all files in this month
                for file_path in year_month_dir.iterdir():
                    if file_path.is_file() and (file_path.suffix in ['.json', '.jsonl'] or file_path.name.endswith('.gz')):
                        # Check if file date is in range
                        file_date = self._extract_date_from_filename(file_path.name)
                        if file_date and start_date.date() <= file_date.date() <= end_date.date():
                            files.append(file_path)
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return sorted(files)
    
    def _extract_date_from_filename(self, filename: str) -> Optional[datetime]:
        """Extract date from audit filename"""
        try:
            # Handle various filename formats
            # events_2024-01-15.jsonl, events_2024-01-15_14.jsonl, etc.
            for fmt in ['%Y-%m-%d_%H', '%Y-%m-%d']:
                try:
                    date_part = filename.replace('events_', '').split('.')[0].replace('_week', '')
                    return datetime.strptime(date_part, fmt)
                except ValueError:
                    continue
            return None
        except:
            return None
    
    def analyze_files(self, start_date: datetime, end_date: datetime) -> AuditAnalysis:
        """Analyze audit files in a date range and return comprehensive analysis"""
        files = self.get_files_in_date_range(start_date, end_date)
        
        # Initialize counters
        total_events = 0
        event_types = defaultdict(int)
        auth_results = defaultdict(int)
        risk_levels = defaultdict(int)
        user_counts = defaultdict(int)
        ip_counts = defaultdict(int)
        geo_counts = defaultdict(int)
        hourly_counts = defaultdict(int)
        
        # Track suspicious patterns
        failed_attempts = defaultdict(list)
        ip_user_combinations = defaultdict(set)
        
        earliest_date = None
        latest_date = None
        
        print(f"📊 Analyzing {len(files)} audit files...")
        
        for file_path in files:
            print(f"   Processing: {file_path.name}")
            
            for event in self.read_audit_file(file_path):
                total_events += 1
                
                # Extract event details
                event_type = event.get('event_type', 'unknown')
                result = event.get('result', 'unknown')
                user_id = event.get('user_id', 'unknown')
                source_ip = event.get('source_ip')
                timestamp_str = event.get('timestamp')
                
                # Update counters
                event_types[event_type] += 1
                auth_results[result] += 1
                user_counts[user_id] += 1
                
                if source_ip:
                    ip_counts[source_ip] += 1
                    ip_user_combinations[source_ip].add(user_id)
                
                # Risk level analysis
                risk_assessment = event.get('risk_assessment', {})
                if risk_assessment and 'risk_level' in risk_assessment:
                    risk_levels[risk_assessment['risk_level']] += 1
                
                # Geographic analysis
                geo_info = event.get('geographic_info', {})
                if geo_info and geo_info.get('country'):
                    geo_counts[geo_info['country']] += 1
                
                # Time analysis
                if timestamp_str:
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        hourly_counts[timestamp.hour] += 1
                        
                        if earliest_date is None or timestamp < earliest_date:
                            earliest_date = timestamp
                        if latest_date is None or timestamp > latest_date:
                            latest_date = timestamp
                            
                    except:
                        pass
                
                # Track failed authentication attempts for pattern analysis
                if event_type == 'authentication' and result == 'failure':
                    failed_attempts[user_id].append({
                        'timestamp': timestamp_str,
                        'source_ip': source_ip,
                        'reason': event.get('auth_details', {}).get('failure_reason', 'Unknown')
                    })
        
        # Detect suspicious patterns
        suspicious_patterns = self._detect_suspicious_patterns(failed_attempts, ip_user_combinations, ip_counts)
        
        # Get top users and IPs
        top_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        top_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return AuditAnalysis(
            total_events=total_events,
            date_range=(earliest_date or start_date, latest_date or end_date),
            event_types=dict(event_types),
            authentication_results=dict(auth_results),
            risk_levels=dict(risk_levels),
            top_users=top_users,
            top_ips=top_ips,
            geographic_distribution=dict(geo_counts),
            hourly_distribution=dict(hourly_counts),
            suspicious_patterns=suspicious_patterns
        )
    
    def _detect_suspicious_patterns(self, failed_attempts: Dict, ip_user_combinations: Dict, ip_counts: Dict) -> List[Dict[str, Any]]:
        """Detect suspicious patterns in the audit data"""
        patterns = []
        
        # Pattern 1: Users with excessive failed attempts
        for user_id, attempts in failed_attempts.items():
            if len(attempts) > 10:
                patterns.append({
                    'type': 'excessive_failed_attempts',
                    'severity': 'high',
                    'description': f'User {user_id} has {len(attempts)} failed login attempts',
                    'details': {
                        'user_id': user_id,
                        'attempt_count': len(attempts),
                        'unique_ips': len(set(a.get('source_ip') for a in attempts if a.get('source_ip')))
                    }
                })
        
        # Pattern 2: IPs targeting multiple users
        for ip, users in ip_user_combinations.items():
            if len(users) > 5:
                patterns.append({
                    'type': 'ip_targeting_multiple_users',
                    'severity': 'medium',
                    'description': f'IP {ip} attempted to access {len(users)} different user accounts',
                    'details': {
                        'source_ip': ip,
                        'user_count': len(users),
                        'total_attempts': ip_counts[ip]
                    }
                })
        
        # Pattern 3: High-volume IPs
        for ip, count in ip_counts.items():
            if count > 50:
                patterns.append({
                    'type': 'high_volume_ip',
                    'severity': 'medium',
                    'description': f'IP {ip} generated {count} audit events',
                    'details': {
                        'source_ip': ip,
                        'event_count': count,
                        'unique_users': len(ip_user_combinations.get(ip, set()))
                    }
                })
        
        return patterns
    
    def create_summary_report(self, analysis: AuditAnalysis, output_file: str = None) -> str:
        """Create a comprehensive summary report"""
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"audit_summary_{timestamp}.txt"
        
        output_path = self.reports_dir / output_file
        
        with open(output_path, 'w') as f:
            f.write("AUDIT ANALYSIS SUMMARY REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Analysis Period: {analysis.date_range[0]} to {analysis.date_range[1]}\n")
            f.write(f"Total Events Analyzed: {analysis.total_events:,}\n\n")
            
            f.write("EVENT TYPE BREAKDOWN:\n")
            for event_type, count in sorted(analysis.event_types.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / analysis.total_events) * 100
                f.write(f"  {event_type}: {count:,} ({percentage:.1f}%)\n")
            f.write("\n")
            
            f.write("AUTHENTICATION RESULTS:\n")
            for result, count in sorted(analysis.authentication_results.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / analysis.total_events) * 100
                f.write(f"  {result}: {count:,} ({percentage:.1f}%)\n")
            f.write("\n")
            
            f.write("RISK LEVEL DISTRIBUTION:\n")
            for risk_level, count in sorted(analysis.risk_levels.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / analysis.total_events) * 100
                f.write(f"  {risk_level}: {count:,} ({percentage:.1f}%)\n")
            f.write("\n")
            
            f.write("TOP 10 USERS BY EVENT COUNT:\n")
            for user, count in analysis.top_users:
                f.write(f"  {user}: {count:,} events\n")
            f.write("\n")
            
            f.write("TOP 10 SOURCE IPs:\n")
            for ip, count in analysis.top_ips:
                f.write(f"  {ip}: {count:,} events\n")
            f.write("\n")
            
            f.write("GEOGRAPHIC DISTRIBUTION:\n")
            for country, count in sorted(analysis.geographic_distribution.items(), key=lambda x: x[1], reverse=True)[:10]:
                f.write(f"  {country}: {count:,} events\n")
            f.write("\n")
            
            f.write("SUSPICIOUS PATTERNS DETECTED:\n")
            if analysis.suspicious_patterns:
                for pattern in analysis.suspicious_patterns:
                    f.write(f"  [{pattern['severity'].upper()}] {pattern['type']}: {pattern['description']}\n")
            else:
                f.write("  No suspicious patterns detected.\n")
            f.write("\n")
            
            f.write(f"Report generated on: {datetime.now()}\n")
        
        print(f"📄 Summary report created: {output_path}")
        return str(output_path)
    
    def create_visualizations(self, analysis: AuditAnalysis, output_dir: str = None) -> List[str]:
        """Create visualization charts from analysis data"""
        if output_dir is None:
            output_dir = self.reports_dir / "charts"
        
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        created_files = []
        plt.style.use('seaborn-v0_8')
        
        # 1. Event Types Pie Chart
        if analysis.event_types:
            plt.figure(figsize=(10, 8))
            plt.pie(analysis.event_types.values(), labels=analysis.event_types.keys(), autopct='%1.1f%%')
            plt.title('Distribution of Event Types')
            chart_path = output_dir / 'event_types_pie.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            created_files.append(str(chart_path))
        
        # 2. Authentication Results Bar Chart
        if analysis.authentication_results:
            plt.figure(figsize=(12, 6))
            results = list(analysis.authentication_results.keys())
            counts = list(analysis.authentication_results.values())
            bars = plt.bar(results, counts)
            plt.title('Authentication Results')
            plt.ylabel('Count')
            plt.xticks(rotation=45)
            
            # Color code bars
            colors = {'success': 'green', 'failure': 'red', 'mfa_required': 'orange', 'blocked': 'darkred'}
            for bar, result in zip(bars, results):
                bar.set_color(colors.get(result, 'blue'))
            
            chart_path = output_dir / 'auth_results_bar.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            created_files.append(str(chart_path))
        
        # 3. Hourly Activity Heatmap
        if analysis.hourly_distribution:
            plt.figure(figsize=(15, 6))
            hours = list(range(24))
            counts = [analysis.hourly_distribution.get(hour, 0) for hour in hours]
            
            plt.bar(hours, counts, color='skyblue')
            plt.title('Activity Distribution by Hour of Day')
            plt.xlabel('Hour')
            plt.ylabel('Event Count')
            plt.xticks(hours)
            plt.grid(axis='y', alpha=0.3)
            
            chart_path = output_dir / 'hourly_activity.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            created_files.append(str(chart_path))
        
        # 4. Risk Level Distribution
        if analysis.risk_levels:
            plt.figure(figsize=(10, 6))
            risk_levels = list(analysis.risk_levels.keys())
            counts = list(analysis.risk_levels.values())
            
            # Color code by risk level
            colors = {'low': 'green', 'medium': 'yellow', 'high': 'orange', 'critical': 'red'}
            bar_colors = [colors.get(level, 'blue') for level in risk_levels]
            
            plt.bar(risk_levels, counts, color=bar_colors)
            plt.title('Risk Level Distribution')
            plt.ylabel('Count')
            
            chart_path = output_dir / 'risk_levels.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            created_files.append(str(chart_path))
        
        # 5. Top IPs Chart
        if analysis.top_ips:
            plt.figure(figsize=(12, 8))
            top_10_ips = analysis.top_ips[:10]
            ips = [ip for ip, count in top_10_ips]
            counts = [count for ip, count in top_10_ips]
            
            plt.barh(ips, counts)
            plt.title('Top 10 Source IP Addresses')
            plt.xlabel('Event Count')
            plt.gca().invert_yaxis()
            
            chart_path = output_dir / 'top_ips.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            created_files.append(str(chart_path))
        
        print(f"📊 Created {len(created_files)} visualization charts in {output_dir}")
        return created_files
    
    def export_to_csv(self, start_date: datetime, end_date: datetime, output_file: str = None) -> str:
        """Export audit events to CSV format"""
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"audit_export_{timestamp}.csv"
        
        output_path = self.reports_dir / output_file
        files = self.get_files_in_date_range(start_date, end_date)
        
        with open(output_path, 'w', newline='') as csvfile:
            fieldnames = [
                'event_id', 'timestamp', 'event_type', 'user_id', 'action', 'result',
                'source_ip', 'user_agent', 'application', 'risk_level', 'risk_score',
                'country', 'device_type', 'auth_method', 'failure_reason'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for file_path in files:
                for event in self.read_audit_file(file_path):
                    # Flatten event data for CSV
                    row = {
                        'event_id': event.get('event_id'),
                        'timestamp': event.get('timestamp'),
                        'event_type': event.get('event_type'),
                        'user_id': event.get('user_id'),
                        'action': event.get('action'),
                        'result': event.get('result'),
                        'source_ip': event.get('source_ip'),
                        'user_agent': event.get('user_agent'),
                        'application': event.get('application'),
                        'risk_level': event.get('risk_assessment', {}).get('risk_level'),
                        'risk_score': event.get('risk_assessment', {}).get('risk_score'),
                        'country': event.get('geographic_info', {}).get('country'),
                        'device_type': event.get('device_info', {}).get('device_type'),
                        'auth_method': event.get('auth_details', {}).get('auth_method'),
                        'failure_reason': event.get('auth_details', {}).get('failure_reason')
                    }
                    writer.writerow(row)
        
        print(f"📄 CSV export created: {output_path}")
        return str(output_path)
    
    def create_pandas_dataframe(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Load audit events into a pandas DataFrame for advanced analysis"""
        files = self.get_files_in_date_range(start_date, end_date)
        events = []
        
        for file_path in files:
            for event in self.read_audit_file(file_path):
                # Flatten nested structures
                flat_event = {
                    'event_id': event.get('event_id'),
                    'timestamp': event.get('timestamp'),
                    'event_type': event.get('event_type'),
                    'user_id': event.get('user_id'),
                    'action': event.get('action'),
                    'result': event.get('result'),
                    'severity': event.get('severity'),
                    'source_ip': event.get('source_ip'),
                    'user_agent': event.get('user_agent'),
                    'application': event.get('application'),
                    'description': event.get('description')
                }
                
                # Add risk assessment data
                risk_assessment = event.get('risk_assessment', {})
                flat_event.update({
                    'risk_level': risk_assessment.get('risk_level'),
                    'risk_score': risk_assessment.get('risk_score'),
                    'geographic_risk': risk_assessment.get('geographic_risk'),
                    'temporal_risk': risk_assessment.get('temporal_risk'),
                    'device_risk': risk_assessment.get('device_risk'),
                    'behavioral_risk': risk_assessment.get('behavioral_risk')
                })
                
                # Add geographic data
                geo_info = event.get('geographic_info', {})
                flat_event.update({
                    'country': geo_info.get('country'),
                    'region': geo_info.get('region'),
                    'city': geo_info.get('city')
                })
                
                # Add device data
                device_info = event.get('device_info', {})
                flat_event.update({
                    'device_type': device_info.get('device_type'),
                    'os': device_info.get('os'),
                    'browser': device_info.get('browser'),
                    'is_trusted': device_info.get('is_trusted')
                })
                
                # Add auth details
                auth_details = event.get('auth_details', {})
                flat_event.update({
                    'auth_method': auth_details.get('auth_method'),
                    'mfa_method': auth_details.get('mfa_method'),
                    'identity_provider': auth_details.get('identity_provider'),
                    'failure_reason': auth_details.get('failure_reason'),
                    'error_code': auth_details.get('error_code')
                })
                
                events.append(flat_event)
        
        df = pd.DataFrame(events)
        
        # Convert timestamp to datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.day_name()
            df['date'] = df['timestamp'].dt.date
        
        print(f"📊 Created DataFrame with {len(df)} events and {len(df.columns)} columns")
        return df
    
    def advanced_analysis(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Perform advanced statistical analysis on audit data"""
        df = self.create_pandas_dataframe(start_date, end_date)
        
        if df.empty:
            return {"error": "No data found for the specified date range"}
        
        analysis = {
            "dataset_info": {
                "total_events": len(df),
                "date_range": f"{start_date.date()} to {end_date.date()}",
                "unique_users": df['user_id'].nunique() if 'user_id' in df.columns else 0,
                "unique_ips": df['source_ip'].nunique() if 'source_ip' in df.columns else 0
            }
        }
        
        # Authentication analysis
        if 'result' in df.columns:
            auth_analysis = df[df['event_type'] == 'authentication']['result'].value_counts()
            analysis["authentication_analysis"] = {
                "total_auth_events": len(df[df['event_type'] == 'authentication']),
                "success_rate": (auth_analysis.get('success', 0) / len(df[df['event_type'] == 'authentication'])) * 100,
                "failure_rate": (auth_analysis.get('failure', 0) / len(df[df['event_type'] == 'authentication'])) * 100,
                "results_breakdown": auth_analysis.to_dict()
            }
        
        # Risk analysis
        if 'risk_score' in df.columns:
            risk_scores = df['risk_score'].dropna()
            analysis["risk_analysis"] = {
                "average_risk_score": risk_scores.mean(),
                "median_risk_score": risk_scores.median(),
                "high_risk_events": len(df[df['risk_score'] > 70]),
                "risk_score_distribution": {
                    "min": risk_scores.min(),
                    "max": risk_scores.max(),
                    "std": risk_scores.std()
                }
            }
        
        # Temporal patterns
        if 'hour' in df.columns:
            hourly_pattern = df['hour'].value_counts().sort_index()
            analysis["temporal_patterns"] = {
                "peak_hour": hourly_pattern.idxmax(),
                "peak_hour_events": hourly_pattern.max(),
                "quiet_hour": hourly_pattern.idxmin(),
                "hourly_distribution": hourly_pattern.to_dict()
            }
        
        # Geographic analysis
        if 'country' in df.columns:
            geo_analysis = df['country'].value_counts()
            analysis["geographic_analysis"] = {
                "unique_countries": df['country'].nunique(),
                "top_countries": geo_analysis.head(10).to_dict(),
                "single_access_countries": len(geo_analysis[geo_analysis == 1])
            }
        
        # User behavior analysis
        if 'user_id' in df.columns:
            user_activity = df['user_id'].value_counts()
            analysis["user_behavior"] = {
                "most_active_user": user_activity.index[0] if len(user_activity) > 0 else None,
                "most_active_user_events": user_activity.iloc[0] if len(user_activity) > 0 else 0,
                "average_events_per_user": user_activity.mean(),
                "users_with_single_event": len(user_activity[user_activity == 1])
            }
        
        return analysis

# =================== COMMAND LINE INTERFACE ===================

class AuditCLI:
    """Command line interface for audit file processing"""
    
    def __init__(self):
        self.processor = AuditFileProcessor()
    
    def run_analysis(self, days: int = 7):
        """Run comprehensive analysis for the last N days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        print(f"🔍 Running audit analysis for last {days} days...")
        print(f"📅 Date range: {start_date.date()} to {end_date.date()}")
        
        # Basic analysis
        analysis = self.processor.analyze_files(start_date, end_date)
        
        # Create reports
        summary_file = self.processor.create_summary_report(analysis)
        
        # Create visualizations
        chart_files = self.processor.create_visualizations(analysis)
        
        # Export CSV
        csv_file = self.processor.export_to_csv(start_date, end_date)
        
        # Advanced analysis
        advanced = self.processor.advanced_analysis(start_date, end_date)
        
        print("\n📊 ANALYSIS COMPLETE!")
        print(f"📄 Summary report: {summary_file}")
        print(f"📊 Charts created: {len(chart_files)} files")
        print(f"📄 CSV export: {csv_file}")
        print(f"\n🔍 Key findings:")
        print(f"   Total events: {analysis.total_events:,}")
        print(f"   Suspicious patterns: {len(analysis.suspicious_patterns)}")
        if 'authentication_analysis' in advanced:
            print(f"   Auth success rate: {advanced['authentication_analysis']['success_rate']:.1f}%")
        if 'risk_analysis' in advanced:
            print(f"   Average risk score: {advanced['risk_analysis']['average_risk_score']:.1f}")
        
        return {
            "analysis": analysis,
            "advanced": advanced,
            "reports": {
                "summary": summary_file,
                "charts": chart_files,
                "csv": csv_file
            }
        }

# =================== USAGE EXAMPLES ===================

def example_usage():
    """Example of how to use the audit file processor"""
    processor = AuditFileProcessor()
    
    # Analyze last 7 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    print("📊 Basic Analysis Example:")
    analysis = processor.analyze_files(start_date, end_date)
    print(f"   Total events: {analysis.total_events}")
    print(f"   Event types: {list(analysis.event_types.keys())}")
    print(f"   Suspicious patterns: {len(analysis.suspicious_patterns)}")
    
    # Create reports
    print("\n📄 Creating Reports:")
    summary_file = processor.create_summary_report(analysis)
    chart_files = processor.create_visualizations(analysis)
    csv_file = processor.export_to_csv(start_date, end_date)
    
    # Advanced analysis with pandas
    print("\n🔬 Advanced Analysis:")
    df = processor.create_pandas_dataframe(start_date, end_date)
    print(f"   DataFrame shape: {df.shape}")
    
    advanced = processor.advanced_analysis(start_date, end_date)
    print(f"   Analysis results: {list(advanced.keys())}")
    
    return {
        "basic_analysis": analysis,
        "dataframe": df,
        "advanced_analysis": advanced,
        "reports": [summary_file, csv_file] + chart_files
    }

if __name__ == "__main__":
    # Command line interface
    import sys
    
    if len(sys.argv) > 1:
        days = int(sys.argv[1])
    else:
        days = 7
    
    cli = AuditCLI()
    results = cli.run_analysis(days)
    
    print(f"\n✅ Analysis complete! Check the essentials/audit/reports/ directory for outputs.")