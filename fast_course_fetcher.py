"""
Fast Course Fetcher - AI Learning Tracker
Fetches AI/ML courses from various APIs (Microsoft Learn, GitHub, etc.)
"""

import requests
import time
import json
import sqlite3
from datetime import datetime
import threading
from typing import Dict, List, Any

class FastCourseFetcher:
    def __init__(self, db_path: str = 'ai_learning.db'):
        self.db_path = db_path
        self.fetch_status = {}
        
    def start_fetch(self, fetch_id: str) -> bool:
        """Start asynchronous course fetching"""
        try:
            # Initialize status
            self.fetch_status[fetch_id] = {
                'status': 'fetching',
                'message': 'Starting course fetch...',
                'courses_added': 0,
                'apis_used': 0,
                'start_time': time.time()
            }
            
            # Start background thread
            thread = threading.Thread(target=self._fetch_courses_background, args=(fetch_id,))
            thread.daemon = True
            thread.start()
            
            return True
        except Exception as e:
            self.fetch_status[fetch_id] = {
                'status': 'error',
                'message': f'Failed to start fetch: {str(e)}'
            }
            return False
    
    def get_status(self, fetch_id: str) -> Dict[str, Any]:
        """Get current fetch status"""
        return self.fetch_status.get(fetch_id, {'status': 'not_found'})
    
    def _fetch_courses_background(self, fetch_id: str):
        """Background thread to fetch courses"""
        try:
            courses_added = 0
            apis_used = 0
            
            # Update status
            self.fetch_status[fetch_id]['message'] = 'Fetching from Microsoft Learn...'
            
            # Fetch from Microsoft Learn API
            ms_courses = self._fetch_microsoft_learn_courses()
            if ms_courses:
                added = self._save_courses_to_db(ms_courses, 'Microsoft Learn')
                courses_added += added
                apis_used += 1
                
            self.fetch_status[fetch_id]['message'] = 'Fetching from GitHub...'
            
            # Fetch from GitHub (mock implementation)
            github_courses = self._fetch_github_courses()
            if github_courses:
                added = self._save_courses_to_db(github_courses, 'GitHub')
                courses_added += added
                apis_used += 1
            
            # Calculate total time
            total_time = round(time.time() - self.fetch_status[fetch_id]['start_time'], 2)
            
            # Update final status
            self.fetch_status[fetch_id] = {
                'status': 'complete',
                'result': {
                    'courses_added': courses_added,
                    'apis_used': apis_used,
                    'total_time': total_time
                }
            }
            
        except Exception as e:
            self.fetch_status[fetch_id] = {
                'status': 'error',
                'message': f'Fetch failed: {str(e)}'
            }
    
    def _fetch_microsoft_learn_courses(self) -> List[Dict]:
        """Fetch courses from Microsoft Learn API"""
        try:
            # Simulated Microsoft Learn courses (replace with real API)
            courses = [
                {
                    'title': 'Introduction to AI with Python',
                    'level': 'Beginner',
                    'description': 'Learn the basics of artificial intelligence using Python programming.',
                    'link': 'https://docs.microsoft.com/learn/paths/intro-to-ai-python',
                    'points': 100
                },
                {
                    'title': 'Machine Learning Fundamentals',
                    'level': 'Intermediate', 
                    'description': 'Understand core machine learning concepts and algorithms.',
                    'link': 'https://docs.microsoft.com/learn/paths/ml-fundamentals',
                    'points': 150
                },
                {
                    'title': 'GitHub Copilot for Developers',
                    'level': 'Intermediate',
                    'description': 'Master AI-powered coding with GitHub Copilot.',
                    'link': 'https://docs.microsoft.com/learn/paths/github-copilot',
                    'points': 120
                },
                {
                    'title': 'Azure OpenAI Service',
                    'level': 'Expert',
                    'description': 'Build AI applications using Azure OpenAI Service.',
                    'link': 'https://docs.microsoft.com/learn/paths/azure-openai',
                    'points': 200
                },
                {
                    'title': 'Computer Vision with Azure',
                    'level': 'Intermediate',
                    'description': 'Develop computer vision solutions using Azure Cognitive Services.',
                    'link': 'https://docs.microsoft.com/learn/paths/computer-vision-azure',
                    'points': 180
                }
            ]
            return courses
        except Exception as e:
            print(f"Error fetching Microsoft Learn courses: {e}")
            return []
    
    def _fetch_github_courses(self) -> List[Dict]:
        """Fetch courses from GitHub repositories"""
        try:
            # Simulated GitHub courses
            courses = [
                {
                    'title': 'Machine Learning with TensorFlow',
                    'level': 'Expert',
                    'description': 'Advanced machine learning techniques using TensorFlow.',
                    'link': 'https://github.com/tensorflow/tensorflow/tree/master/tensorflow/examples',
                    'points': 220
                },
                {
                    'title': 'Natural Language Processing Basics',
                    'level': 'Beginner',
                    'description': 'Learn NLP fundamentals with practical examples.',
                    'link': 'https://github.com/microsoft/nlp-recipes',
                    'points': 90
                },
                {
                    'title': 'Deep Learning with PyTorch',
                    'level': 'Expert',
                    'description': 'Master deep learning using PyTorch framework.',
                    'link': 'https://github.com/pytorch/tutorials',
                    'points': 250
                },
                {
                    'title': 'AI Ethics and Responsible AI',
                    'level': 'Learner',
                    'description': 'Understanding ethical considerations in AI development.',
                    'link': 'https://github.com/microsoft/responsible-ai-toolbox',
                    'points': 80
                },
                {
                    'title': 'Automated Machine Learning (AutoML)',
                    'level': 'Intermediate',
                    'description': 'Streamline ML workflows with automated tools.',
                    'link': 'https://github.com/microsoft/nni',
                    'points': 160
                }
            ]
            return courses
        except Exception as e:
            print(f"Error fetching GitHub courses: {e}")
            return []
    
    def _save_courses_to_db(self, courses: List[Dict], source: str) -> int:
        """Save courses to database, avoiding duplicates"""
        added_count = 0
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            for course in courses:
                # Check for duplicates
                existing = conn.execute(
                    'SELECT id FROM courses WHERE LOWER(title) = LOWER(?) OR link = ?',
                    (course['title'], course['link'])
                ).fetchone()
                
                if not existing:
                    conn.execute('''
                        INSERT INTO courses (title, source, level, link, points, description, created_at, url_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        course['title'],
                        source,
                        course['level'],
                        course['link'],
                        course['points'],
                        course['description'],
                        datetime.now().isoformat(),
                        'pending'
                    ))
                    added_count += 1
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error saving courses to database: {e}")
        
        return added_count

# Global fetcher instance
fetcher = FastCourseFetcher()
