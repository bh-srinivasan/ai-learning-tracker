"""
Simple route test for Azure deployment
"""
def create_simple_debug_route():
    """Create a simple debug route for Azure testing"""
    return '''
@app.route('/debug-test')
def debug_test():
    """Simple debug route that doesn't use database"""
    import os
    from datetime import datetime
    
    try:
        return {
            'status': 'OK',
            'timestamp': datetime.now().isoformat(),
            'environment': os.environ.get('ENV', 'unknown'),
            'admin_password_set': bool(os.environ.get('ADMIN_PASSWORD')),
            'port': os.environ.get('PORT', 'unknown'),
            'python_version': os.sys.version
        }
    except Exception as e:
        return {
            'status': 'ERROR',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
'''

if __name__ == '__main__':
    print(create_simple_debug_route())
