#!/usr/bin/env python3
"""
Minimal Azure debug script to test database connectivity and environment
"""

import sqlite3
import os
import traceback
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/debug/database')
def debug_database():
    """Test database connectivity and schema"""
    try:
        # Get database path
        db_path = os.path.join(os.path.dirname(__file__), 'ai_learning.db')
        
        result = {
            'database_exists': os.path.exists(db_path),
            'database_path': db_path,
            'working_directory': os.getcwd(),
            'file_listing': os.listdir('.') if os.path.exists('.') else 'Cannot list files'
        }
        
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            
            # Check tables
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            result['tables'] = tables
            
            # Check each table structure
            table_info = {}
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table});")
                columns = [dict(row) for row in cursor.fetchall()]
                table_info[table] = columns
                
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                table_info[table + '_count'] = count
                
            result['table_info'] = table_info
            
            # Test specific queries that might be failing
            try:
                cursor.execute("SELECT COUNT(*) FROM users;")
                result['users_count'] = cursor.fetchone()[0]
            except Exception as e:
                result['users_error'] = str(e)
                
            try:
                cursor.execute("SELECT COUNT(*) FROM courses;")
                result['courses_count'] = cursor.fetchone()[0]
            except Exception as e:
                result['courses_error'] = str(e)
                
            try:
                cursor.execute("SELECT COUNT(*) FROM learning_entries;")
                result['learning_entries_count'] = cursor.fetchone()[0]
            except Exception as e:
                result['learning_entries_error'] = str(e)
            
            conn.close()
        else:
            result['error'] = 'Database file not found'
            
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/debug/environment')
def debug_environment():
    """Check environment variables and Python setup"""
    try:
        result = {
            'python_version': os.sys.version,
            'environment_variables': dict(os.environ),
            'working_directory': os.getcwd(),
            'file_permissions': {},
            'flask_version': None
        }
        
        # Check Flask version
        try:
            import flask
            result['flask_version'] = flask.__version__
        except:
            result['flask_version'] = 'Not available'
            
        # Check file permissions
        files_to_check = ['ai_learning.db', 'app.py', 'requirements.txt']
        for file in files_to_check:
            if os.path.exists(file):
                stat = os.stat(file)
                result['file_permissions'][file] = {
                    'exists': True,
                    'size': stat.st_size,
                    'readable': os.access(file, os.R_OK),
                    'writable': os.access(file, os.W_OK)
                }
            else:
                result['file_permissions'][file] = {'exists': False}
                
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/debug/admin-simulation')
def debug_admin_simulation():
    """Simulate the admin dashboard logic to find the error"""
    try:
        # Get database path
        db_path = os.path.join(os.path.dirname(__file__), 'ai_learning.db')
        
        if not os.path.exists(db_path):
            return jsonify({'error': 'Database not found'}), 500
            
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        result = {}
        
        # Try each query separately
        try:
            cursor.execute("SELECT COUNT(*) FROM users;")
            result['total_users'] = cursor.fetchone()[0]
        except Exception as e:
            result['users_error'] = str(e)
            
        try:
            cursor.execute("SELECT COUNT(*) FROM courses;")
            result['total_courses'] = cursor.fetchone()[0]
        except Exception as e:
            result['courses_error'] = str(e)
            
        try:
            cursor.execute("SELECT COUNT(*) FROM learning_entries;")
            result['total_learning_entries'] = cursor.fetchone()[0]
        except Exception as e:
            result['learning_entries_error'] = str(e)
            
        try:
            cursor.execute("""
                SELECT u.username, COUNT(le.id) as entry_count 
                FROM users u 
                LEFT JOIN learning_entries le ON u.id = le.user_id 
                GROUP BY u.id, u.username 
                ORDER BY entry_count DESC 
                LIMIT 5
            """)
            result['recent_users'] = [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            result['recent_users_error'] = str(e)
            
        try:
            cursor.execute("""
                SELECT title, COUNT(le.id) as usage_count 
                FROM courses c 
                LEFT JOIN learning_entries le ON c.id = le.course_id 
                GROUP BY c.id, c.title 
                ORDER BY usage_count DESC 
                LIMIT 5
            """)
            result['popular_courses'] = [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            result['popular_courses_error'] = str(e)
            
        conn.close()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
