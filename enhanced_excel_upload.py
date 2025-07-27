#!/usr/bin/env python3
"""
Enhanced Excel Upload Manager
Provides cross-environment Excel file upload functionality with comprehensive feedback,
row-by-row processing details, and production-safe error handling.
"""

import os
import sys
import logging
import tempfile
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import request, jsonify

# Import the upload reports manager for persistent reporting
from upload_reports_manager import create_upload_report, add_row_detail

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RowProcessingResult:
    """Represents the processing result for a single Excel row"""
    
    def __init__(self, row_number: int, raw_data: Dict[str, Any]):
        self.row_number = row_number
        self.raw_data = raw_data
        self.status = 'pending'  # pending, success, skipped, error
        self.action = None  # inserted, skipped_duplicate, skipped_invalid, error
        self.error_message = None
        self.processed_data = {}
        self.validation_warnings = []
    
    def mark_success(self, action: str, processed_data: Dict[str, Any]):
        """Mark row as successfully processed"""
        self.status = 'success'
        self.action = action
        self.processed_data = processed_data
    
    def mark_skipped(self, reason: str):
        """Mark row as skipped with reason"""
        self.status = 'skipped'
        self.action = f'skipped_{reason}'
        self.error_message = reason
    
    def mark_error(self, error_message: str):
        """Mark row as failed with error"""
        self.status = 'error'
        self.action = 'error'
        self.error_message = error_message
    
    def add_warning(self, warning: str):
        """Add a validation warning"""
        self.validation_warnings.append(warning)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response"""
        return {
            'row_number': self.row_number,
            'status': self.status,
            'action': self.action,
            'error_message': self.error_message,
            'processed_data': {
                'title': self.processed_data.get('title', ''),
                'url': self.processed_data.get('url', ''),
                'source': self.processed_data.get('source', ''),
                'level': self.processed_data.get('level', ''),
                'points': self.processed_data.get('points', 0)
            } if self.processed_data else {},
            'warnings': self.validation_warnings,
            'raw_data_preview': {
                'title': str(self.raw_data.get('title', ''))[:50],
                'url': str(self.raw_data.get('url', ''))[:50],
                'source': str(self.raw_data.get('source', ''))[:20],
                'level': str(self.raw_data.get('level', ''))[:20]
            }
        }


class ExcelUploadManager:
    """Manages Excel file uploads with environment-aware database operations"""
    
    def __init__(self, db_manager):
        """
        Initialize with database manager
        Args:
            db_manager: DatabaseEnvironmentManager instance
        """
        self.db_manager = db_manager
        self.required_columns = ['title', 'url', 'source', 'level']
        self.optional_columns = ['description', 'points', 'category', 'difficulty']
        self.valid_levels = ['Beginner', 'Intermediate', 'Advanced']
        self.max_file_size_mb = 10
        self.allowed_extensions = {'.xlsx', '.xls'}
        
        logger.info(f"🚀 ExcelUploadManager initialized for {db_manager.environment} environment")
    
    def validate_file_upload(self, request_files) -> Tuple[bool, str, Any]:
        """
        Validate the uploaded file
        Returns: (is_valid, error_message, file_object)
        """
        try:
            # Check if file was uploaded
            if 'excel_file' not in request_files:
                return False, "No file uploaded. Please select an Excel file.", None
            
            file = request_files['excel_file']
            
            # Check if filename is empty
            if not file.filename or file.filename == '':
                return False, "No file selected. Please choose an Excel file to upload.", None
            
            # Secure the filename
            filename = secure_filename(file.filename)
            if not filename:
                return False, "Invalid filename. Please use a valid Excel file name.", None
            
            # Check file extension
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext not in self.allowed_extensions:
                return False, f"Invalid file type '{file_ext}'. Please upload an Excel file (.xlsx or .xls).", None
            
            # Check file size (read content length if available)
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            max_size_bytes = self.max_file_size_mb * 1024 * 1024
            if file_size > max_size_bytes:
                return False, f"File too large ({file_size/1024/1024:.1f}MB). Maximum size is {self.max_file_size_mb}MB.", None
            
            logger.info(f"📄 File validation passed: {filename} ({file_size/1024:.1f}KB)")
            return True, "", file
            
        except Exception as e:
            logger.error(f"❌ File validation error: {e}")
            return False, f"File validation failed: {str(e)}", None
    
    def read_excel_file(self, file) -> Tuple[bool, str, Any]:
        """
        Read and validate Excel file content
        Returns: (is_valid, error_message, dataframe)
        """
        try:
            import pandas as pd
            
            # Create temporary file for secure processing
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
                file.save(temp_file.name)
                temp_path = temp_file.name
            
            try:
                # Read Excel file
                df = pd.read_excel(temp_path)
                logger.info(f"📊 Excel file read successfully: {len(df)} rows, columns: {list(df.columns)}")
                
                # Basic validation
                if df.empty:
                    return False, "Excel file is empty. Please provide a file with course data.", None
                
                if len(df) > 1000:
                    return False, f"File too large ({len(df)} rows). Maximum 1000 rows allowed for safety.", None
                
                return True, "", df
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except Exception as cleanup_error:
                    logger.warning(f"⚠️ Failed to cleanup temp file: {cleanup_error}")
                
        except ImportError:
            return False, "pandas library is not available. Cannot process Excel files.", None
        except Exception as e:
            logger.error(f"❌ Excel read error: {e}")
            return False, f"Failed to read Excel file: {str(e)}", None
    
    def validate_columns(self, df) -> Tuple[bool, str]:
        """
        Validate that required columns are present
        Returns: (is_valid, error_message)
        """
        try:
            missing_columns = [col for col in self.required_columns if col not in df.columns]
            
            if missing_columns:
                available_cols = ", ".join(df.columns.tolist())
                required_cols = ", ".join(self.required_columns)
                return False, f"Missing required columns: {', '.join(missing_columns)}. Required: {required_cols}. Available: {available_cols}"
            
            logger.info(f"✅ Column validation passed. Required columns present: {self.required_columns}")
            return True, ""
            
        except Exception as e:
            logger.error(f"❌ Column validation error: {e}")
            return False, f"Column validation failed: {str(e)}"
    
    def get_existing_courses(self) -> Dict[Tuple[str, str], bool]:
        """
        Get existing courses from database for duplicate checking
        Returns: Dictionary with (title, url) tuples as keys
        """
        try:
            if not self.db_manager.connection:
                raise RuntimeError("No database connection available")
            
            cursor = self.db_manager.connection.cursor()
            
            if self.db_manager.environment == 'production':
                # Azure SQL syntax
                cursor.execute("SELECT title, url FROM courses WHERE title IS NOT NULL AND url IS NOT NULL")
            else:
                # SQLite syntax
                cursor.execute("SELECT title, url FROM courses WHERE title IS NOT NULL AND url IS NOT NULL")
            
            existing_courses = cursor.fetchall()
            existing_set = {}
            
            for row in existing_courses:
                title = row[0] if row[0] else ''
                url = row[1] if row[1] else ''
                if title and url:
                    key = (title.lower().strip(), url.lower().strip())
                    existing_set[key] = True
            
            logger.info(f"📋 Found {len(existing_set)} existing courses for duplicate checking")
            return existing_set
            
        except Exception as e:
            logger.error(f"❌ Failed to get existing courses: {e}")
            return {}
    
    def validate_and_process_row(self, row_data: Dict[str, Any], existing_courses: Dict[Tuple[str, str], bool]) -> RowProcessingResult:
        """
        Validate and process a single row from the Excel file
        Returns: RowProcessingResult object
        """
        import pandas as pd
        
        row_number = row_data.get('_row_number', 0)
        result = RowProcessingResult(row_number, row_data)
        
        try:
            # Extract and clean required fields
            title = str(row_data.get('title', '')).strip() if pd.notna(row_data.get('title')) else ''
            url = str(row_data.get('url', '')).strip() if pd.notna(row_data.get('url')) else ''
            source = str(row_data.get('source', '')).strip() if pd.notna(row_data.get('source')) else ''
            level = str(row_data.get('level', '')).strip() if pd.notna(row_data.get('level')) else ''
            
            # Validate required fields
            if not title:
                result.mark_error("Missing or empty title")
                return result
            if not url:
                result.mark_error("Missing or empty URL")
                return result
            if not source:
                result.mark_error("Missing or empty source")
                return result
            if not level:
                result.mark_error("Missing or empty level")
                return result
            
            # Validate level
            if level not in self.valid_levels:
                result.mark_error(f"Invalid level '{level}'. Must be one of: {', '.join(self.valid_levels)}")
                return result
            
            # Validate URL format
            if not url.startswith(('http://', 'https://')):
                result.mark_error(f"Invalid URL format. Must start with http:// or https://")
                return result
            
            # Check for duplicates
            duplicate_key = (title.lower().strip(), url.lower().strip())
            if duplicate_key in existing_courses:
                result.mark_skipped("duplicate - course with same title and URL already exists")
                return result
            
            # Process optional fields
            description = str(row_data.get('description', '')).strip() if pd.notna(row_data.get('description')) else ''
            category = str(row_data.get('category', '')).strip() if pd.notna(row_data.get('category')) else None
            difficulty = str(row_data.get('difficulty', '')).strip() if pd.notna(row_data.get('difficulty')) else None
            
            # Handle points
            points = 0
            if 'points' in row_data and pd.notna(row_data['points']):
                try:
                    points = int(float(row_data['points']))
                    if points < 0:
                        result.add_warning("Negative points converted to 0")
                        points = 0
                    elif points > 1000:
                        result.add_warning("Points over 1000 may be unusually high")
                except (ValueError, TypeError):
                    result.add_warning("Invalid points value, using 0")
                    points = 0
            
            # Auto-assign level based on points if points are provided
            original_level = level
            if points > 0:
                if points < 150:
                    level = 'Beginner'
                elif points < 250:
                    level = 'Intermediate'
                else:
                    level = 'Advanced'
                
                if level != original_level:
                    result.add_warning(f"Level auto-adjusted from '{original_level}' to '{level}' based on points ({points})")
            
            # Prepare processed data
            processed_data = {
                'title': title,
                'description': description,
                'url': url,
                'source': source,
                'level': level,
                'points': points,
                'category': category,
                'difficulty': difficulty
            }
            
            result.processed_data = processed_data
            return result
            
        except Exception as e:
            logger.error(f"❌ Row processing error for row {row_number}: {e}")
            result.mark_error(f"Processing failed: {str(e)}")
            return result
    
    def insert_course_to_database(self, processed_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Insert a single course into the database
        Returns: (success, error_message)
        """
        try:
            if not self.db_manager.connection:
                raise RuntimeError("No database connection available")
            
            cursor = self.db_manager.connection.cursor()
            
            # Prepare SQL based on environment
            if self.db_manager.environment == 'production':
                # Azure SQL - use parameterized query
                sql = """
                    INSERT INTO courses 
                    (title, description, url, link, source, level, points, category, difficulty, created_at, url_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                params = (
                    processed_data['title'],
                    processed_data['description'],
                    processed_data['url'],
                    processed_data['url'],  # Use same URL for both url and link
                    processed_data['source'],
                    processed_data['level'],
                    processed_data['points'],
                    processed_data['category'],
                    processed_data['difficulty'],
                    datetime.now().isoformat(),
                    'unknown'
                )
            else:
                # SQLite - use parameterized query
                sql = """
                    INSERT INTO courses 
                    (title, description, url, link, source, level, points, category, difficulty, created_at, url_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                params = (
                    processed_data['title'],
                    processed_data['description'],
                    processed_data['url'],
                    processed_data['url'],  # Use same URL for both url and link
                    processed_data['source'],
                    processed_data['level'],
                    processed_data['points'],
                    processed_data['category'],
                    processed_data['difficulty'],
                    datetime.now().isoformat(),
                    'unknown'
                )
            
            cursor.execute(sql, params)
            return True, ""
            
        except Exception as e:
            logger.error(f"❌ Database insert error: {e}")
            return False, str(e)
    
    def process_excel_upload(self, request_files, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main method to process Excel file upload
        Returns: Dictionary with processing results and detailed feedback
        """
        import pandas as pd
        
        # Initialize response structure
        response = {
            'success': False,
            'message': '',
            'environment': self.db_manager.environment,
            'timestamp': datetime.now().isoformat(),
            'user': user_info.get('username', 'unknown'),
            'stats': {
                'total_processed': 0,
                'successful': 0,
                'skipped': 0,
                'errors': 0,
                'warnings': 0
            },
            'row_results': [],
            'summary': {
                'file_info': {},
                'processing_time_ms': 0,
                'primary_error': None,
                'recommendations': []
            }
        }
        
        start_time = datetime.now()
        
        try:
            logger.info(f"🚀 Starting Excel upload processing for user: {user_info.get('username')}")
            
            # Step 1: Validate file upload
            is_valid, error_msg, file = self.validate_file_upload(request_files)
            if not is_valid:
                response['message'] = error_msg
                response['summary']['primary_error'] = 'file_validation'
                return response
            
            response['summary']['file_info'] = {
                'filename': secure_filename(file.filename),
                'size_kb': round(file.content_length / 1024, 2) if file.content_length else 'unknown'
            }
            
            # Step 2: Read Excel file
            is_valid, error_msg, df = self.read_excel_file(file)
            if not is_valid:
                response['message'] = error_msg
                response['summary']['primary_error'] = 'file_reading'
                return response
            
            # Step 3: Validate columns
            is_valid, error_msg = self.validate_columns(df)
            if not is_valid:
                response['message'] = error_msg
                response['summary']['primary_error'] = 'column_validation'
                response['summary']['recommendations'] = [
                    "Ensure your Excel file has the required columns: title, url, source, level",
                    "Download the template file for the correct format",
                    "Check column names for typos or extra spaces"
                ]
                return response
            
            # Step 4: Connect to database
            if not self.db_manager.connection:
                try:
                    self.db_manager.connect_to_database()
                except Exception as db_error:
                    response['message'] = f"Database connection failed: {str(db_error)}"
                    response['summary']['primary_error'] = 'database_connection'
                    return response
            
            # Step 5: Get existing courses for duplicate checking
            existing_courses = self.get_existing_courses()
            
            # Step 6: Process each row
            response['stats']['total_processed'] = len(df)
            row_results = []
            
            for index, row in df.iterrows():
                # Add row number for tracking
                row_dict = row.to_dict()
                row_dict['_row_number'] = index + 2  # +2 because Excel rows start at 1 and we skip header
                
                # Validate and process row
                result = self.validate_and_process_row(row_dict, existing_courses)
                
                # Attempt database insertion if validation passed
                if result.status == 'pending':
                    success, db_error = self.insert_course_to_database(result.processed_data)
                    if success:
                        result.mark_success('inserted', result.processed_data)
                        # Add to existing courses to prevent duplicates within same upload
                        key = (result.processed_data['title'].lower(), result.processed_data['url'].lower())
                        existing_courses[key] = True
                        response['stats']['successful'] += 1
                    else:
                        result.mark_error(f"Database insert failed: {db_error}")
                        response['stats']['errors'] += 1
                elif result.status == 'skipped':
                    response['stats']['skipped'] += 1
                elif result.status == 'error':
                    response['stats']['errors'] += 1
                
                # Count warnings
                if result.validation_warnings:
                    response['stats']['warnings'] += len(result.validation_warnings)
                
                row_results.append(result.to_dict())
            
            # Step 7: Commit transaction
            try:
                self.db_manager.connection.commit()
                logger.info(f"✅ Transaction committed successfully")
            except Exception as commit_error:
                logger.error(f"❌ Commit error: {commit_error}")
                response['message'] = f"Failed to save changes to database: {str(commit_error)}"
                response['summary']['primary_error'] = 'database_commit'
                return response
            
            # Step 8: Create persistent upload report
            report_id = None
            try:
                report_id = create_upload_report(
                    user_id=user_info.get('id'),
                    filename=response['summary']['file_info']['filename'],
                    total_rows=len(df),
                    processed_rows=response['stats']['total_processed'],
                    success_count=response['stats']['successful'],
                    error_count=response['stats']['errors'],
                    warnings_count=response['stats']['warnings']
                )
                
                # Add row details to the persistent report
                for result in row_results:
                    status_map = {
                        'success': 'SUCCESS',
                        'skipped': 'SKIPPED', 
                        'error': 'ERROR'
                    }
                    
                    message = result.get('error_message', result.get('action', 'Processed'))
                    if result.get('validation_warnings'):
                        message += f" (Warnings: {', '.join(result['validation_warnings'])})"
                    
                    add_row_detail(
                        report_id=report_id,
                        row_number=result['row_number'],
                        status=status_map.get(result['status'], 'UNKNOWN'),
                        message=message,
                        course_title=result.get('processed_data', {}).get('title'),
                        course_url=result.get('processed_data', {}).get('url')
                    )
                
                logger.info(f"📊 Created persistent upload report: {report_id}")
                response['report_id'] = report_id
                
            except Exception as report_error:
                logger.error(f"⚠️ Failed to create upload report: {report_error}")
                # Don't fail the upload due to reporting issues
                response['report_warning'] = f"Upload succeeded but reporting failed: {str(report_error)}"
            
            # Step 9: Prepare final response
            response['success'] = True
            response['row_results'] = row_results
            
            # Generate summary message
            if response['stats']['successful'] > 0:
                if response['stats']['errors'] == 0 and response['stats']['skipped'] == 0:
                    response['message'] = f"Perfect! All {response['stats']['successful']} courses uploaded successfully."
                elif response['stats']['errors'] > 0:
                    response['message'] = f"Partial success: {response['stats']['successful']} courses uploaded, {response['stats']['errors']} failed, {response['stats']['skipped']} skipped."
                else:
                    response['message'] = f"Upload completed: {response['stats']['successful']} courses uploaded, {response['stats']['skipped']} duplicates skipped."
            else:
                response['success'] = False
                response['message'] = f"No courses were uploaded. {response['stats']['errors']} errors, {response['stats']['skipped']} skipped."
                response['summary']['primary_error'] = 'no_valid_data'
            
            # Add recommendations based on results
            recommendations = []
            if response['stats']['errors'] > 0:
                recommendations.append("Review the detailed error messages below to fix data issues")
            if response['stats']['skipped'] > 0:
                recommendations.append("Skipped items are likely duplicates - check for existing courses")
            if response['stats']['warnings'] > 0:
                recommendations.append("Review warnings for data quality improvements")
            
            response['summary']['recommendations'] = recommendations
            
        except Exception as e:
            logger.error(f"❌ Unexpected error during Excel processing: {e}")
            response['message'] = f"Unexpected error occurred: {str(e)}"
            response['summary']['primary_error'] = 'unexpected_error'
            
        finally:
            # Calculate processing time
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds() * 1000
            response['summary']['processing_time_ms'] = round(processing_time, 2)
            
            logger.info(f"📊 Excel upload completed in {processing_time:.0f}ms: {response['stats']}")
        
        return response


def handle_excel_upload_request(db_manager, get_current_user_func, request_obj):
    """
    Flask route handler for Excel upload requests
    Args:
        db_manager: DatabaseEnvironmentManager instance
        get_current_user_func: Function to get current user
        request_obj: Flask request object
    Returns:
        Flask JSON response
    """
    try:
        # Authenticate user
        user = get_current_user_func()
        if not user or user.get('username') != 'admin':
            logger.warning(f"❌ Unauthorized Excel upload attempt from: {request_obj.remote_addr}")
            return jsonify({
                'success': False,
                'message': 'Admin privileges required for Excel uploads.',
                'error_type': 'authentication',
                'timestamp': datetime.now().isoformat()
            }), 403
        
        logger.info(f"📋 Excel upload request from admin user: {user.get('username')} ({request_obj.remote_addr})")
        
        # Create upload manager and process file
        upload_manager = ExcelUploadManager(db_manager)
        result = upload_manager.process_excel_upload(request_obj.files, user)
        
        # Determine HTTP status code
        if result['success']:
            status_code = 200
        elif result['summary']['primary_error'] in ['authentication', 'file_validation']:
            status_code = 400
        elif result['summary']['primary_error'] in ['database_connection', 'database_commit']:
            status_code = 500
        else:
            status_code = 400
        
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"❌ Excel upload handler error: {e}")
        return jsonify({
            'success': False,
            'message': f'Server error during Excel upload: {str(e)}',
            'error_type': 'server_error',
            'timestamp': datetime.now().isoformat()
        }), 500


if __name__ == "__main__":
    # Test script
    print("🧪 Enhanced Excel Upload Manager - Test Mode")
    print("This module is designed to be imported and used within the Flask application.")
    print("Key features:")
    print("  ✅ Cross-environment database support (SQLite/Azure SQL)")
    print("  ✅ Comprehensive file validation and security")
    print("  ✅ Row-by-row processing with detailed feedback")
    print("  ✅ Production-safe error handling")
    print("  ✅ Real-time progress tracking")
    print("  ✅ Detailed upload summary and recommendations")
