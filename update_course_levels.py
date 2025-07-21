#!/usr/bin/env python3
"""
Update course levels based on points:
- 0-150 points: Beginner
- 151-250 points: Intermediate  
- 251+ points: Advanced
"""

import sqlite3
import os

def update_course_levels():
    """Update course levels based on points"""
    print("🔄 Updating Course Levels Based on Points")
    print("=" * 50)
    
    # Connect to database
    db_path = os.path.join(os.path.dirname(__file__), 'ai_learning.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get current course distribution
        print("📊 Current Course Level Distribution:")
        cursor.execute("SELECT level, COUNT(*) FROM courses GROUP BY level ORDER BY level")
        current_levels = cursor.fetchall()
        for level, count in current_levels:
            print(f"   {level}: {count} courses")
        
        print(f"\n📊 Current Points Distribution:")
        cursor.execute("SELECT points, COUNT(*) FROM courses GROUP BY points ORDER BY points")
        points_dist = cursor.fetchall()
        beginner_count = 0
        intermediate_count = 0
        advanced_count = 0
        
        for points, count in points_dist:
            if points is None:
                points = 0
            if points < 150:
                beginner_count += count
            elif points < 250:
                intermediate_count += count
            else:
                advanced_count += count
        
        print(f"   0-149 points: {beginner_count} courses (will be Beginner)")
        print(f"   150-249 points: {intermediate_count} courses (will be Intermediate)")
        print(f"   250+ points: {advanced_count} courses (will be Advanced)")
        
        # Update levels based on points
        print(f"\n🔄 Updating course levels...")
        
        # Beginner: 0-149 points
        cursor.execute("UPDATE courses SET level = 'Beginner' WHERE points < 150 OR points IS NULL")
        beginner_updated = cursor.rowcount
        
        # Intermediate: 150-249 points  
        cursor.execute("UPDATE courses SET level = 'Intermediate' WHERE points >= 150 AND points < 250")
        intermediate_updated = cursor.rowcount
        
        # Advanced: 250+ points
        cursor.execute("UPDATE courses SET level = 'Advanced' WHERE points >= 250")
        advanced_updated = cursor.rowcount
        
        # Convert any remaining old levels to the new system
        cursor.execute("UPDATE courses SET level = 'Beginner' WHERE level IN ('Learner', 'learner')")
        learner_converted = cursor.rowcount
        
        cursor.execute("UPDATE courses SET level = 'Advanced' WHERE level IN ('Expert', 'expert')")
        expert_converted = cursor.rowcount
        
        # Commit changes
        conn.commit()
        
        print(f"\n✅ Updates Complete:")
        print(f"   Beginner: {beginner_updated} courses updated")
        print(f"   Intermediate: {intermediate_updated} courses updated")
        print(f"   Advanced: {advanced_updated} courses updated")
        if learner_converted > 0:
            print(f"   Learner → Beginner: {learner_converted} courses converted")
        if expert_converted > 0:
            print(f"   Expert → Advanced: {expert_converted} courses converted")
        
        # Show final distribution
        print(f"\n📊 Final Course Level Distribution:")
        cursor.execute("SELECT level, COUNT(*) FROM courses GROUP BY level ORDER BY level")
        final_levels = cursor.fetchall()
        for level, count in final_levels:
            print(f"   {level}: {count} courses")
            
    except Exception as e:
        print(f"❌ Error updating course levels: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_course_levels()
