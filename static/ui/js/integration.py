#!/usr/bin/env python3
"""
Integration Hub Backend
Handles connections to Splunk, DynaTrace, ExtraHop and other data sources
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp
import pandas as pd
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import requests
import hashlib
import os
from dataclasses import dataclass, asdict
import sqlite3
import threading
from queue import Queue
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

@dataclass
class IntegrationConfig:
    """Configuration for integration connections"""
    name: str
    type: str
    endpoint: str
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    enabled: bool = True
    last_sync: Optional[datetime] = None
    status: str = "disconnected"

@dataclass
class DataRecord:
    """Normalized data record"""
    id: str
    source: str
    timestamp: datetime
    source_ip: Optional[str] = None
    dest_ip: Optional[str] = None
    source_port: Optional[int] = None
    dest_port: Optional[int] = None
    protocol: Optional[str] = None
    bytes_transferred: Optional[int] = None
    action: Optional[str] = None
    raw_data: Optional[Dict] = None

class IntegrationManager:
    """Manages all integration connections and data processing"""
    
    def __init__(self):
        self.integrations: Dict[str, IntegrationConfig] = {}
        self.data_queue = Queue()
        self.processed_data: List[DataRecord] = []
        self.collection_active = False
        self.processing_stats = {
            'total_collected': 0,
            'total_processed': 0,
            'error_count': 0,
            'last_collection': None
        }
        self.setup_database()
        self.load_configurations()
        
    def setup_database(self):
        """Setup SQLite database for storing processed data"""
        self.db_path = 'integration_data.db'
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_data (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                source_ip TEXT,
                dest_ip TEXT,
                source_port INTEGER,
                dest_port INTEGER,
                protocol TEXT,
                bytes_transferred INTEGER,
                action TEXT,
                raw_data TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collection_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                source TEXT NOT NULL,
                records_collected INTEGER,
                processing_time_ms INTEGER,
                status TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Database initialized")

    def load_configurations(self):
        """Load integration configurations"""
        config_file = 'config/integrations.yaml'
        
        # Default configurations if file doesn't exist
        default_configs = {
            'extrahop': {
                'name': 'ExtraHop',
                'type': 'network_monitoring',
                'endpoint': 'https://extrahop.company.com/api/v1',
                'enabled': True
            },
            'splunk': {
                'name': 'Splunk Enterprise',
                'type': 'log_management',
                'endpoint': 'https://splunk.company.com:8089',
                'enabled': True
            },
            'dynatrace': {
                'name': 'DynaTrace',
                'type': 'apm',
                'endpoint': 'https://us1.dynatrace.com/api/v2',
                'enabled': True
            },
            'custom_api': {
                'name': 'Custom API',
                'type': 'api',
                'endpoint': 'https://api.internal.com/v1',
                'enabled': True
            },
            'database': {
                'name': 'Database',
                'type': 'database',
                'endpoint': 'postgresql://localhost:5432/network_db',
                'enabled': True
            }
        }
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    configs = yaml.safe_load(f)
            else:
                configs = default_configs
                
            for integration_id, config in configs.items():
                self.integrations[integration_id] = IntegrationConfig(**config)
                
            logger.info(f"✅ Loaded {len(self.integrations)} integration configurations")
            
        except Exception as e:
            logger.error(f"❌ Failed to load configurations: {e}")
            # Use default configs
            for integration_id, config in default_configs.items():
                self.integrations[integration_id] = IntegrationConfig(**config)

class SplunkConnector:
    """Connector for Splunk Enterprise"""
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.session = None
        
    async def connect(self) -> bool:
        """Establish connection to Splunk"""
        try:
            auth_url = f"{self.config.endpoint}/services/auth/login"
            
            async with aiohttp.ClientSession() as session:
                data = {
                    'username': self.config.username,
                    'password': self.config.password,
                    'output_mode': 'json'
                }
                
                async with session.post(auth_url, data=data, ssl=False) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.session_key = result['sessionKey']
                        self.config.status = "connected"
                        logger.info("✅ Connected to Splunk")
                        return True
                    else:
                        logger.error(f"❌ Splunk authentication failed: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Splunk connection error: {e}")
            self.config.status = "error"
            return False
    
    async def execute_query(self, query: str, **kwargs) -> List[Dict]:
        """Execute SPL query"""
        try:
            search_url = f"{self.config.endpoint}/services/search/jobs"
            
            headers = {
                'Authorization': f'Splunk {self.session_key}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'search': query,
                'output_mode': 'json',
                'count': kwargs.get('count', 1000)
            }
            
            async with aiohttp.ClientSession() as session:
                # Create search job
                async with session.post(search_url, headers=headers, data=data, ssl=False) as response:
                    if response.status == 201:
                        job_response = await response.json()
                        job_id = job_response['sid']
                        
                        # Wait for job completion
                        await self._wait_for_job(session, job_id, headers)
                        
                        # Get results
                        results_url = f"{self.config.endpoint}/services/search/jobs/{job_id}/results"
                        async with session.get(results_url, headers=headers, ssl=False) as results_response:
                            if results_response.status == 200:
                                results = await results_response.json()
                                return results.get('results', [])
                            
        except Exception as e:
            logger.error(f"❌ Splunk query error: {e}")
            return []
    
    async def _wait_for_job(self, session, job_id: str, headers: Dict, timeout: int = 30):
        """Wait for Splunk search job to complete"""
        status_url = f"{self.config.endpoint}/services/search/jobs/{job_id}"
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            async with session.get(status_url, headers=headers, ssl=False) as response:
                if response.status == 200:
                    status_data = await response.json()
                    dispatch_state = status_data['entry'][0]['content']['dispatchState']
                    
                    if dispatch_state == 'DONE':
                        return
                    elif dispatch_state == 'FAILED':
                        raise Exception("Search job failed")
                        
            await asyncio.sleep(1)
        
        raise Exception("Search job timeout")

class DynatraceConnector:
    """Connector for DynaTrace"""
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
        
    async def connect(self) -> bool:
        """Test DynaTrace connection"""
        try:
            test_url = f"{self.config.endpoint}/environment-api/v2/entities"
            headers = {
                'Authorization': f'Api-Token {self.config.api_key}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(test_url, headers=headers) as response:
                    if response.status == 200:
                        self.config.status = "connected"
                        logger.info("✅ Connected to DynaTrace")
                        return True
                    else:
                        logger.error(f"❌ DynaTrace connection failed: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ DynaTrace connection error: {e}")
            self.config.status = "error"
            return False
    
    async def query_logs(self, query: str, **kwargs) -> List[Dict]:
        """Query DynaTrace logs"""
        try:
            logs_url = f"{self.config.endpoint}/logs/search"
            headers = {
                'Authorization': f'Api-Token {self.config.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Build time range
            from_time = kwargs.get('from_time', datetime.now() - timedelta(hours=1))
            to_time = kwargs.get('to_time', datetime.now())
            
            payload = {
                'query': query,
                'from': from_time.isoformat(),
                'to': to_time.isoformat(),
                'limit': kwargs.get('limit', 1000)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(logs_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('results', [])
                    else:
                        logger.error(f"❌ DynaTrace query failed: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"❌ DynaTrace query error: {e}")
            return []

class ExtraHopConnector:
    """Connector for ExtraHop"""
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
        
    async def connect(self) -> bool:
        """Test ExtraHop connection"""
        try:
            test_url = f"{self.config.endpoint}/metrics"
            headers = {
                'Authorization': f'ExtraHop apikey={self.config.api_key}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(test_url, headers=headers, ssl=False) as response:
                    if response.status == 200:
                        self.config.status = "connected"
                        logger.info("✅ Connected to ExtraHop")
                        return True
                    else:
                        logger.error(f"❌ ExtraHop connection failed: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ ExtraHop connection error: {e}")
            self.config.status = "error"
            return False
    
    async def query_metrics(self, metric_specs: List[Dict], **kwargs) -> List[Dict]:
        """Query ExtraHop metrics"""
        try:
            metrics_url = f"{self.config.endpoint}/metrics"
            headers = {
                'Authorization': f'ExtraHop apikey={self.config.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Build time range
            from_time = kwargs.get('from_time', datetime.now() - timedelta(minutes=30))
            to_time = kwargs.get('to_time', datetime.now())
            
            payload = {
                'metric_specs': metric_specs,
                'from': int(from_time.timestamp() * 1000),
                'until': int(to_time.timestamp() * 1000),
                'object_type': kwargs.get('object_type', 'device')
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(metrics_url, headers=headers, json=payload, ssl=False) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('stats', [])
                    else:
                        logger.error(f"❌ ExtraHop query failed: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"❌ ExtraHop query error: {e}")
            return []

class DataNormalizer:
    """Normalizes data from different sources"""
    
    @staticmethod
    def normalize_splunk_record(record: Dict) -> DataRecord:
        """Normalize Splunk data"""
        return DataRecord(
            id=f"splunk_{int(time.time() * 1000)}_{hash(str(record)) % 10000}",
            source="splunk",
            timestamp=datetime.fromisoformat(record.get('_time', datetime.now().isoformat())),
            source_ip=record.get('src_ip') or record.get('clientip') or record.get('src'),
            dest_ip=record.get('dest_ip') or record.get('destip') or record.get('dest'),
            source_port=record.get('src_port') or record.get('srcport'),
            dest_port=record.get('dest_port') or record.get('destport') or record.get('port'),
            protocol=record.get('protocol') or record.get('proto'),
            bytes_transferred=record.get('bytes') or record.get('bytes_in') or record.get('bytes_out'),
            action=record.get('action') or record.get('act'),
            raw_data=record
        )
    
    @staticmethod
    def normalize_dynatrace_record(record: Dict) -> DataRecord:
        """Normalize DynaTrace data"""
        return DataRecord(
            id=f"dynatrace_{int(time.time() * 1000)}_{hash(str(record)) % 10000}",
            source="dynatrace",
            timestamp=datetime.fromisoformat(record.get('timestamp', datetime.now().isoformat())),
            source_ip=record.get('@network.client.ip') or record.get('client_ip'),
            dest_ip=record.get('@network.destination.ip') or record.get('dest_ip'),
            source_port=record.get('@network.client.port') or record.get('client_port'),
            dest_port=record.get('@network.destination.port') or record.get('dest_port'),
            protocol=record.get('@network.transport') or record.get('protocol'),
            bytes_transferred=record.get('@network.bytes_read') or record.get('bytes'),
            action=record.get('@http.status_code') or record.get('status'),
            raw_data=record
        )
    
    @staticmethod
    def normalize_extrahop_record(record: Dict) -> DataRecord:
        """Normalize ExtraHop data"""
        return DataRecord(
            id=f"extrahop_{int(time.time() * 1000)}_{hash(str(record)) % 10000}",
            source="extrahop",
            timestamp=datetime.fromtimestamp(record.get('timestamp', time.time()) / 1000),
            source_ip=record.get('src_ip') or record.get('client_ip'),
            dest_ip=record.get('dest_ip') or record.get('server_ip'),
            source_port=record.get('src_port') or record.get('client_port'),
            dest_port=record.get('dest_port') or record.get('server_port'),
            protocol=record.get('protocol') or record.get('l4_proto'),
            bytes_transferred=record.get('bytes') or record.get('req_bytes') or record.get('rsp_bytes'),
            action=record.get('packets') or record.get('req_pkts') or record.get('rsp_pkts'),
            raw_data=record
        )

# Initialize global integration manager
integration_manager = IntegrationManager()

# API Routes
@app.route('/api/integrations/status', methods=['GET'])
def get_integration_status():
    """Get status of all integrations"""
    status = {}
    for integration_id, config in integration_manager.integrations.items():
        status[integration_id] = {
            'name': config.name,
            'type': config.type,
            'status': config.status,
            'enabled': config.enabled,
            'last_sync': config.last_sync.isoformat() if config.last_sync else None
        }
    
    return jsonify({
        'integrations': status,
        'processing_stats': integration_manager.processing_stats,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/integrations/<integration_id>/connect', methods=['POST'])
def connect_integration(integration_id):
    """Connect to specific integration"""
    if integration_id not in integration_manager.integrations:
        return jsonify({'error': 'Integration not found'}), 404
    
    config = integration_manager.integrations[integration_id]
    
    # Update configuration with request data
    data = request.get_json() or {}
    if 'api_key' in data:
        config.api_key = data['api_key']
    if 'username' in data:
        config.username = data['username']
    if 'password' in data:
        config.password = data['password']
    if 'endpoint' in data:
        config.endpoint = data['endpoint']
    
    # Attempt connection
    try:
        if integration_id == 'splunk':
            connector = SplunkConnector(config)
            success = asyncio.run(connector.connect())
        elif integration_id == 'dynatrace':
            connector = DynatraceConnector(config)
            success = asyncio.run(connector.connect())
        elif integration_id == 'extrahop':
            connector = ExtraHopConnector(config)
            success = asyncio.run(connector.connect())
        else:
            success = True  # Mock connection for other types
            config.status = "connected"
        
        if success:
            config.last_sync = datetime.now()
            return jsonify({
                'message': f'Successfully connected to {config.name}',
                'status': config.status
            })
        else:
            return jsonify({'error': 'Connection failed'}), 400
            
    except Exception as e:
        logger.error(f"Connection error for {integration_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/integrations/<integration_id>/query', methods=['POST'])
def execute_query(integration_id):
    """Execute query on specific integration"""
    if integration_id not in integration_manager.integrations:
        return jsonify({'error': 'Integration not found'}), 404
    
    config = integration_manager.integrations[integration_id]
    data = request.get_json() or {}
    query = data.get('query', '')
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    try:
        start_time = time.time()
        
        if integration_id == 'splunk':
            connector = SplunkConnector(config)
            results = asyncio.run(connector.execute_query(query))
        elif integration_id == 'dynatrace':
            connector = DynatraceConnector(config)
            results = asyncio.run(connector.query_logs(query))
        elif integration_id == 'extrahop':
            connector = ExtraHopConnector(config)
            metric_specs = [{'name': 'network.bytes'}, {'name': 'network.pkts'}]
            results = asyncio.run(connector.query_metrics(metric_specs))
        else:
            # Mock results for other integrations
            results = [{'mock': 'data', 'timestamp': datetime.now().isoformat()}]
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Normalize and store results
        normalized_results = []
        for record in results:
            if integration_id == 'splunk':
                normalized = DataNormalizer.normalize_splunk_record(record)
            elif integration_id == 'dynatrace':
                normalized = DataNormalizer.normalize_dynatrace_record(record)
            elif integration_id == 'extrahop':
                normalized = DataNormalizer.normalize_extrahop_record(record)
            else:
                continue
                
            normalized_results.append(normalized)
            integration_manager.processed_data.append(normalized)
        
        # Store in database
        store_processed_data(normalized_results)
        
        # Update stats
        integration_manager.processing_stats['total_collected'] += len(results)
        integration_manager.processing_stats['total_processed'] += len(normalized_results)
        
        # Store collection stats
        store_collection_stats(integration_id, len(results), processing_time, 'success')
        
        return jsonify({
            'results_count': len(results),
            'normalized_count': len(normalized_results),
            'processing_time_ms': processing_time,
            'query': query,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Query execution error for {integration_id}: {e}")
        store_collection_stats(integration_id, 0, 0, 'error')
        integration_manager.processing_stats['error_count'] += 1
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/export', methods=['GET'])
def export_data():
    """Export processed data"""
    format_type = request.args.get('format', 'json')
    source_filter = request.args.get('source')
    
    # Filter data if source specified
    if source_filter:
        filtered_data = [d for d in integration_manager.processed_data if d.source == source_filter]
    else:
        filtered_data = integration_manager.processed_data
    
    if format_type == 'csv':
        # Convert to DataFrame and return CSV
        df = pd.DataFrame([asdict(record) for record in filtered_data])
        csv_data = df.to_csv(index=False)
        
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=integration_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
        )
    else:
        # Return JSON
        data = {
            'metadata': {
                'export_timestamp': datetime.now().isoformat(),
                'total_records': len(filtered_data),
                'sources': list(set(d.source for d in filtered_data))
            },
            'data': [asdict(record) for record in filtered_data]
        }
        
        return jsonify(data)

@app.route('/api/data/stats', methods=['GET'])
def get_data_stats():
    """Get data processing statistics"""
    conn = sqlite3.connect(integration_manager.db_path)
    cursor = conn.cursor()
    
    # Get record counts by source
    cursor.execute('''
        SELECT source, COUNT(*) as count 
        FROM processed_data 
        GROUP BY source
    ''')
    source_counts = dict(cursor.fetchall())
    
    # Get recent collection stats
    cursor.execute('''
        SELECT * FROM collection_stats 
        ORDER BY timestamp DESC 
        LIMIT 10
    ''')
    recent_collections = cursor.fetchall()
    
    conn.close()
    
    return jsonify({
        'source_counts': source_counts,
        'recent_collections': recent_collections,
        'processing_stats': integration_manager.processing_stats,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/collection/start', methods=['POST'])
def start_collection():
    """Start real-time data collection"""
    data = request.get_json() or {}
    interval = data.get('interval', 30)  # seconds
    
    if integration_manager.collection_active:
        return jsonify({'error': 'Collection already active'}), 400
    
    integration_manager.collection_active = True
    
    # Start collection thread
    collection_thread = threading.Thread(
        target=run_collection_loop,
        args=(interval,),
        daemon=True
    )
    collection_thread.start()
    
    return jsonify({
        'message': 'Real-time collection started',
        'interval': interval,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/collection/stop', methods=['POST'])
def stop_collection():
    """Stop real-time data collection"""
    integration_manager.collection_active = False
    
    return jsonify({
        'message': 'Real-time collection stopped',
        'timestamp': datetime.now().isoformat()
    })

def store_processed_data(records: List[DataRecord]):
    """Store processed data in database"""
    if not records:
        return
    
    conn = sqlite3.connect(integration_manager.db_path)
    cursor = conn.cursor()
    
    for record in records:
        cursor.execute('''
            INSERT OR REPLACE INTO processed_data 
            (id, source, timestamp, source_ip, dest_ip, source_port, dest_port, 
             protocol, bytes_transferred, action, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            record.id, record.source, record.timestamp.isoformat(),
            record.source_ip, record.dest_ip, record.source_port, record.dest_port,
            record.protocol, record.bytes_transferred, record.action,
            json.dumps(record.raw_data) if record.raw_data else None
        ))
    
    conn.commit()
    conn.close()

def store_collection_stats(source: str, records_collected: int, processing_time_ms: int, status: str):
    """Store collection statistics"""
    conn = sqlite3.connect(integration_manager.db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO collection_stats 
        (timestamp, source, records_collected, processing_time_ms, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        datetime.now().isoformat(), source, records_collected, processing_time_ms, status
    ))
    
    conn.commit()
    conn.close()

def run_collection_loop(interval: int):
    """Run continuous data collection"""
    logger.info(f"🚀 Starting collection loop with {interval}s interval")
    
    while integration_manager.collection_active:
        try:
            # Collect from all connected integrations
            for integration_id, config in integration_manager.integrations.items():
                if config.status == "connected" and config.enabled:
                    # Execute default queries for each integration
                    default_queries = {
                        'splunk': 'search index=network | head 50',
                        'dynatrace': 'source:network',
                        'extrahop': 'network.bytes'
                    }
                    
                    if integration_id in default_queries:
                        try:
                            # This would call the query endpoint internally
                            logger.info(f"Collecting from {integration_id}")
                            # Note: In a real implementation, you'd call the actual query methods here
                            
                        except Exception as e:
                            logger.error(f"Collection error for {integration_id}: {e}")
                            integration_manager.processing_stats['error_count'] += 1
            
            integration_manager.processing_stats['last_collection'] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"Collection loop error: {e}")
        
        time.sleep(interval)
    
    logger.info("⏹️ Collection loop stopped")

if __name__ == '__main__':
    print("🔌 Starting Integration Hub Backend Server...")
    print("API Endpoints:")
    print("  GET  /api/integrations/status                    - Get integration status")
    print("  POST /api/integrations/<id>/connect              - Connect to integration")
    print("  POST /api/integrations/<id>/query               - Execute query")
    print("  GET  /api/data/export                           - Export processed data")
    print("  GET  /api/data/stats                            - Get data statistics")
    print("  POST /api/collection/start                      - Start real-time collection")
    print("  POST /api/collection/stop                       - Stop real-time collection")
    print("\nServer running on http://localhost:5001")
    
    app.run(debug=True, host='0.0.0.0', port=5001)