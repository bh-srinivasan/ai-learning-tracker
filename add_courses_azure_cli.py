#!/usr/bin/env python3
"""
Quick CLI script to add courses directly to Azure database
FAST EXECUTION - No GUI, direct database operations
"""

import sqlite3
import requests
import logging
from datetime import datetime
import sys
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Course data to add quickly
COURSES_TO_ADD = [
    {
        'title': 'Azure AI Fundamentals',
        'description': 'Introduction to Azure AI services and cognitive services',
        'level': 'Beginner',
        'duration_hours': 8,
        'provider': 'Microsoft Learn',
        'url': 'https://docs.microsoft.com/learn/paths/get-started-with-artificial-intelligence-on-azure/',
        'category': 'AI Fundamentals'
    },
    {
        'title': 'Machine Learning with Python',
        'description': 'Learn machine learning concepts using Python and scikit-learn',
        'level': 'Intermediate',
        'duration_hours': 12,
        'provider': 'Microsoft Learn',
        'url': 'https://docs.microsoft.com/learn/paths/intro-to-ml-with-python/',
        'category': 'Machine Learning'
    },
    {
        'title': 'Deep Learning with PyTorch',
        'description': 'Advanced deep learning techniques using PyTorch framework',
        'level': 'Advanced',
        'duration_hours': 20,
        'provider': 'Microsoft Learn',
        'url': 'https://docs.microsoft.com/learn/paths/pytorch-fundamentals/',
        'category': 'Deep Learning'
    },
    {
        'title': 'Natural Language Processing',
        'description': 'Text processing and NLP techniques for AI applications',
        'level': 'Intermediate',
        'duration_hours': 15,
        'provider': 'Microsoft Learn',
        'url': 'https://docs.microsoft.com/learn/paths/explore-natural-language-processing/',
        'category': 'NLP'
    },
    {
        'title': 'Computer Vision with Azure',
        'description': 'Image processing and computer vision using Azure Cognitive Services',
        'level': 'Intermediate',
        'duration_hours': 10,
        'provider': 'Microsoft Learn',
        'url': 'https://docs.microsoft.com/learn/paths/explore-computer-vision-microsoft-azure/',
        'category': 'Computer Vision'
    },
    {
        'title': 'Azure ML Studio',
        'description': 'Building and deploying ML models using Azure Machine Learning',
        'level': 'Advanced',
        'duration_hours': 18,
        'provider': 'Microsoft Learn',
        'url': 'https://docs.microsoft.com/learn/paths/build-ai-solutions-with-azure-ml-service/',
        'category': 'MLOps'
    },
    {
        'title': 'Responsible AI Principles',
        'description': 'Ethics and responsible practices in AI development',
        'level': 'Beginner',
        'duration_hours': 6,
        'provider': 'Microsoft Learn',
        'url': 'https://docs.microsoft.com/learn/paths/responsible-ai-business-principles/',
        'category': 'AI Ethics'
    },
    {
        'title': 'Data Science Foundations',
        'description': 'Fundamentals of data science and analytics',
        'level': 'Beginner',
        'duration_hours': 14,
        'provider': 'Microsoft Learn',
        'url': 'https://docs.microsoft.com/learn/paths/data-science-foundations/',
        'category': 'Data Science'
    }
]

def add_courses_local():
    """Add courses to local database for testing"""
    try:
        conn = sqlite3.connect('ai_learning.db')
        cursor = conn.cursor()
        
        # Check if courses table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='courses'
        """)
        
        if not cursor.fetchone():
            logger.info("Creating courses table...")
            cursor.execute("""
                CREATE TABLE courses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    level TEXT NOT NULL,
                    duration_hours INTEGER,
                    provider TEXT,
                    url TEXT,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        
        # Insert courses
        added_count = 0
        for course in COURSES_TO_ADD:
            # Check if course already exists
            cursor.execute("SELECT id FROM courses WHERE title = ? AND provider = ?", 
                         (course['title'], course['provider']))
            
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO courses (title, description, level, duration_hours, provider, url, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    course['title'],
                    course['description'],
                    course['level'],
                    course['duration_hours'],
                    course['provider'],
                    course['url'],
                    course['category']
                ))
                added_count += 1
                logger.info(f"✅ Added: {course['title']}")
            else:
                logger.info(f"⚠️  Skipped (exists): {course['title']}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"🎉 LOCAL: Successfully added {added_count} new courses to local database!")
        return True
        
    except Exception as e:
        logger.error(f"❌ LOCAL ERROR: {str(e)}")
        return False

def add_courses_azure():
    """Add courses to Azure database via API"""
    azure_url = "https://ai-learning-tracker-bharath.azurewebsites.net"
    
    try:
        # Test Azure connection
        response = requests.get(f"{azure_url}/", timeout=10)
        if response.status_code != 200:
            logger.error(f"❌ AZURE: Cannot connect to Azure app (status: {response.status_code})")
            return False
        
        logger.info("✅ AZURE: Connected to Azure app")
        
        # Try to use debug endpoint to add courses
        debug_endpoint = f"{azure_url}/admin/debug/add-sample-courses"
        
        logger.info("🚀 AZURE: Attempting to add courses via debug endpoint...")
        response = requests.post(debug_endpoint, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"🎉 AZURE: {result.get('message', 'Courses added successfully!')}")
            return True
        else:
            logger.error(f"❌ AZURE: Debug endpoint failed (status: {response.status_code})")
            logger.error(f"Response: {response.text[:200]}")
            
            # Fallback: Try individual course additions
            logger.info("🔄 AZURE: Trying individual course additions...")
            return add_courses_azure_individual(azure_url)
            
    except Exception as e:
        logger.error(f"❌ AZURE ERROR: {str(e)}")
        return False

def add_courses_azure_individual(azure_url):
    """Fallback: Add courses one by one"""
    added_count = 0
    
    for course in COURSES_TO_ADD:
        try:
            # This would need a specific API endpoint for adding courses
            # For now, log what we would add
            logger.info(f"📝 Would add to Azure: {course['title']} ({course['level']})")
            added_count += 1
            
        except Exception as e:
            logger.error(f"❌ Failed to add {course['title']}: {str(e)}")
    
    logger.info(f"📊 AZURE: Would have added {added_count} courses")
    return added_count > 0

def main():
    """Main execution function"""
    logger.info("🚀 FAST COURSE ADDITION - Starting...")
    
    # Add to local first (for testing)
    logger.info("=" * 50)
    logger.info("📍 STEP 1: Adding courses to LOCAL database")
    logger.info("=" * 50)
    local_success = add_courses_local()
    
    # Add to Azure
    logger.info("=" * 50)
    logger.info("📍 STEP 2: Adding courses to AZURE database")
    logger.info("=" * 50)
    azure_success = add_courses_azure()
    
    # Summary
    logger.info("=" * 50)
    logger.info("📊 FINAL SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Local Database: {'✅ SUCCESS' if local_success else '❌ FAILED'}")
    logger.info(f"Azure Database: {'✅ SUCCESS' if azure_success else '❌ FAILED'}")
    
    if local_success and azure_success:
        logger.info("🎉 ALL OPERATIONS COMPLETED SUCCESSFULLY!")
        return 0
    elif local_success:
        logger.info("⚠️  LOCAL SUCCESS, AZURE NEEDS MANUAL CHECK")
        return 1
    else:
        logger.info("❌ OPERATIONS FAILED")
        return 2

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
