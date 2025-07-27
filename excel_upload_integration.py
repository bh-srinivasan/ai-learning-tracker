#!/usr/bin/env python3
"""
Enhanced Excel Upload Route Integration
This file provides the enhanced Excel upload route that can be integrated into app.py
"""

from flask import request, jsonify
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def create_enhanced_excel_upload_route(get_current_user_func):
    """
    Creates the enhanced Excel upload route function
    Args:
        get_current_user_func: Function to get current user from the main app
    Returns:
        Route function ready to be used with @app.route decorator
    """
    
    def admin_upload_excel_courses():
        """Enhanced Excel file upload - Admin only with comprehensive feedback"""
        try:
            # Import enhanced upload functionality dynamically
            from database_environment_manager import DatabaseEnvironmentManager
            from enhanced_excel_upload import handle_excel_upload_request
            
            # Get or create database manager
            try:
                from database_integration import get_database_manager
                db_manager = get_database_manager()
            except Exception as db_init_error:
                logger.warning(f"⚠️ Database manager not available, creating new one: {db_init_error}")
                db_manager = DatabaseEnvironmentManager()
                db_manager.connect_to_database()
            
            # Use enhanced upload handler
            return handle_excel_upload_request(db_manager, get_current_user_func, request)
            
        except ImportError as import_error:
            logger.warning(f"⚠️ Enhanced upload not available, using fallback: {import_error}")
            # Fall back to original implementation
            return admin_upload_excel_courses_fallback(get_current_user_func)
        except Exception as e:
            logger.error(f"❌ Excel upload error: {e}")
            return jsonify({
                'success': False,
                'message': f'Excel upload failed: {str(e)}',
                'error_type': 'server_error',
                'timestamp': datetime.now().isoformat()
            }), 500
    
    return admin_upload_excel_courses


def admin_upload_excel_courses_fallback(get_current_user_func):
    """Fallback Excel upload implementation for when enhanced version is not available"""
    try:
        import pandas as pd
        from datetime import datetime
        
        # Authentication
        user = get_current_user_func()
        if not user or user['username'] != 'admin':
            return jsonify({
                'success': False,
                'message': 'Admin privileges required for Excel uploads.',
                'error_type': 'authentication',
                'timestamp': datetime.now().isoformat()
            }), 403
        
        # Check if file was uploaded
        if 'excel_file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No file uploaded. Please select an Excel file.',
                'error_type': 'file_validation',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        file = request.files['excel_file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No file selected. Please choose an Excel file to upload.',
                'error_type': 'file_validation',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Basic validation
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            return jsonify({
                'success': False,
                'message': 'Invalid file type. Please upload an Excel file (.xlsx or .xls).',
                'error_type': 'file_validation',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Read Excel file
        try:
            df = pd.read_excel(file)
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Failed to read Excel file: {str(e)}',
                'error_type': 'file_reading',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Validate required columns
        required_columns = ['title', 'url', 'source', 'level']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({
                'success': False,
                'message': f'Missing required columns: {", ".join(missing_columns)}. Required: {", ".join(required_columns)}',
                'error_type': 'column_validation',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Import database connection (fallback to app's existing function)
        from app import get_db_connection
        
        # Process the data using simplified logic
        conn = None
        try:
            conn = get_db_connection()
            
            stats = {
                'total_processed': len(df),
                'successful': 0,
                'skipped': 0,
                'errors': 0
            }
            
            # Get existing courses
            existing_courses = conn.execute('SELECT title, url FROM courses').fetchall()
            existing_set = set()
            for row in existing_courses:
                title = row['title'] if row['title'] else ''
                url = row['url'] if row['url'] else ''
                if title and url:
                    existing_set.add((title.lower().strip(), url.lower().strip()))
            
            # Process rows
            for index, row in df.iterrows():
                try:
                    title = str(row['title']).strip() if pd.notna(row['title']) else ''
                    url = str(row['url']).strip() if pd.notna(row['url']) else ''
                    source = str(row['source']).strip() if pd.notna(row['source']) else ''
                    level = str(row['level']).strip() if pd.notna(row['level']) else ''
                    
                    # Basic validation
                    if not all([title, url, source, level]):
                        stats['errors'] += 1
                        continue
                    
                    if level not in ['Beginner', 'Intermediate', 'Advanced']:
                        stats['errors'] += 1
                        continue
                    
                    if not url.startswith(('http://', 'https://')):
                        stats['errors'] += 1
                        continue
                    
                    # Check duplicates
                    if (title.lower(), url.lower()) in existing_set:
                        stats['skipped'] += 1
                        continue
                    
                    # Insert course
                    description = str(row.get('description', '')).strip() if pd.notna(row.get('description')) else ''
                    points = 0
                    
                    conn.execute('''
                        INSERT INTO courses 
                        (title, description, url, link, source, level, points, created_at, url_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        title, description, url, url, source, level, points,
                        datetime.now().isoformat(), 'unknown'
                    ))
                    
                    existing_set.add((title.lower(), url.lower()))
                    stats['successful'] += 1
                    
                except Exception:
                    stats['errors'] += 1
            
            conn.commit()
            
            # Return response
            if stats['successful'] > 0:
                return jsonify({
                    'success': True,
                    'message': f"Upload completed: {stats['successful']} courses added, {stats['skipped']} skipped, {stats['errors']} errors.",
                    'stats': stats,
                    'environment': 'local',
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f"No courses were uploaded. {stats['errors']} errors, {stats['skipped']} skipped.",
                    'stats': stats,
                    'environment': 'local',
                    'timestamp': datetime.now().isoformat()
                })
            
        except Exception as db_error:
            return jsonify({
                'success': False,
                'message': f'Database operation failed: {str(db_error)}',
                'error_type': 'database_error',
                'timestamp': datetime.now().isoformat()
            }), 500
        finally:
            if conn:
                conn.close()
            
    except ImportError:
        return jsonify({
            'success': False,
            'message': 'pandas library is required for Excel processing.',
            'error_type': 'missing_dependency',
            'timestamp': datetime.now().isoformat()
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Upload failed: {str(e)}',
            'error_type': 'unexpected_error',
            'timestamp': datetime.now().isoformat()
        }), 500


# Integration instructions for app.py:
"""
To integrate this enhanced Excel upload functionality into your app.py:

1. Add this import at the top of app.py (after other imports):
   from excel_upload_integration import create_enhanced_excel_upload_route

2. Replace your existing @app.route('/admin/upload_excel_courses', methods=['POST']) 
   with this:

   # Enhanced Excel Upload Route
   enhanced_upload_func = create_enhanced_excel_upload_route(get_current_user)
   app.add_url_rule('/admin/upload_excel_courses', 'admin_upload_excel_courses', 
                    enhanced_upload_func, methods=['POST'])

3. Or replace the function definition with:
   
   @app.route('/admin/upload_excel_courses', methods=['POST'])
   def admin_upload_excel_courses():
       enhanced_func = create_enhanced_excel_upload_route(get_current_user)
       return enhanced_func()

This will provide:
- Environment-aware database connection (SQLite/Azure SQL)
- Comprehensive row-by-row processing feedback
- Production-safe file handling
- Detailed error reporting
- Fallback to original implementation if enhanced version is not available
"""
