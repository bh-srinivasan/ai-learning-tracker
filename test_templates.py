#!/usr/bin/env python3
"""
Test the My Courses page template rendering
"""
import sys
sys.path.append('.')

from app import app
from flask import render_template

def test_my_courses_template():
    """Test if the My Courses template renders without errors"""
    print("Testing My Courses template rendering...")
    print("=" * 50)
    
    with app.app_context():
        with app.test_request_context():
            try:
                # Simulate some course data
                courses = [
                    {
                        'id': 1,
                        'title': 'Test Course 1',
                        'provider': 'Test Provider',
                        'url': 'https://example.com/course1',
                        'url_status': 'Working',
                        'last_url_check': '2025-01-01 10:00:00'
                    },
                    {
                        'id': 2,
                        'title': 'Test Course 2',
                        'provider': 'Test Provider',
                        'url': 'https://example.com/course2',
                        'url_status': 'Not Working',
                        'last_url_check': '2025-01-01 11:00:00'
                    }
                ]
                
                # Try to render the admin courses template
                result = render_template('admin/courses.html', courses=courses)
                print("✅ SUCCESS: admin/courses.html template rendered successfully")
                print(f"Template length: {len(result)} characters")
                
            except Exception as e:
                print(f"❌ ERROR rendering admin/courses.html: {e}")
                import traceback
                traceback.print_exc()

def test_url_validation_template():
    """Test if the URL validation template renders without errors"""
    print("\nTesting URL validation template rendering...")
    print("=" * 50)
    
    with app.app_context():
        with app.test_request_context():
            try:
                # Simulate course and summary data
                courses = [
                    {
                        'id': 1,
                        'title': 'Test Course 1',
                        'url': 'https://example.com/course1',
                        'url_status': 'Working',
                        'last_url_check': '2025-01-01 10:00:00'
                    }
                ]
                
                summary = {
                    'working': {'count': 5},
                    'not_working': {'count': 2},
                    'broken': {'count': 1},
                    'unchecked': {'count': 3}
                }
                
                # Try to render the URL validation template
                result = render_template('admin/url_validation.html', 
                                       courses=courses, 
                                       summary=summary)
                print("✅ SUCCESS: admin/url_validation.html template rendered successfully")
                print(f"Template length: {len(result)} characters")
                
            except Exception as e:
                print(f"❌ ERROR rendering admin/url_validation.html: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    test_my_courses_template()
    test_url_validation_template()
