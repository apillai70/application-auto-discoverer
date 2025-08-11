#!/usr/bin/env python3
"""
Core audit system functionality without data analysis dependencies
Place this file in your project root directory (same level as main.py)
"""

import json
import asyncio
import aiofiles
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict

class CoreAuditStorage:
    """Core audit storage without pandas dependencies"""
    
    def __init__(self, base_path: str = "essentials/audit"):
        self.base_path = Path(base_path)
        self.events_dir = self.base_path / "events"
        self.reports_dir = self.base_path / "reports"
        
        # Create directories
        self.events_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    async def store_event(self, event: Dict[str, Any]) -> str:
        """Store an audit event"""
        if 'timestamp' not in event:
            event['timestamp'] = datetime.utcnow().isoformat()
        if 'event_id' not in event:
            import uuid
            event['event_id'] = str(uuid.uuid4())
        
        # Get file path
        timestamp = datetime.fromisoformat(event['timestamp'])
        year_month_dir = self.events_dir / f"{timestamp.year:04d}" / f"{timestamp.month:02d}"
        year_month_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = year_month_dir / f"events_{timestamp.strftime('%Y-%m-%d')}.jsonl"
        
        # Write event
        async with aiofiles.open(file_path, 'a') as f:
            await f.write(json.dumps(event, default=str) + '\n')
        
        return event['event_id']
    
    async def get_events(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent events"""
        events = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        while current_date <= end_date:
            year_month_dir = self.events_dir / f"{current_date.year:04d}" / f"{current_date.month:02d}"
            
            if year_month_dir.exists():
                file_path = year_month_dir / f"events_{current_date.strftime('%Y-%m-%d')}.jsonl"
                if file_path.exists():
                    async with aiofiles.open(file_path, 'r') as f:
                        async for line in f:
                            if line.strip():
                                try:
                                    events.append(json.loads(line.strip()))
                                except json.JSONDecodeError:
                                    continue
            
            current_date += timedelta(days=1)
        
        return events
    
    async def get_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get basic summary without pandas"""
        events = await self.get_events(days)
        
        summary = {
            'total_events': len(events),
            'event_types': defaultdict(int),
            'results': defaultdict(int),
            'users': defaultdict(int),
            'ips': defaultdict(int)
        }
        
        for event in events:
            summary['event_types'][event.get('event_type', 'unknown')] += 1
            summary['results'][event.get('result', 'unknown')] += 1
            summary['users'][event.get('user_id', 'unknown')] += 1
            if event.get('source_ip'):
                summary['ips'][event.get('source_ip')] += 1
        
        # Convert to regular dicts
        return {
            'total_events': summary['total_events'],
            'event_types': dict(summary['event_types']),
            'results': dict(summary['results']),
            'top_users': sorted(summary['users'].items(), key=lambda x: x[1], reverse=True)[:10],
            'top_ips': sorted(summary['ips'].items(), key=lambda x: x[1], reverse=True)[:10]
        }

async def test_core_audit():
    """Test core audit functionality"""
    print("🧪 Testing Core Audit System (No pandas)")
    print("=" * 40)
    
    storage = CoreAuditStorage()
    
    # Store test events
    test_events = [
        {
            "event_type": "authentication",
            "user_id": "test1@company.com",
            "action": "login",
            "result": "success",
            "source_ip": "192.168.1.100"
        },
        {
            "event_type": "authentication", 
            "user_id": "test2@company.com",
            "action": "login",
            "result": "failure",
            "source_ip": "203.0.113.50"
        }
    ]
    
    print("📝 Storing test events...")
    for event in test_events:
        event_id = await storage.store_event(event)
        print(f"   ✅ Stored: {event_id}")
    
    # Get summary
    print("\n📊 Generating summary...")
    summary = await storage.get_summary(days=1)
    print(f"   Total events: {summary['total_events']}")
    print(f"   Event types: {summary['event_types']}")
    print(f"   Results: {summary['results']}")
    
    print("\n✅ Core audit system working!")

if __name__ == "__main__":
    asyncio.run(test_core_audit())