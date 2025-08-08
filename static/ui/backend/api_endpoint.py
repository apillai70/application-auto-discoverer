# API Endpoints for Data Normalization Integration
# Integration Hub - Network Topology Application
# Author: Integration Hub Team
# Version: 1.0.0

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import io
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
import traceback

from data_normalization import DataNormalizer, ProcessingConfig, create_normalizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Global normalizer instance
normalizer = None
processing_results = []

def init_normalizer():
    """Initialize the global normalizer instance"""
    global normalizer
    if normalizer is None:
        config = {
            'duplicate_strategy': 'smart_upsert',
            'logging_level': 'detailed',
            'vectorization_enabled': True,
            'field_mapping_enabled': True,
            'max_file_size_mb': 100,
            'time_window_minutes': 5,
            'quality_threshold': 0.8
        }
        normalizer = create_normalizer(config)
        logger.info("DataNormalizer initialized")

@app.before_first_request
def startup():
    """Initialize normalizer on app startup"""
    init_normalizer()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'Integration Hub Data Normalization API',
        'version': '1.0.0'
    })

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current normalizer configuration"""
    if normalizer is None:
        init_normalizer()
    
    return jsonify({
        'config': {
            'duplicate_strategy': normalizer.config.duplicate_strategy,
            'logging_level': normalizer.config.logging_level,
            'vectorization_enabled': normalizer.config.vectorization_enabled,
            'field_mapping_enabled': normalizer.config.field_mapping_enabled,
            'max_file_size_mb': normalizer.config.max_file_size_mb,
            'time_window_minutes': normalizer.config.time_window_minutes,
            'quality_threshold': normalizer.config.quality_threshold
        },
        'field_mappings': normalizer.STANDARD_FIELD_MAP,
        'vector_mappings': normalizer.VECTOR_FIELD_MAPPINGS
    })

@app.route('/api/config', methods=['POST'])
def update_config():
    """Update normalizer configuration"""
    global normalizer
    
    try:
        config_data = request.json
        
        # Create new config
        new_config = ProcessingConfig(
            duplicate_strategy=config_data.get('duplicate_strategy', 'smart_upsert'),
            logging_level=config_data.get('logging_level', 'detailed'),
            vectorization_enabled=config_data.get('vectorization_enabled', True),
            field_mapping_enabled=config_data.get('field_mapping_enabled', True),
            max_file_size_mb=config_data.get('max_file_size_mb', 100),
            time_window_minutes=config_data.get('time_window_minutes', 5),
            quality_threshold=config_data.get('quality_threshold', 0.8)
        )
        
        # Reinitialize normalizer with new config
        normalizer = DataNormalizer(new_config)
        
        return jsonify({
            'status': 'success',
            'message': 'Configuration updated successfully',
            'config': {
                'duplicate_strategy': normalizer.config.duplicate_strategy,
                'logging_level': normalizer.config.logging_level,
                'vectorization_enabled': normalizer.config.vectorization_enabled,
                'field_mapping_enabled': normalizer.config.field_mapping_enabled,
                'max_file_size_mb': normalizer.config.max_file_size_mb,
                'time_window_minutes': normalizer.config.time_window_minutes,
                'quality_threshold': normalizer.config.quality_threshold
            }
        })
        
    except Exception as e:
        logger.error(f"Configuration update failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Configuration update failed: {str(e)}'
        }), 400

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload and process a single file"""
    global normalizer, processing_results
    
    if normalizer is None:
        init_normalizer()
    
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No file provided'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No file selected'
            }), 400
        
        # Read file content
        file_content = file.read()
        filename = file.filename
        
        # Validate file size
        file_size_mb = len(file_content) / (1024 * 1024)
        if file_size_mb > normalizer.config.max_file_size_mb:
            return jsonify({
                'status': 'error',
                'message': f'File size ({file_size_mb:.1f}MB) exceeds limit ({normalizer.config.max_file_size_mb}MB)'
            }), 400
        
        # Process file
        result = normalizer.process_file(file_content, filename)
        
        # Store result
        processing_results.append(result)
        
        # Convert result to JSON-serializable format
        result_dict = {
            'file_name': result.file_name,
            'original_rows': result.original_rows,
            'processed_rows': result.processed_rows,
            'quality_score': result.quality_score,
            'known_applications': result.known_applications,
            'unknown_applications': result.unknown_applications,
            'duplicate_info': result.duplicate_info,
            'field_mapping': result.field_mapping,
            'vectorization_result': result.vectorization_result,
            'processing_time': result.processing_time,
            'status': result.status,
            'errors': result.errors or []
        }
        
        logger.info(f"File processed successfully: {filename}")
        
        return jsonify({
            'status': 'success',
            'message': f'File {filename} processed successfully',
            'result': result_dict
        })
        
    except Exception as e:
        logger.error(f"File processing failed: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': f'File processing failed: {str(e)}'
        }), 500

@app.route('/api/upload/batch', methods=['POST'])
def upload_batch():
    """Upload and process multiple files"""
    global normalizer, processing_results
    
    if normalizer is None:
        init_normalizer()
    
    try:
        files = request.files.getlist('files')
        if not files:
            return jsonify({
                'status': 'error',
                'message': 'No files provided'
            }), 400
        
        batch_results = []
        
        for file in files:
            if file.filename == '':
                continue
                
            try:
                # Read file content
                file_content = file.read()
                filename = file.filename
                
                # Validate file size
                file_size_mb = len(file_content) / (1024 * 1024)
                if file_size_mb > normalizer.config.max_file_size_mb:
                    batch_results.append({
                        'file_name': filename,
                        'status': 'error',
                        'message': f'File size ({file_size_mb:.1f}MB) exceeds limit'
                    })
                    continue
                
                # Process file
                result = normalizer.process_file(file_content, filename)
                processing_results.append(result)
                
                # Convert to JSON-serializable format
                result_dict = {
                    'file_name': result.file_name,
                    'original_rows': result.original_rows,
                    'processed_rows': result.processed_rows,
                    'quality_score': result.quality_score,
                    'known_applications': result.known_applications,
                    'unknown_applications': result.unknown_applications,
                    'duplicate_info': result.duplicate_info,
                    'field_mapping': result.field_mapping,
                    'vectorization_result': result.vectorization_result,
                    'processing_time': result.processing_time,
                    'status': result.status,
                    'errors': result.errors or []
                }
                
                batch_results.append(result_dict)
                
            except Exception as e:
                logger.error(f"Failed to process file {file.filename}: {str(e)}")
                batch_results.append({
                    'file_name': file.filename,
                    'status': 'error',
                    'message': str(e)
                })
        
        successful_files = [r for r in batch_results if r.get('status') != 'error']
        failed_files = [r for r in batch_results if r.get('status') == 'error']
        
        return jsonify({
            'status': 'success',
            'message': f'Batch processing completed: {len(successful_files)} successful, {len(failed_files)} failed',
            'results': batch_results,
            'summary': {
                'total_files': len(files),
                'successful': len(successful_files),
                'failed': len(failed_files)
            }
        })
        
    except Exception as e:
        logger.error(f"Batch processing failed: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': f'Batch processing failed: {str(e)}'
        }), 500

@app.route('/api/results', methods=['GET'])
def get_results():
    """Get all processing results"""
    try:
        # Convert results to JSON-serializable format
        results_json = []
        for result in processing_results:
            result_dict = {
                'file_name': result.file_name,
                'original_rows': result.original_rows,
                'processed_rows': result.processed_rows,
                'quality_score': result.quality_score,
                'known_applications': result.known_applications,
                'unknown_applications': result.unknown_applications,
                'duplicate_info': result.duplicate_info,
                'field_mapping': result.field_mapping,
                'vectorization_result': result.vectorization_result,
                'processing_time': result.processing_time,
                'status': result.status,
                'errors': result.errors or []
            }
            results_json.append(result_dict)
        
        return jsonify({
            'status': 'success',
            'results': results_json,
            'total_count': len(results_json)
        })
        
    except Exception as e:
        logger.error(f"Failed to retrieve results: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve results: {str(e)}'
        }), 500

@app.route('/api/results/<filename>', methods=['GET'])
def get_result_by_filename(filename):
    """Get processing result for specific file"""
    try:
        for result in processing_results:
            if result.file_name == filename:
                result_dict = {
                    'file_name': result.file_name,
                    'original_rows': result.original_rows,
                    'processed_rows': result.processed_rows,
                    'quality_score': result.quality_score,
                    'known_applications': result.known_applications,
                    'unknown_applications': result.unknown_applications,
                    'duplicate_info': result.duplicate_info,
                    'field_mapping': result.field_mapping,
                    'vectorization_result': result.vectorization_result,
                    'processing_time': result.processing_time,
                    'status': result.status,
                    'errors': result.errors or []
                }
                return jsonify({
                    'status': 'success',
                    'result': result_dict
                })
        
        return jsonify({
            'status': 'error',
            'message': f'No results found for file: {filename}'
        }), 404
        
    except Exception as e:
        logger.error(f"Failed to retrieve result for {filename}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve result: {str(e)}'
        }), 500

@app.route('/api/export/normalized', methods=['GET'])
def export_normalized_data():
    """Export all normalized data"""
    global normalizer
    
    if normalizer is None:
        init_normalizer()
    
    try:
        format_type = request.args.get('format', 'json').lower()
        
        if not normalizer.global_record_store:
            return jsonify({
                'status': 'error',
                'message': 'No normalized data available for export'
            }), 404
        
        # Convert global record store to exportable format
        records = []
        for key, record_info in normalizer.global_record_store.items():
            record = record_info['data'].copy()
            if hasattr(record, 'to_dict'):
                record = record.to_dict()
            record['_global_key'] = key
            record['_first_seen'] = record_info['first_seen']
            record['_last_updated'] = record_info['last_updated']
            record['_update_count'] = record_info.get('update_count', 0)
            records.append(record)
        
        export_data = {
            'exported_at': datetime.utcnow().isoformat(),
            'total_records': len(records),
            'export_format': format_type,
            'schema_version': '1.0',
            'data': records
        }
        
        if format_type == 'json':
            # Return JSON response
            return jsonify({
                'status': 'success',
                'export_data': export_data
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Unsupported export format: {format_type}'
            }), 400
            
    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Export failed: {str(e)}'
        }), 500

@app.route('/api/export/ml/<filename>', methods=['GET'])
def export_ml_data(filename):
    """Export ML-ready data for specific file"""
    try:
        format_type = request.args.get('format', 'json').lower()
        
        # Find result for filename
        target_result = None
        for result in processing_results:
            if result.file_name == filename:
                target_result = result
                break
        
        if not target_result:
            return jsonify({
                'status': 'error',
                'message': f'No results found for file: {filename}'
            }), 404
        
        if not target_result.vectorization_result or not target_result.vectorization_result.get('ready_for_ml'):
            return jsonify({
                'status': 'error',
                'message': f'No ML-ready data available for file: {filename}'
            }), 404
        
        ml_export = {
            'exported_at': datetime.utcnow().isoformat(),
            'file_name': filename,
            'format': format_type,
            'tensor_shape': target_result.vectorization_result['tensor_shape'],
            'feature_count': target_result.vectorization_result['feature_count'],
            'feature_names': target_result.vectorization_result['feature_names'],
            'encoding_maps': target_result.vectorization_result['encoding_maps'],
            'statistics': target_result.vectorization_result['statistics'],
            'metadata': {
                'original_rows': target_result.original_rows,
                'processed_rows': target_result.processed_rows,
                'quality_score': target_result.quality_score,
                'processing_time': target_result.processing_time
            }
        }
        
        return jsonify({
            'status': 'success',
            'ml_data': ml_export
        })
        
    except Exception as e:
        logger.error(f"ML export failed for {filename}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'ML export failed: {str(e)}'
        }), 500

@app.route('/api/logs', methods=['GET'])
def get_processing_logs():
    """Get processing logs"""
    global normalizer
    
    if normalizer is None:
        init_normalizer()
    
    try:
        limit = request.args.get('limit', 100, type=int)
        level = request.args.get('level', None)
        category = request.args.get('category', None)
        
        logs = normalizer.get_processing_logs()
        
        # Filter logs
        if level:
            logs = [log for log in logs if log['level'] == level]
        if category:
            logs = [log for log in logs if log['category'] == category]
        
        # Limit results
        if limit:
            logs = logs[-limit:]
        
        return jsonify({
            'status': 'success',
            'logs': logs,
            'total_count': len(logs),
            'filters': {
                'level': level,
                'category': category,
                'limit': limit
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to retrieve logs: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve logs: {str(e)}'
        }), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get global processing statistics"""
    global normalizer, processing_results
    
    if normalizer is None:
        init_normalizer()
    
    try:
        # Get global statistics
        global_stats = normalizer.get_global_statistics()
        
        # Calculate processing statistics
        processing_stats = {
            'total_files_processed': len(processing_results),
            'successful_files': len([r for r in processing_results if r.status == 'completed']),
            'failed_files': len([r for r in processing_results if r.status == 'error']),
            'total_records_processed': sum(r.processed_rows for r in processing_results if r.status == 'completed'),
            'average_quality_score': sum(r.quality_score for r in processing_results if r.status == 'completed') / len([r for r in processing_results if r.status == 'completed']) if processing_results else 0,
            'total_processing_time': sum(r.processing_time for r in processing_results),
            'ml_ready_files': len([r for r in processing_results if r.vectorization_result and r.vectorization_result.get('ready_for_ml')])
        }
        
        # Combine statistics
        all_stats = {
            'global_statistics': global_stats,
            'processing_statistics': processing_stats,
            'duplicate_statistics': {
                'total_new_records': sum(r.duplicate_info.get('new_records', 0) for r in processing_results),
                'total_updated_records': sum(r.duplicate_info.get('updated_records', 0) for r in processing_results),
                'total_ignored_duplicates': sum(r.duplicate_info.get('ignored_duplicates', 0) for r in processing_results)
            }
        }
        
        return jsonify({
            'status': 'success',
            'statistics': all_stats
        })
        
    except Exception as e:
        logger.error(f"Failed to retrieve statistics: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve statistics: {str(e)}'
        }), 500

@app.route('/api/reset', methods=['POST'])
def reset_normalizer():
    """Reset normalizer state"""
    global normalizer, processing_results
    
    try:
        # Clear processing results
        processing_results.clear()
        
        # Reinitialize normalizer
        init_normalizer()
        
        logger.info("Normalizer state reset successfully")
        
        return jsonify({
            'status': 'success',
            'message': 'Normalizer state reset successfully'
        })
        
    except Exception as e:
        logger.error(f"Failed to reset normalizer: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to reset normalizer: {str(e)}'
        }), 500

@app.route('/api/validate', methods=['POST'])
def validate_file():
    """Validate file without processing"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No file provided'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No file selected'
            }), 400
        
        # Basic validation
        filename = file.filename
        file_content = file.read()
        file_size_mb = len(file_content) / (1024 * 1024)
        
        validation_result = {
            'filename': filename,
            'file_size_mb': round(file_size_mb, 2),
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Validate file size
        if file_size_mb > 100:  # 100MB limit
            validation_result['errors'].append(f'File size ({file_size_mb:.1f}MB) exceeds 100MB limit')
            validation_result['is_valid'] = False
        
        # Validate file type
        supported_extensions = ['.csv', '.xlsx', '.xls', '.json']
        if not any(filename.lower().endswith(ext) for ext in supported_extensions):
            validation_result['errors'].append('Unsupported file type. Supported: CSV, Excel, JSON')
            validation_result['is_valid'] = False
        
        # Try to detect fields (basic check)
        try:
            if filename.lower().endswith('.csv'):
                content_str = file_content.decode('utf-8')
                first_line = content_str.split('\n')[0]
                detected_fields = [field.strip().strip('"') for field in first_line.split(',')]
                validation_result['detected_fields'] = detected_fields
                validation_result['field_count'] = len(detected_fields)
            elif filename.lower().endswith(('.xlsx', '.xls')):
                validation_result['warnings'].append('Excel file detected - field validation will occur during processing')
            elif filename.lower().endswith('.json'):
                json_data = json.loads(file_content.decode('utf-8'))
                if isinstance(json_data, list) and len(json_data) > 0:
                    detected_fields = list(json_data[0].keys())
                    validation_result['detected_fields'] = detected_fields
                    validation_result['field_count'] = len(detected_fields)
        except Exception as e:
            validation_result['warnings'].append(f'Could not analyze file structure: {str(e)}')
        
        return jsonify({
            'status': 'success',
            'validation': validation_result
        })
        
    except Exception as e:
        logger.error(f"File validation failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'File validation failed: {str(e)}'
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500

if __name__ == '__main__':
    # Development server
    app.run(debug=True, host='0.0.0.0', port=5000)