#!/usr/bin/env python3
"""
Detailed debug script to see what the API fetcher finds vs what gets added
"""

import asyncio
import sqlite3
import os
import hashlib
import aiohttp
from fast_course_fetcher import FastCourseAPIFetcher

async def detailed_debug():
    """Debug the course fetching process step by step"""
    print("🔍 DETAILED Course Fetching Debug")
    print("=" * 60)
    
    fetcher = FastCourseAPIFetcher()
    
    # 1. Check existing course hashes
    existing_hashes = fetcher.get_existing_course_hashes()
    print(f"📋 Existing course URL hashes in DB: {len(existing_hashes)}")
    print(f"   Sample hashes: {list(existing_hashes)[:5]}...")
    
    # 2. Fetch courses from APIs
    print(f"\n🌐 Fetching courses from APIs...")
    
    try:
        # Fetch Microsoft Learn courses
        microsoft_courses = await fetcher.fetch_microsoft_learn_courses(3)
        print(f"📚 Microsoft Learn found: {len(microsoft_courses)} courses")
        for i, course in enumerate(microsoft_courses, 1):
            url_hash = hashlib.md5(course['url'].encode()).hexdigest()[:8]
            is_duplicate = url_hash in existing_hashes
            print(f"   {i}. {course['title'][:50]}...")
            print(f"      URL: {course['url']}")
            print(f"      Hash: {url_hash}")
            print(f"      Duplicate: {is_duplicate}")
        
        # Fetch GitHub courses
        github_courses = await fetcher.fetch_github_courses(3)
        print(f"\n🐙 GitHub found: {len(github_courses)} courses")
        for i, course in enumerate(github_courses, 1):
            url_hash = hashlib.md5(course['url'].encode()).hexdigest()[:8]
            is_duplicate = url_hash in existing_hashes
            print(f"   {i}. {course['title'][:50]}...")
            print(f"      URL: {course['url']}")
            print(f"      Hash: {url_hash}")
            print(f"      Duplicate: {is_duplicate}")
        
        # 3. Test URL validation for a few courses
        print(f"\n🔗 Testing URL validation...")
        test_courses = (microsoft_courses[:2] + github_courses[:2])
        
        for course in test_courses:
            is_valid = await fetcher.validate_url(course['url'])
            print(f"   {course['title'][:40]}... → Valid: {is_valid}")
            
    except Exception as e:
        print(f"❌ Error in detailed debug: {e}")
        import traceback
        traceback.print_exc()

async def check_specific_courses():
    """Check for specific new courses that should be available"""
    print(f"\n🎯 Checking for specific new AI courses...")
    
    # Check recent Microsoft Learn AI courses that might not be in our DB
    test_urls = [
        "https://docs.microsoft.com/learn/paths/get-started-with-artificial-intelligence-on-azure/",
        "https://docs.microsoft.com/learn/paths/azure-ai-fundamentals/",
        "https://docs.microsoft.com/learn/paths/introduction-to-github-copilot/",
        "https://github.com/microsoft/AI-For-Beginners",
        "https://github.com/microsoft/ML-For-Beginners"
    ]
    
    # Check if these exist in our database
    db_path = os.path.join(os.path.dirname(__file__), 'ai_learning.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for url in test_urls:
        cursor.execute("SELECT COUNT(*) FROM courses WHERE url = ? OR link = ?", (url, url))
        exists = cursor.fetchone()[0] > 0
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        print(f"   {url}")
        print(f"      Exists in DB: {exists}")
        print(f"      Hash: {url_hash}")
    
    conn.close()

if __name__ == "__main__":
    asyncio.run(detailed_debug())
    asyncio.run(check_specific_courses())
