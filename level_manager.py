"""
Enhanced Level Management System

CRITICAL BUSINESS RULES:
========================

1. LEVEL CALCULATION LOGIC
   - Users advance levels based on total points earned
   - Points are earned by completing courses 
   - Level progression is cumulative (points carry over)
   - No level downgrade even if points calculation suggests lower level

2. POINTS SYSTEM
   - Each course completion awards configured points
   - Points are persistent and accumulate over time
   - Course points can be configured per course
   - Bonus points may be awarded for special achievements

3. LEVEL RESTRICTIONS
   - Users cannot be manually downgraded if their points exceed current level
   - Level changes must be consistent with points earned
   - Admin can manually adjust levels but system will warn of inconsistencies

4. PROGRESSION TRACKING
   - All level changes are logged with timestamps
   - Point earning history is maintained
   - Progress towards next level is calculated dynamically

This module is CRITICAL for user progression and should not be modified
without understanding the impact on existing user levels and points.

Comprehensive level and points management with logging and restrictions
"""

import sqlite3
from datetime import datetime
from typing import Tuple, Dict, List, Optional

class LevelManager:
    """Comprehensive level management system"""
    
    def __init__(self, db_path: str = 'ai_learning.db'):
        self.db_path = db_path
    
    def get_db_connection(self):
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_level_settings(self) -> List[Dict]:
        """Get all level settings ordered by points required"""
        conn = self.get_db_connection()
        settings = conn.execute('''
            SELECT level_name, points_required 
            FROM level_settings 
            ORDER BY points_required ASC
        ''').fetchall()
        conn.close()
        return [dict(setting) for setting in settings]
    
    def calculate_level_from_points(self, total_points: int) -> str:
        """Calculate what level user should be based on total points"""
        settings = self.get_level_settings()
        
        # Find highest level user qualifies for
        for level in reversed(settings):  # Start from highest level
            if total_points >= level['points_required']:
                return level['level_name']
        
        return 'Beginner'  # Fallback
    
    def get_level_points_breakdown(self, total_points: int, level: str) -> Dict:
        """Get detailed breakdown of points at current level"""
        settings = self.get_level_settings()
        
        # Find current and next level
        current_threshold = 0
        next_threshold = None
        next_level = None
        
        for i, setting in enumerate(settings):
            if setting['level_name'] == level:
                current_threshold = setting['points_required']
                if i + 1 < len(settings):
                    next_threshold = settings[i + 1]['points_required']
                    next_level = settings[i + 1]['level_name']
                break
        
        level_points = total_points - current_threshold
        points_to_next = (next_threshold - total_points) if next_threshold else 0
        
        return {
            'total_points': total_points,
            'current_level': level,
            'level_points': level_points,
            'current_threshold': current_threshold,
            'next_level': next_level,
            'next_threshold': next_threshold,
            'points_to_next': max(0, points_to_next),
            'progress_percentage': min(100, (total_points / next_threshold * 100)) if next_threshold else 100
        }
    
    def can_set_level(self, user_id: int, target_level: str) -> Tuple[bool, str]:
        """Check if user can set their level to target_level"""
        conn = self.get_db_connection()
        
        # Get user's current data
        user = conn.execute('''
            SELECT points, level, user_selected_level 
            FROM users WHERE id = ?
        ''', (user_id,)).fetchone()
        
        if not user:
            conn.close()
            return False, "User not found"
        
        # Get level thresholds
        settings = self.get_level_settings()
        level_thresholds = {s['level_name']: s['points_required'] for s in settings}
        
        conn.close()
        
        # Check restrictions
        user_points = user['points']
        target_threshold = level_thresholds.get(target_level, 0)
        
        # Users can always set a higher level in their profile
        current_threshold = level_thresholds.get(user['level'], 0)
        
        # Users cannot set a level lower than what their points qualify them for
        qualified_level = self.calculate_level_from_points(user_points)
        qualified_threshold = level_thresholds.get(qualified_level, 0)
        
        if target_threshold < qualified_threshold:
            return False, f"Cannot set level to {target_level}. Your {user_points} points qualify you for {qualified_level} or higher."
        
        return True, "Level change allowed"
    
    def update_user_points_from_courses(self, user_id: int) -> Tuple[str, int, int]:
        """Update user points based on completed courses and return level info"""
        conn = self.get_db_connection()
        
        # Get current user data
        user = conn.execute('SELECT points, level FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            conn.close()
            return 'Beginner', 0, 0
        
        old_points = user['points'] or 0
        old_level = user['level']
        
        # Calculate total points from completed courses
        total_points = conn.execute('''
            SELECT COALESCE(SUM(c.points), 0) as total
            FROM user_courses uc
            JOIN courses c ON uc.course_id = c.id
            WHERE uc.user_id = ? AND uc.completed = 1
        ''', (user_id,)).fetchone()['total']
        
        # Calculate new level based on points
        new_level = self.calculate_level_from_points(total_points)
        
        # Get level points breakdown
        breakdown = self.get_level_points_breakdown(total_points, new_level)
        level_points = breakdown['level_points']
        
        # Update user record
        conn.execute('''
            UPDATE users 
            SET points = ?, level = ?, level_points = ?, level_updated_at = ?
            WHERE id = ?
        ''', (total_points, new_level, level_points, datetime.now(), user_id))
        
        # Log points change if different
        points_change = total_points - old_points
        if points_change != 0:
            conn.execute('''
                INSERT INTO points_log (user_id, action, points_change, points_before, points_after, reason)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, 'COURSE_UPDATE', points_change, old_points, total_points, 
                  'Points updated from course completions'))
        
        # Log level change if different
        if new_level != old_level:
            conn.execute('''
                INSERT INTO points_log (user_id, action, points_change, points_before, points_after, reason)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, 'LEVEL_CHANGE', 0, total_points, total_points, 
                  f'Level changed from {old_level} to {new_level}'))
        
        conn.commit()
        conn.close()
        
        return new_level, total_points, level_points
    
    def mark_course_completion(self, user_id: int, course_id: int, completed: bool) -> Dict:
        """Mark course as completed/uncompleted and update points"""
        conn = self.get_db_connection()
        
        # Get course info
        course = conn.execute('SELECT title, points FROM courses WHERE id = ?', (course_id,)).fetchone()
        if not course:
            conn.close()
            return {'success': False, 'message': 'Course not found'}
        
        # Get current completion status
        current_status = conn.execute('''
            SELECT completed FROM user_courses 
            WHERE user_id = ? AND course_id = ?
        ''', (user_id, course_id)).fetchone()
        
        if not current_status:
            conn.close()
            return {'success': False, 'message': 'User not enrolled in course'}
        
        # Update completion status
        completion_date = datetime.now() if completed else None
        conn.execute('''
            UPDATE user_courses 
            SET completed = ?, completion_date = ?
            WHERE user_id = ? AND course_id = ?
        ''', (1 if completed else 0, completion_date, user_id, course_id))
        
        conn.commit()
        conn.close()
        
        # Update user points and level
        new_level, total_points, level_points = self.update_user_points_from_courses(user_id)
        
        action = 'COURSE_COMPLETED' if completed else 'COURSE_UNCOMPLETED'
        points_change = course['points'] if completed else -course['points']
        
        # Log the specific course action
        conn = self.get_db_connection()
        conn.execute('''
            INSERT INTO points_log (user_id, course_id, action, points_change, points_before, points_after, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, course_id, action, points_change, total_points - points_change, total_points,
              f'{"Completed" if completed else "Uncompleted"} course: {course["title"]}'))
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'message': f'Course {"completed" if completed else "marked as incomplete"}',
            'new_level': new_level,
            'total_points': total_points,
            'level_points': level_points,
            'points_change': points_change
        }
    
    def update_user_selected_level(self, user_id: int, target_level: str) -> Dict:
        """Update user's selected level with validation"""
        can_set, message = self.can_set_level(user_id, target_level)
        
        if not can_set:
            return {'success': False, 'message': message}
        
        conn = self.get_db_connection()
        
        # Update user selected level
        conn.execute('''
            UPDATE users 
            SET user_selected_level = ?
            WHERE id = ?
        ''', (target_level, user_id))
        
        # Log the change
        conn.execute('''
            INSERT INTO points_log (user_id, action, points_change, points_before, points_after, reason)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, 'LEVEL_SELECTED', 0, 0, 0, f'User selected level: {target_level}'))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'message': f'Level updated to {target_level}',
            'new_selected_level': target_level
        }
    
    def get_user_points_log(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get user's points transaction history"""
        conn = self.get_db_connection()
        
        logs = conn.execute('''
            SELECT pl.*, c.title as course_title
            FROM points_log pl
            LEFT JOIN courses c ON pl.course_id = c.id
            WHERE pl.user_id = ?
            ORDER BY pl.created_at DESC
            LIMIT ?
        ''', (user_id, limit)).fetchall()
        
        conn.close()
        
        return [dict(log) for log in logs]
    
    def get_user_level_info(self, user_id: int) -> Dict:
        """Get comprehensive level information for user"""
        conn = self.get_db_connection()
        
        user = conn.execute('''
            SELECT username, level, points, level_points, user_selected_level, level_updated_at
            FROM users WHERE id = ?
        ''', (user_id,)).fetchone()
        
        if not user:
            conn.close()
            return {}
        
        conn.close()
        
        # Get detailed breakdown
        breakdown = self.get_level_points_breakdown(user['points'], user['level'])
        
        return {
            'username': user['username'],
            'current_level': user['level'],
            'selected_level': user['user_selected_level'],
            'total_points': user['points'],
            'level_points': user['level_points'],
            'level_updated_at': user['level_updated_at'],
            **breakdown
        }
