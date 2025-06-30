#!/usr/bin/env python3
"""
Test the level management system comprehensively
"""

import sqlite3
from level_manager import LevelManager

def test_level_system():
    print("="*70)
    print("COMPREHENSIVE LEVEL MANAGEMENT SYSTEM TEST")
    print("="*70)
    
    # Initialize level manager
    level_manager = LevelManager()
    
    # Get database connection
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    # Test 1: Level calculation based on points
    print("\n🧪 TEST 1: Level Calculation")
    print("-" * 40)
    
    test_points = [0, 150, 250, 600, 1200]
    for points in test_points:
        level = level_manager.calculate_level_from_points(points)
        print(f"   {points} points → {level}")
    
    # Test 2: Points breakdown
    print("\n🧪 TEST 2: Points Breakdown")
    print("-" * 40)
    
    bharath_user = conn.execute("SELECT * FROM users WHERE username = 'bharath'").fetchone()
    if bharath_user:
        breakdown = level_manager.get_level_points_breakdown(bharath_user['points'], bharath_user['level'])
        print(f"   User: bharath")
        print(f"   Total Points: {breakdown['total_points']}")
        print(f"   Current Level: {breakdown['current_level']}")
        print(f"   Level Points: {breakdown['level_points']}")
        print(f"   Next Level: {breakdown['next_level']}")
        print(f"   Points to Next: {breakdown['points_to_next']}")
        print(f"   Progress: {breakdown['progress_percentage']:.1f}%")
    
    # Test 3: Level restrictions
    print("\n🧪 TEST 3: Level Setting Restrictions")
    print("-" * 40)
    
    if bharath_user:
        user_id = bharath_user['id']
        
        # Test setting various levels
        test_levels = ['Beginner', 'Learner', 'Intermediate', 'Expert']
        for level in test_levels:
            can_set, message = level_manager.can_set_level(user_id, level)
            status = "✅ ALLOWED" if can_set else "❌ BLOCKED"
            print(f"   {level}: {status} - {message}")
    
    # Test 4: Course completion and points
    print("\n🧪 TEST 4: Course Completion Points")
    print("-" * 40)
    
    # Get bharath's completed courses
    if bharath_user:
        user_id = bharath_user['id']
        
        completed_courses = conn.execute('''
            SELECT c.title, c.points, uc.completed, uc.completion_date
            FROM user_courses uc
            JOIN courses c ON uc.course_id = c.id
            WHERE uc.user_id = ?
            ORDER BY uc.completion_date DESC
        ''', (user_id,)).fetchall()
        
        if completed_courses:
            total_points = 0
            for course in completed_courses:
                status = "✅ COMPLETED" if course['completed'] else "⏳ ENROLLED"
                if course['completed']:
                    total_points += course['points']
                print(f"   {course['title']}: {course['points']} pts {status}")
                if course['completion_date']:
                    print(f"     Completed: {course['completion_date']}")
            
            print(f"   \n   💯 Total Points from Courses: {total_points}")
        else:
            print("   No courses found for bharath")
    
    # Test 5: Points log
    print("\n🧪 TEST 5: Recent Points Log")
    print("-" * 40)
    
    if bharath_user:
        points_log = level_manager.get_user_points_log(bharath_user['id'], limit=5)
        
        if points_log:
            for log in points_log:
                action_emoji = {
                    'COURSE_COMPLETED': '✅',
                    'COURSE_UNCOMPLETED': '❌',
                    'LEVEL_CHANGE': '⬆️',
                    'LEVEL_SELECTED': '🎯',
                    'COURSE_UPDATE': '🔄'
                }.get(log['action'], '📝')
                
                course_info = f" - {log['course_title']}" if log['course_title'] else ""
                points_info = f" ({log['points_change']:+d})" if log['points_change'] != 0 else ""
                
                print(f"   {action_emoji} {log['action']}{points_info}{course_info}")
                print(f"     {log['created_at']} | Total: {log['points_after']}")
        else:
            print("   No points log entries found")
    
    # Test 6: User level info
    print("\n🧪 TEST 6: Comprehensive User Info")
    print("-" * 40)
    
    if bharath_user:
        level_info = level_manager.get_user_level_info(bharath_user['id'])
        
        for key, value in level_info.items():
            if key not in ['username']:
                print(f"   {key}: {value}")
    
    conn.close()
    
    print("\n" + "="*70)
    print("✅ ALL TESTS COMPLETED")
    print("="*70)

if __name__ == "__main__":
    test_level_system()
