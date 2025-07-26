"""
Enhanced Excel upload handler with user-friendly error descriptions
"""
from flask import jsonify, request
import pandas as pd
from datetime import datetime
import os
import tempfile
from werkzeug.utils import secure_filename
from error_descriptions import generate_user_friendly_error_description

def handle_excel_upload_with_descriptions(get_db_connection_func, get_current_user_func):
    """
    Enhanced Excel upload handler that includes user-friendly error descriptions
    """
    try:
        print(f"📋 Enhanced upload request received from: {request.remote_addr}")
        user = get_current_user_func()
        print(f"📋 Current user: {user}")
        
        if not user or user['username'] != 'admin':
            print(f"❌ Access denied for user: {user}")
            error_desc = "Admin privileges are required to upload course files."
            return jsonify({
                'success': False, 
                'error': 'Admin privileges required.', 
                'error_description': error_desc
            }), 403
            
    except Exception as auth_error:
        print(f"❌ Authentication error: {auth_error}")
        error_desc = generate_user_friendly_error_description(None, 'server_error', 'Authentication failed')
        return jsonify({
            'success': False, 
            'error': f'Authentication error: {str(auth_error)}', 
            'error_description': error_desc
        }), 500

    try:
        # Check if file was uploaded
        if 'excel_file' not in request.files:
            error_desc = generate_user_friendly_error_description(None, 'no_file', None)
            return jsonify({
                'success': False, 
                'error': 'No file uploaded.', 
                'error_description': error_desc
            }), 400
        
        file = request.files['excel_file']
        if file.filename == '':
            error_desc = generate_user_friendly_error_description(None, 'empty_file', None)
            return jsonify({
                'success': False, 
                'error': 'No file selected.', 
                'error_description': error_desc
            }), 400
        
        # Validate file type
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            error_desc = generate_user_friendly_error_description(None, 'invalid_format', None)
            return jsonify({
                'success': False, 
                'error': 'Please upload an Excel file (.xlsx or .xls).', 
                'error_description': error_desc
            }), 400
        
        # Save file temporarily
        temp_filename = secure_filename(file.filename)
        temp_path = os.path.join(tempfile.gettempdir(), temp_filename)
        file.save(temp_path)
        
        # Read Excel file
        try:
            df = pd.read_excel(temp_path)
            print(f"Excel file read successfully: {len(df)} rows, columns: {list(df.columns)}")
        except Exception as e:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            error_desc = generate_user_friendly_error_description(None, 'read_error', None)
            return jsonify({
                'success': False, 
                'error': f'Failed to read Excel file: {str(e)}', 
                'error_description': error_desc
            }), 400
        
        # Validate required columns
        required_columns = ['title', 'url', 'source', 'level']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            error_desc = generate_user_friendly_error_description(None, 'missing_columns', ", ".join(missing_columns))
            return jsonify({
                'success': False, 
                'error': f'Missing required columns: {", ".join(missing_columns)}. Required: {", ".join(required_columns)}', 
                'error_description': error_desc
            }), 400
        
        # Process the data
        conn = None
        try:
            conn = get_db_connection_func()
            print("Database connection established")
            
            stats = {
                'total_processed': 0,
                'added': 0,
                'skipped': 0,
                'errors': 0,
                'error_details': []
            }
            
            # Get existing courses to check for duplicates
            existing_courses = conn.execute('SELECT title, url FROM courses').fetchall()
            existing_set = set()
            for row in existing_courses:
                title = row['title'] if row['title'] else ''
                url = row['url'] if row['url'] else ''
                if title and url:
                    existing_set.add((title.lower().strip(), url.lower().strip()))
            print(f"Found {len(existing_set)} existing courses for duplicate check")
            
            for index, row in df.iterrows():
                stats['total_processed'] += 1
                
                try:
                    # Extract and validate data
                    title = str(row['title']).strip() if pd.notna(row['title']) else ''
                    url = str(row['url']).strip() if pd.notna(row['url']) else ''
                    source = str(row['source']).strip() if pd.notna(row['source']) else ''
                    level = str(row['level']).strip() if pd.notna(row['level']) else ''
                    
                    # Validate required fields
                    if not all([title, url, source, level]):
                        stats['errors'] += 1
                        continue
                    
                    # Validate level
                    if level not in ['Beginner', 'Intermediate', 'Advanced']:
                        stats['errors'] += 1
                        continue
                    
                    # Validate URL format
                    if not url.startswith(('http://', 'https://')):
                        stats['errors'] += 1
                        continue
                    
                    # Check for duplicates
                    if (title.lower(), url.lower()) in existing_set:
                        stats['skipped'] += 1
                        continue
                    
                    # Extract optional fields
                    description = str(row.get('description', '')).strip() if pd.notna(row.get('description')) else ''
                    category = str(row.get('category', '')).strip() if pd.notna(row.get('category')) else None
                    difficulty = str(row.get('difficulty', '')).strip() if pd.notna(row.get('difficulty')) else None
                    
                    # Handle points
                    points = 0
                    if 'points' in row and pd.notna(row['points']):
                        try:
                            points = int(float(row['points']))
                            if points < 0:
                                points = 0
                        except (ValueError, TypeError):
                            points = 0
                    
                    # Auto-assign level based on points if points are provided
                    if points > 0:
                        if points < 150:
                            level = 'Beginner'
                        elif points < 250:
                            level = 'Intermediate'
                        else:
                            level = 'Advanced'
                    
                    # Insert the course
                    try:
                        conn.execute('''
                            INSERT INTO courses 
                            (title, description, url, link, source, level, points, category, difficulty, created_at, url_status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            title,
                            description,
                            url,
                            url,
                            source,
                            level,
                            points,
                            category,
                            difficulty,
                            datetime.now().isoformat(),
                            'Pending'
                        ))
                        
                        # Add to existing set to prevent duplicates within the same upload
                        existing_set.add((title.lower(), url.lower()))
                        stats['added'] += 1
                        
                    except Exception as db_error:
                        stats['errors'] += 1
                        print(f"Database insert error for row {index + 1}: {str(db_error)}")
                        continue
                    
                except Exception as row_error:
                    stats['errors'] += 1
                    print(f"Row processing error for row {index + 1}: {str(row_error)}")
                    continue
            
            # Commit the transaction
            try:
                conn.commit()
                print(f"Transaction committed successfully. Stats: {stats}")
            except Exception as commit_error:
                print(f"Commit error: {str(commit_error)}")
                error_desc = generate_user_friendly_error_description(None, 'database_error', None)
                return jsonify({
                    'success': False, 
                    'error': f'Failed to save courses to database: {str(commit_error)}',
                    'error_description': error_desc,
                    'stats': stats
                }), 500
            
            # Generate user-friendly description
            success_description = generate_user_friendly_error_description(stats)
            
            # Prepare response
            response_data = {
                'success': True,
                'message': 'Excel upload completed successfully.',
                'stats': stats,
                'success_description': success_description
            }
            
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            
            return jsonify(response_data)
            
        except Exception as db_error:
            error_desc = generate_user_friendly_error_description(None, 'database_error', None)
            print(f"Database error: {str(db_error)}")
            return jsonify({
                'success': False, 
                'error': f'Database operation failed: {str(db_error)}', 
                'error_description': error_desc
            }), 500
        finally:
            if conn:
                conn.close()
                print("Database connection closed")
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            
    except ImportError as import_error:
        error_desc = generate_user_friendly_error_description(None, 'server_error', 'Required libraries are missing')
        print(f"Import error: {str(import_error)}")
        return jsonify({
            'success': False, 
            'error': f'pandas library is required for Excel processing. Import error: {str(import_error)}', 
            'error_description': error_desc
        }), 500
    except Exception as e:
        error_desc = generate_user_friendly_error_description(None, 'server_error', None)
        print(f"General error: {str(e)}")
        return jsonify({
            'success': False, 
            'error': f'Upload failed: {str(e)}', 
            'error_description': error_desc
        }), 500
