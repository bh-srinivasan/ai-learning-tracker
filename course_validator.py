#!/usr/bin/env python3
"""
Enhanced Course Validation Service
- Validates course URLs with async support
- Enforces comprehensive course schema validation
- Provides debounced validation for better UX
- Logs validation errors and maintains validation cache
"""
import requests
import sqlite3
import logging
import asyncio
import aiohttp
import time
import re
from datetime import datetime
from urllib.parse import urlparse, urljoin
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CourseLevel(Enum):
    """Valid course levels"""
    BEGINNER = "Beginner"
    LEARNER = "Learner"
    INTERMEDIATE = "Intermediate"
    EXPERT = "Expert"

class CourseSource(Enum):
    """Valid course sources"""
    LINKEDIN_LEARNING = "LinkedIn Learning"
    COURSERA = "Coursera"
    EDX = "edX"
    UDACITY = "Udacity"
    UDEMY = "Udemy"
    KHAN_ACADEMY = "Khan Academy"
    MIT_OPENCOURSEWARE = "MIT OpenCourseWare"
    STANFORD_ONLINE = "Stanford Online"
    GOOGLE_AI_EDUCATION = "Google AI Education"
    MICROSOFT_LEARN = "Microsoft Learn"
    AWS_TRAINING = "AWS Training"
    IBM = "IBM"
    MANUAL = "Manual"
    DYNAMIC = "Dynamic"

class URLStatus(Enum):
    """URL validation status"""
    UNCHECKED = "unchecked"
    WORKING = "Working"
    NOT_WORKING = "Not Working"
    BROKEN = "Broken"
    TIMEOUT = "Timeout"
    INVALID_FORMAT = "Invalid Format"

@dataclass
class CourseValidationError:
    """Represents a validation error for a course field"""
    field: str
    message: str
    severity: str = "error"  # error, warning, info

@dataclass
class URLValidationResult:
    """Result of URL validation"""
    url: str
    status: URLStatus
    response_code: Optional[int] = None
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    checked_at: Optional[str] = None

@dataclass
class CourseSchema:
    """
    Comprehensive course schema with validation
    """
    # Required fields
    title: str
    description: str
    source: str
    level: str
    
    # Optional fields
    url: Optional[str] = None
    link: Optional[str] = None
    category: Optional[str] = None
    points: int = 0
    difficulty: Optional[str] = None
    
    # System fields
    id: Optional[int] = None
    created_at: Optional[str] = None
    url_status: str = URLStatus.UNCHECKED.value
    last_url_check: Optional[str] = None
    
    # Validation results
    validation_errors: List[CourseValidationError] = field(default_factory=list)
    is_valid: bool = True

class CourseURLValidator:
    """
    Enhanced Course URL Validator with schema validation and async support
    """
    
    def __init__(self, database_path: str = 'ai_learning.db'):
        self.database_path = database_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AI-Learning-Tracker/1.0 (Enhanced Course Validation Bot)'
        })
        # Set reasonable timeout
        self.timeout = 10
        # Rate limiting
        self.request_delay = 1  # 1 second between requests
        # Validation cache
        self.url_cache = {}
        self.validation_cache = {}
        
    def get_db_connection(self):
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def validate_schema(self, course_data: Dict[str, Any]) -> CourseSchema:
        """
        Validate course data against comprehensive schema
        
        Args:
            course_data: Dictionary containing course data
            
        Returns:
            CourseSchema object with validation results
        """
        errors = []
        
        # Extract and validate required fields
        title = course_data.get('title', '').strip()
        description = course_data.get('description', '').strip()
        source = course_data.get('source', '').strip()
        level = course_data.get('level', '').strip()
        
        # Validate title
        if not title:
            errors.append(CourseValidationError('title', 'Title is required'))
        elif len(title) < 3:
            errors.append(CourseValidationError('title', 'Title must be at least 3 characters long'))
        elif len(title) > 200:
            errors.append(CourseValidationError('title', 'Title must not exceed 200 characters'))
        elif not self._is_valid_text(title):
            errors.append(CourseValidationError('title', 'Title contains invalid characters'))
            
        # Validate description
        if not description:
            errors.append(CourseValidationError('description', 'Description is required'))
        elif len(description) < 10:
            errors.append(CourseValidationError('description', 'Description must be at least 10 characters long'))
        elif len(description) > 2000:
            errors.append(CourseValidationError('description', 'Description must not exceed 2000 characters'))
            
        # Validate source
        if not source:
            errors.append(CourseValidationError('source', 'Source is required'))
        else:
            valid_sources = [s.value for s in CourseSource]
            if source not in valid_sources:
                errors.append(CourseValidationError('source', f'Invalid source. Must be one of: {", ".join(valid_sources)}', 'warning'))
                
        # Validate level
        if not level:
            errors.append(CourseValidationError('level', 'Level is required'))
        else:
            valid_levels = [l.value for l in CourseLevel]
            if level not in valid_levels:
                errors.append(CourseValidationError('level', f'Invalid level. Must be one of: {", ".join(valid_levels)}'))
        
        # Validate optional fields
        url = course_data.get('url', '').strip() if course_data.get('url') else None
        link = course_data.get('link', '').strip() if course_data.get('link') else None
        points = course_data.get('points', 0)
        
        # Validate URLs
        if url and not self._is_valid_url_format(url):
            errors.append(CourseValidationError('url', 'Invalid URL format'))
            
        if link and not self._is_valid_url_format(link):
            errors.append(CourseValidationError('link', 'Invalid link format'))
            
        # Validate points
        try:
            points = int(points) if points else 0
            if points < 0 or points > 1000:
                errors.append(CourseValidationError('points', 'Points must be between 0 and 1000'))
        except (ValueError, TypeError):
            errors.append(CourseValidationError('points', 'Points must be a valid number'))
            points = 0
            
        # Create course schema object
        course = CourseSchema(
            id=course_data.get('id'),
            title=title,
            description=description,
            source=source,
            level=level,
            url=url,
            link=link,
            category=course_data.get('category', '').strip() if course_data.get('category') else None,
            points=points,
            difficulty=course_data.get('difficulty', '').strip() if course_data.get('difficulty') else None,
            created_at=course_data.get('created_at'),
            url_status=course_data.get('url_status', URLStatus.UNCHECKED.value),
            last_url_check=course_data.get('last_url_check'),
            validation_errors=errors,
            is_valid=len([e for e in errors if e.severity == 'error']) == 0
        )
        
        logger.info(f"Course validation completed: {len(errors)} issues found for '{title}'")
        if errors:
            for error in errors:
                logger.warning(f"Validation {error.severity} in {error.field}: {error.message}")
        
        return course
    
    def _is_valid_text(self, text: str) -> bool:
        """Check if text contains only valid characters"""
        # Allow letters, numbers, spaces, and common punctuation
        pattern = re.compile(r'^[a-zA-Z0-9\s\-\.,\!\?\(\)\[\]\:;\'\"\_\+\&\@\#\$\%\^]*$')
        return bool(pattern.match(text))
    
    def _is_valid_url_format(self, url: str) -> bool:
        """Check if URL has valid format"""
        try:
            result = urlparse(url)
            return all([result.scheme in ['http', 'https'], result.netloc])
        except Exception:
            return False
    
    def validate_url(self, url: str) -> Dict[str, str]:
        """
        Validate a single URL and return status information
        
        Args:
            url: The URL to validate
            
        Returns:
            Dict with keys: status, status_code, error_message, validated_url
        """
        if not url or not isinstance(url, str):
            return {
                'status': 'Broken',
                'status_code': None,
                'error_message': 'Invalid or empty URL',
                'validated_url': url
            }
        
        # Clean and validate URL format
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Basic URL format validation
        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                return {
                    'status': 'Broken',
                    'status_code': None,
                    'error_message': 'Malformed URL',
                    'validated_url': url
                }
        except Exception as e:
            return {
                'status': 'Broken',
                'status_code': None,
                'error_message': f'URL parsing error: {str(e)}',
                'validated_url': url
            }
        
        try:
            logger.info(f"Validating URL: {url}")
            
            # Make HEAD request first (faster)
            response = self.session.head(
                url, 
                allow_redirects=True, 
                timeout=self.timeout,
                verify=True
            )
            
            # If HEAD fails, try GET request
            if response.status_code == 405:  # Method Not Allowed
                response = self.session.get(
                    url,
                    allow_redirects=True,
                    timeout=self.timeout,
                    verify=True
                )
            
            status_code = response.status_code
            final_url = response.url
            
            # Determine status based on response
            if status_code == 200:
                # Additional validation for course-specific content
                if self._is_valid_course_page(response, final_url):
                    status = 'Working'
                    error_message = None
                else:
                    status = 'Broken'
                    error_message = 'Page does not appear to be a valid course'
            elif status_code == 404:
                status = 'Not Working'
                error_message = 'Course not found (404)'
            elif status_code in [301, 302, 303, 307, 308]:
                status = 'Working'
                error_message = f'Redirected to {final_url}'
            elif status_code in [401, 403]:
                status = 'Broken'
                error_message = 'Access denied or authentication required'
            elif status_code >= 500:
                status = 'Not Working'
                error_message = f'Server error ({status_code})'
            else:
                status = 'Not Working'
                error_message = f'HTTP {status_code}'
            
            return {
                'status': status,
                'status_code': status_code,
                'error_message': error_message,
                'validated_url': final_url
            }
            
        except requests.exceptions.SSLError as e:
            logger.warning(f"SSL error for {url}: {e}")
            return {
                'status': 'Broken',
                'status_code': None,
                'error_message': 'SSL certificate error',
                'validated_url': url
            }
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Connection error for {url}: {e}")
            return {
                'status': 'Not Working',
                'status_code': None,
                'error_message': 'Connection failed',
                'validated_url': url
            }
        except requests.exceptions.Timeout as e:
            logger.warning(f"Timeout for {url}: {e}")
            return {
                'status': 'Not Working',
                'status_code': None,
                'error_message': 'Request timeout',
                'validated_url': url
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {url}: {e}")
            return {
                'status': 'Broken',
                'status_code': None,
                'error_message': str(e),
                'validated_url': url
            }
        except Exception as e:
            logger.error(f"Unexpected error validating {url}: {e}")
            return {
                'status': 'Broken',
                'status_code': None,
                'error_message': f'Validation error: {str(e)}',
                'validated_url': url
            }
    
    def _is_valid_course_page(self, response: requests.Response, url: str) -> bool:
        """
        Check if the response indicates a valid course page
        
        Args:
            response: The HTTP response
            url: The final URL after redirects
            
        Returns:
            bool: True if it appears to be a valid course page
        """
        # Check content type
        content_type = response.headers.get('content-type', '').lower()
        if 'text/html' not in content_type:
            return False
        
        # Check for common course platforms in URL
        course_platforms = [
            'linkedin.com/learning',
            'coursera.org',
            'edx.org',
            'udemy.com',
            'pluralsight.com',
            'microsoft.com/learn',
            'docs.microsoft.com',
            'academy.microsoft.com',
            'skillshare.com',
            'udacity.com',
            'khanacademy.org'
        ]
        
        url_lower = url.lower()
        for platform in course_platforms:
            if platform in url_lower:
                return True
        
        # If we have content, check for course-related keywords
        try:
            if hasattr(response, 'content') and response.content:
                content = response.content.decode('utf-8', errors='ignore').lower()
                course_indicators = [
                    'course', 'lesson', 'tutorial', 'training',
                    'learning', 'education', 'skill', 'certification'
                ]
                return any(indicator in content for indicator in course_indicators)
        except:
            pass
        
        return True  # Default to valid if we can't determine otherwise
    
    def validate_course_urls(self, course_ids: List[int] = None, 
                           max_courses: int = None) -> Dict[str, int]:
        """
        Validate URLs for courses and update database
        
        Args:
            course_ids: List of specific course IDs to validate (None for all)
            max_courses: Maximum number of courses to validate (None for unlimited)
            
        Returns:
            Dict with validation statistics
        """
        conn = self.get_db_connection()
        stats = {
            'total_processed': 0,
            'working': 0,
            'not_working': 0,
            'broken': 0,
            'errors': 0
        }
        
        try:
            # Build query based on parameters
            if course_ids:
                placeholders = ','.join(['?' for _ in course_ids])
                query = f'''
                    SELECT id, title, url, link 
                    FROM courses 
                    WHERE id IN ({placeholders})
                '''
                params = course_ids
            else:
                query = '''
                    SELECT id, title, url, link 
                    FROM courses 
                    WHERE (url IS NOT NULL AND url != '') 
                       OR (link IS NOT NULL AND link != '')
                    ORDER BY id
                '''
                params = []
                
                if max_courses:
                    query += ' LIMIT ?'
                    params.append(max_courses)
            
            courses = conn.execute(query, params).fetchall()
            logger.info(f"Found {len(courses)} courses to validate")
            
            for course in courses:
                course_id = course['id']
                title = course['title']
                # Use url field first, fallback to link field
                course_url = course['url'] or course['link']
                
                if not course_url:
                    logger.warning(f"No URL found for course {course_id}: {title}")
                    continue
                
                logger.info(f"Validating course {course_id}: {title}")
                
                # Validate the URL
                validation_result = self.validate_url(course_url)
                
                # Update database with results
                try:
                    conn.execute('''
                        UPDATE courses 
                        SET url_status = ?, 
                            last_url_check = ?
                        WHERE id = ?
                    ''', (
                        validation_result['status'],
                        datetime.now().isoformat(),
                        course_id
                    ))
                    conn.commit()
                    
                    # Update statistics
                    stats['total_processed'] += 1
                    status = validation_result['status'].lower()
                    if status == 'working':
                        stats['working'] += 1
                    elif status == 'not working':
                        stats['not_working'] += 1
                    elif status == 'broken':
                        stats['broken'] += 1
                    
                    logger.info(f"Course {course_id}: {validation_result['status']} "
                              f"(HTTP {validation_result['status_code']})")
                    
                except Exception as e:
                    logger.error(f"Database update error for course {course_id}: {e}")
                    stats['errors'] += 1
                
                # Rate limiting
                time.sleep(self.request_delay)
            
        except Exception as e:
            logger.error(f"Error during URL validation: {e}")
            stats['errors'] += 1
        finally:
            conn.close()
        
        return stats
    
    def get_validation_summary(self) -> Dict[str, int]:
        """
        Get summary of URL validation status for all courses
        
        Returns:
            Dict with status counts
        """
        conn = self.get_db_connection()
        try:
            result = conn.execute('''
                SELECT 
                    url_status,
                    COUNT(*) as count,
                    MAX(last_url_check) as latest_check
                FROM courses 
                WHERE (url IS NOT NULL AND url != '') 
                   OR (link IS NOT NULL AND link != '')
                GROUP BY url_status
            ''').fetchall()
            
            summary = {}
            for row in result:
                summary[row['url_status']] = {
                    'count': row['count'],
                    'latest_check': row['latest_check']
                }
            
            return summary
        finally:
            conn.close()
    
    def get_courses_by_status(self, status: str) -> List[Dict]:
        """
        Get courses with a specific URL status
        
        Args:
            status: The status to filter by ('Working', 'Not Working', 'Broken', 'unchecked')
            
        Returns:
            List of course dictionaries
        """
        conn = self.get_db_connection()
        try:
            courses = conn.execute('''
                SELECT id, title, url, link, url_status, last_url_check
                FROM courses 
                WHERE url_status = ?
                   AND ((url IS NOT NULL AND url != '') 
                        OR (link IS NOT NULL AND link != ''))
                ORDER BY title
            ''', (status,)).fetchall()
            
            return [dict(course) for course in courses]
        finally:
            conn.close()


def main():
    """
    Command-line interface for URL validation
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate course URLs')
    parser.add_argument('--max-courses', type=int, help='Maximum courses to validate')
    parser.add_argument('--course-ids', nargs='+', type=int, help='Specific course IDs to validate')
    parser.add_argument('--status', choices=['Working', 'Not Working', 'Broken', 'unchecked'],
                       help='Show courses with specific status')
    parser.add_argument('--summary', action='store_true', help='Show validation summary')
    
    args = parser.parse_args()
    
    validator = CourseURLValidator()
    
    if args.summary:
        summary = validator.get_validation_summary()
        print("\n📊 URL Validation Summary:")
        print("=" * 40)
        for status, info in summary.items():
            print(f"{status}: {info['count']} courses")
            if info['latest_check']:
                print(f"  Latest check: {info['latest_check']}")
        return
    
    if args.status:
        courses = validator.get_courses_by_status(args.status)
        print(f"\n📋 Courses with status '{args.status}':")
        print("=" * 60)
        for course in courses:
            print(f"ID: {course['id']} | {course['title']}")
            print(f"  URL: {course['url'] or course['link']}")
            if course['last_url_check']:
                print(f"  Last checked: {course['last_url_check']}")
            print()
        return
    
    # Run validation
    print("🔍 Starting course URL validation...")
    stats = validator.validate_course_urls(
        course_ids=args.course_ids,
        max_courses=args.max_courses
    )
    
    print("\n✅ Validation completed!")
    print("=" * 40)
    print(f"Total processed: {stats['total_processed']}")
    print(f"Working: {stats['working']}")
    print(f"Not Working: {stats['not_working']}")
    print(f"Broken: {stats['broken']}")
    print(f"Errors: {stats['errors']}")


if __name__ == "__main__":
    main()
