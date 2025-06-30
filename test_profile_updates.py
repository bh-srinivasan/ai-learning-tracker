#!/usr/bin/env python3
"""
Test profile update functionality
"""

import sqlite3
from level_manager import LevelManager

def test_profile_updates():
    print("="*70)
    print("TESTING PROFILE UPDATE FUNCTIONALITY")
    print("="*70)
    
    # Initialize level manager
    level_manager = LevelManager()
    
    # Get database connection
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    
    # Get bharath user for testing
    bharath_user = conn.execute("SELECT * FROM users WHERE username = 'bharath'").fetchone()
    
    if not bharath_user:
        print("❌ Bharath user not found")
        return
    
    user_id = bharath_user['id']
    
    print(f"\n👤 Testing profile updates for: {bharath_user['username']}")
    print(f"   Current Level: {bharath_user['level']}")
    print(f"   Current Points: {bharath_user['points']}")
    print(f"   Selected Level: {bharath_user['user_selected_level']}")
    
    # Test 1: Update selected level to Learner
    print("\n🧪 TEST 1: Update Selected Level to 'Learner'")
    print("-" * 50)
    
    result = level_manager.update_user_selected_level(user_id, 'Learner')
    print(f"   Result: {result}")
    
    # Verify the update
    updated_user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    print(f"   New Selected Level: {updated_user['user_selected_level']}")
    
    # Test 2: Try to update to Expert (should be allowed as profile setting)
    print("\n🧪 TEST 2: Update Selected Level to 'Expert'")
    print("-" * 50)
    
    result = level_manager.update_user_selected_level(user_id, 'Expert')
    print(f"   Result: {result}")
    
    # Verify the update
    updated_user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    print(f"   New Selected Level: {updated_user['user_selected_level']}")
    
    # Test 3: Check course completion toggle
    print("\n🧪 TEST 3: Test Course Completion Toggle")
    print("-" * 50)
    
    # Get a completed course
    completed_course = conn.execute('''
        SELECT c.id, c.title, c.points, uc.completed
        FROM user_courses uc
        JOIN courses c ON uc.course_id = c.id
        WHERE uc.user_id = ? AND uc.completed = 1
        LIMIT 1
    ''', (user_id,)).fetchone()
    
    if completed_course:
        course_id = completed_course['id']
        print(f"   Testing with course: {completed_course['title']} ({completed_course['points']} pts)")
        
        # Mark as uncompleted
        result = level_manager.mark_course_completion(user_id, course_id, False)
        print(f"   Mark as incomplete result: {result}")
        
        # Check updated points
        updated_user = conn.execute("SELECT points FROM users WHERE id = ?", (user_id,)).fetchone()
        print(f"   Points after unmarking: {updated_user['points']}")
        
        # Mark as completed again
        result = level_manager.mark_course_completion(user_id, course_id, True)
        print(f"   Mark as complete result: {result}")
        
        # Check updated points
        updated_user = conn.execute("SELECT points FROM users WHERE id = ?", (user_id,)).fetchone()
        print(f"   Points after remarking: {updated_user['points']}")
    
    # Test 4: Check level progression with more points
    print("\n🧪 TEST 4: Test Level Progression")
    print("-" * 50)
    
    # Manually add enough points to trigger level up
    current_points = conn.execute("SELECT points FROM users WHERE id = ?", (user_id,)).fetchone()['points']
    
    # Simulate adding more points by updating a course's point value temporarily
    conn.execute("UPDATE courses SET points = 200 WHERE title = 'GitHub Copilot: Code Faster with AI'")
    conn.commit()
    
    # Update user points from courses (should recalculate)
    new_level, total_points, level_points = level_manager.update_user_points_from_courses(user_id)
    
    print(f"   After increasing course points:")
    print(f"   New Level: {new_level}")
    print(f"   Total Points: {total_points}")
    print(f"   Level Points: {level_points}")
    
    # Restore original course points
    conn.execute("UPDATE courses SET points = 60 WHERE title = 'GitHub Copilot: Code Faster with AI'")
    conn.commit()
    
    # Restore original user points
    level_manager.update_user_points_from_courses(user_id)
    
    # Test 5: Show final level info
    print("\n🧪 TEST 5: Final Level Information")
    print("-" * 50)
    
    level_info = level_manager.get_user_level_info(user_id)
    
    for key, value in level_info.items():
        print(f"   {key}: {value}")
    
    # Test 6: Show recent points log
    print("\n🧪 TEST 6: Recent Points Activity")
    print("-" * 50)
    
    points_log = level_manager.get_user_points_log(user_id, limit=10)
    
    for log in points_log:
        action_type = log['action']
        change = f" ({log['points_change']:+d})" if log['points_change'] != 0 else ""
        course = f" - {log['course_title']}" if log['course_title'] else ""
        reason = f" - {log['reason']}" if log['reason'] and not log['course_title'] else ""
        
        print(f"   {log['created_at']}: {action_type}{change}{course}{reason}")
    
    conn.close()
    
    print("\n" + "="*70)
    print("✅ PROFILE UPDATE TESTS COMPLETED")
    print("="*70)

if __name__ == "__main__":
    test_profile_updates()
