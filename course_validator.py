"""
Course URL Validator - AI Learning Tracker
Validates course URLs and manages URL status tracking
"""

import requests
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import threading
import time
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CourseURLValidator:
    def __init__(self, db_path: str = 'ai_learning.db', timeout: int = 10):
        self.db_path = db_path
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def validate_single_url(self, url: str, course_id: int = None) -> Dict:
        """Validate a single URL and return status"""
        try:
            # Parse URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return {
                    'status': 'Broken',
                    'response_code': None,
                    'error': 'Invalid URL format',
                    'response_time': None
                }
            
            # Make request
            start_time = time.time()
            response = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            response_time = round((time.time() - start_time) * 1000, 2)  # ms
            
            # Determine status
            if response.status_code == 200:
                status = 'Working'
                error = None
            elif 300 <= response.status_code < 400:
                status = 'Working'  # Redirects are generally OK
                error = f'Redirect: {response.status_code}'
            elif response.status_code == 404:
                status = 'Not Working'
                error = 'Page not found (404)'
            elif response.status_code == 403:
                status = 'Not Working'
                error = 'Access forbidden (403)'
            elif response.status_code >= 500:
                status = 'Broken'
                error = f'Server error ({response.status_code})'
            else:
                status = 'Broken'
                error = f'HTTP {response.status_code}'
            
            result = {
                'status': status,
                'response_code': response.status_code,
                'error': error,
                'response_time': response_time
            }
            
            # Update database if course_id provided
            if course_id:
                self.update_course_url_status(course_id, result)
            
            return result
            
        except requests.exceptions.Timeout:
            result = {
                'status': 'Broken',
                'response_code': None,
                'error': 'Request timeout',
                'response_time': None
            }
            if course_id:
                self.update_course_url_status(course_id, result)
            return result
            
        except requests.exceptions.ConnectionError:
            result = {
                'status': 'Broken',
                'response_code': None,
                'error': 'Connection failed',
                'response_time': None
            }
            if course_id:
                self.update_course_url_status(course_id, result)
            return result
            
        except Exception as e:
            result = {
                'status': 'Broken',
                'response_code': None,
                'error': f'Validation error: {str(e)}',
                'response_time': None
            }
            if course_id:
                self.update_course_url_status(course_id, result)
            return result
    
    def update_course_url_status(self, course_id: int, validation_result: Dict):
        """Update course URL status in database"""
        try:
            conn = self.get_db_connection()
            conn.execute('''
                UPDATE courses 
                SET url_status = ?, 
                    last_url_check = ?,
                    url_response_code = ?,
                    url_error = ?,
                    url_response_time = ?
                WHERE id = ?
            ''', (
                validation_result['status'],
                datetime.now().isoformat(),
                validation_result['response_code'],
                validation_result['error'],
                validation_result['response_time'],
                course_id
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error updating course URL status: {e}")
    
    def get_courses_by_status(self, status: str) -> List[Dict]:
        """Get courses by URL status"""
        try:
            conn = self.get_db_connection()
            if status.lower() == 'unchecked':
                courses = conn.execute('''
                    SELECT id, title, link, url_status, last_url_check
                    FROM courses 
                    WHERE url_status IS NULL OR url_status = 'pending'
                    ORDER BY created_at DESC
                ''').fetchall()
            else:
                courses = conn.execute('''
                    SELECT id, title, link, url_status, last_url_check, url_response_code, url_error
                    FROM courses 
                    WHERE LOWER(url_status) = LOWER(?)
                    ORDER BY last_url_check DESC
                ''', (status,)).fetchall()
            
            conn.close()
            return [dict(course) for course in courses]
        except Exception as e:
            logger.error(f"Error getting courses by status: {e}")
            return []
    
    def get_validation_summary(self) -> Dict:
        """Get summary of URL validation status"""
        try:
            conn = self.get_db_connection()
            
            # Count by status
            working = conn.execute("SELECT COUNT(*) FROM courses WHERE LOWER(url_status) = 'working'").fetchone()[0]
            not_working = conn.execute("SELECT COUNT(*) FROM courses WHERE LOWER(url_status) = 'not working'").fetchone()[0]
            broken = conn.execute("SELECT COUNT(*) FROM courses WHERE LOWER(url_status) = 'broken'").fetchone()[0]
            unchecked = conn.execute("SELECT COUNT(*) FROM courses WHERE url_status IS NULL OR url_status = 'pending'").fetchone()[0]
            
            # Recent checks
            recent_checks = conn.execute('''
                SELECT COUNT(*) FROM courses 
                WHERE last_url_check >= ? AND url_status IS NOT NULL
            ''', (datetime.now() - timedelta(days=7),)).fetchone()[0]
            
            conn.close()
            
            total_courses = working + not_working + broken + unchecked
            
            return {
                'working': {'count': working, 'percentage': round((working/total_courses)*100, 1) if total_courses > 0 else 0},
                'not_working': {'count': not_working, 'percentage': round((not_working/total_courses)*100, 1) if total_courses > 0 else 0},
                'broken': {'count': broken, 'percentage': round((broken/total_courses)*100, 1) if total_courses > 0 else 0},
                'unchecked': {'count': unchecked, 'percentage': round((unchecked/total_courses)*100, 1) if total_courses > 0 else 0},
                'total_courses': total_courses,
                'recent_checks': recent_checks,
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting validation summary: {e}")
            return {
                'working': {'count': 0, 'percentage': 0},
                'not_working': {'count': 0, 'percentage': 0},
                'broken': {'count': 0, 'percentage': 0},
                'unchecked': {'count': 0, 'percentage': 0},
                'total_courses': 0,
                'recent_checks': 0,
                'last_updated': datetime.now().isoformat()
            }
    
    def validate_course_urls(self, course_ids: List[int] = None, status_filter: str = None, max_concurrent: int = 5) -> Dict:
        """Validate multiple course URLs"""
        try:
            conn = self.get_db_connection()
            
            # Build query based on filters
            if course_ids:
                placeholders = ','.join(['?' for _ in course_ids])
                courses = conn.execute(f'''
                    SELECT id, title, link FROM courses 
                    WHERE id IN ({placeholders})
                ''', course_ids).fetchall()
            elif status_filter:
                if status_filter.lower() == 'unchecked':
                    courses = conn.execute('''
                        SELECT id, title, link FROM courses 
                        WHERE url_status IS NULL OR url_status = 'pending'
                    ''').fetchall()
                else:
                    courses = conn.execute('''
                        SELECT id, title, link FROM courses 
                        WHERE LOWER(url_status) = LOWER(?)
                    ''', (status_filter,)).fetchall()
            else:
                courses = conn.execute('SELECT id, title, link FROM courses').fetchall()
            
            conn.close()
            
            # Validate URLs
            results = {
                'total_checked': len(courses),
                'working': 0,
                'not_working': 0,
                'broken': 0,
                'start_time': datetime.now().isoformat(),
                'details': []
            }
            
            for course in courses:
                result = self.validate_single_url(course['link'], course['id'])
                
                # Update counters
                if result['status'] == 'Working':
                    results['working'] += 1
                elif result['status'] == 'Not Working':
                    results['not_working'] += 1
                else:
                    results['broken'] += 1
                
                # Add details
                results['details'].append({
                    'course_id': course['id'],
                    'title': course['title'],
                    'url': course['link'],
                    **result
                })
                
                # Small delay to be respectful
                time.sleep(0.1)
            
            results['end_time'] = datetime.now().isoformat()
            return results
            
        except Exception as e:
            logger.error(f"Error validating course URLs: {e}")
            return {
                'total_checked': 0,
                'working': 0,
                'not_working': 0,
                'broken': 0,
                'error': str(e),
                'start_time': datetime.now().isoformat(),
                'end_time': datetime.now().isoformat(),
                'details': []
            }
    
    def cleanup_old_validation_data(self, days_old: int = 30):
        """Clean up old validation data"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            conn = self.get_db_connection()
            
            # Reset old checks to pending
            conn.execute('''
                UPDATE courses 
                SET url_status = 'pending', url_response_code = NULL, url_error = NULL 
                WHERE last_url_check < ?
            ''', (cutoff_date.isoformat(),))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Cleaned up validation data older than {days_old} days")
        except Exception as e:
            logger.error(f"Error cleaning up old validation data: {e}")

# Global validator instance
validator = CourseURLValidator()
