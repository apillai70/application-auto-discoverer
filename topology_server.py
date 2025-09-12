#!/usr/bin/env python3
"""
Topology Storage Server - Saves large topology data to disk
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import os
from pathlib import Path
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from your web app

# Configuration
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
TOPOLOGY_DIR = DATA_DIR / "topologies"

# Ensure directories exist
TOPOLOGY_DIR.mkdir(parents=True, exist_ok=True)

@app.route('/api/topology/save', methods=['POST'])
def save_topology():
    """Save topology data to disk"""
    try:
        data = request.json
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"topology_{timestamp}.json"
        filepath = TOPOLOGY_DIR / filename
        
        # Add metadata
        data['metadata'] = data.get('metadata', {})
        data['metadata'].update({
            'saved_at': datetime.now().isoformat(),
            'filename': filename,
            'size_bytes': len(json.dumps(data))
        })
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        # Also save a "latest" symlink/copy
        latest_path = TOPOLOGY_DIR / "topology_latest.json"
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'path': str(filepath),
            'size': os.path.getsize(filepath)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/topology/load/<filename>', methods=['GET'])
def load_topology(filename):
    """Load topology data from disk"""
    try:
        filepath = TOPOLOGY_DIR / filename
        
        if not filepath.exists():
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(filepath, mimetype='application/json')
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/topology/list', methods=['GET'])
def list_topologies():
    """List available topology files"""
    try:
        files = []
        for file in TOPOLOGY_DIR.glob('topology_*.json'):
            stat = file.stat()
            files.append({
                'filename': file.name,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            'success': True,
            'files': files
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print(f"📁 Topology storage server starting...")
    print(f"📂 Saving topologies to: {TOPOLOGY_DIR}")
    app.run(port=5001, debug=True)