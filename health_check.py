"""
Health check and diagnostics for Azure deployment
"""
import os
import sys
import sqlite3
from datetime import datetime

def check_health():
    """Check application health and return status"""
    health_status = {
        'timestamp': datetime.utcnow().isoformat(),
        'status': 'healthy',
        'checks': {}
    }
    
    try:
        # Check Python environment
        health_status['checks']['python_version'] = {
            'status': 'ok',
            'value': sys.version
        }
        
        # Check environment variables
        health_status['checks']['environment'] = {
            'status': 'ok',
            'flask_env': os.environ.get('FLASK_ENV', 'not set'),
            'port': os.environ.get('PORT', 'not set'),
            'python_path': sys.path[0] if sys.path else 'not set'
        }
        
        # Check database connectivity
        try:
            database_path = os.environ.get('DATABASE_URL', 'sqlite:///ai_learning.db')
            if database_path.startswith('sqlite:///'):
                database_path = database_path.replace('sqlite:///', '')
            elif database_path.startswith('sqlite://'):
                database_path = database_path.replace('sqlite://', '')
            
            conn = sqlite3.connect(database_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            conn.close()
            
            health_status['checks']['database'] = {
                'status': 'ok',
                'path': database_path,
                'tables': table_count
            }
        except Exception as e:
            health_status['checks']['database'] = {
                'status': 'error',
                'error': str(e)
            }
            health_status['status'] = 'degraded'
        
        # Check imports
        try:
            import flask
            import requests
            import azure.storage.blob
            
            health_status['checks']['imports'] = {
                'status': 'ok',
                'flask_version': flask.__version__
            }
        except Exception as e:
            health_status['checks']['imports'] = {
                'status': 'error',
                'error': str(e)
            }
            health_status['status'] = 'degraded'
            
    except Exception as e:
        health_status['status'] = 'error'
        health_status['error'] = str(e)
    
    return health_status

if __name__ == '__main__':
    import json
    status = check_health()
    print(json.dumps(status, indent=2))
