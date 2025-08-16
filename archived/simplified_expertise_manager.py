"""
Simplified Expertise Level System
Single, user-friendly expertise level based on both self-assessment and system progress
"""

import sqlite3
from datetime import datetime
from typing import Dict, Optional

class SimplifiedExpertiseManager:
    """Simplified expertise level management with combined assessment"""
    
    def __init__(self, db_path: str = 'ai_learning.db'):
        self.db_path = db_path
        
        # Define expertise levels (simplified to 3 levels)
        self.expertise_levels = {
            'Beginner': {
                'name': 'Beginner',
                'description': 'Starting your AI journey',
                'min_points': 0,
                'max_points': 299,
                'self_weight': 0.4,  # 40% self-assessment
                'system_weight': 0.6  # 60% system assessment
            },
            'Intermediate': {
                'name': 'Intermediate', 
                'description': 'Building solid AI knowledge',
                'min_points': 300,
                'max_points': 999,
                'self_weight': 0.3,  # 30% self-assessment
                'system_weight': 0.7  # 70% system assessment
            },
            'Advanced': {
                'name': 'Advanced',
                'description': 'Mastering AI concepts and applications',
                'min_points': 1000,
                'max_points': float('inf'),
                'self_weight': 0.2,  # 20% self-assessment
                'system_weight': 0.8  # 80% system assessment
            }
        }
    
    def get_db_connection(self):
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_system_level_from_points(self, total_points: int) -> str:
        """Get system-assessed level based on points"""
        for level_name, config in self.expertise_levels.items():
            if config['min_points'] <= total_points <= config['max_points']:
                return level_name
        return 'Beginner'
    
    def map_old_level_to_simplified(self, old_level: str) -> str:
        """Map old detailed levels to simplified 3-level system"""
        level_mapping = {
            'Beginner': 'Beginner',
            'Learner': 'Beginner', 
            'Explorer': 'Intermediate',
            'Practitioner': 'Intermediate',
            'Intermediate': 'Intermediate',
            'Advanced': 'Advanced',
            'Specialist': 'Advanced',
            'Expert': 'Advanced',
            'Master': 'Advanced',
            'AI Expert': 'Advanced'
        }
        return level_mapping.get(old_level, 'Beginner')
    
    def calculate_combined_expertise_level(self, user_id: int) -> Dict:
        """Calculate combined expertise level based on self-assessment and system progress"""
        conn = self.get_db_connection()
        
        # Get user data
        user = conn.execute('''
            SELECT points, level, user_selected_level, username
            FROM users WHERE id = ?
        ''', (user_id,)).fetchone()
        
        if not user:
            conn.close()
            return {'level': 'Beginner', 'confidence': 'low', 'message': 'User not found'}
        
        # Get system level from points
        system_level = self.get_system_level_from_points(user['points'])
        
        # Map user selected level to simplified system
        user_level = self.map_old_level_to_simplified(user['user_selected_level'] or 'Beginner')
        
        # Calculate combined level using weighted approach
        combined_level = self._calculate_weighted_level(system_level, user_level, user['points'])
        
        # Generate user-friendly message
        message = self._generate_level_message(system_level, user_level, combined_level)
        
        # Calculate confidence based on agreement between assessments
        confidence = self._calculate_confidence(system_level, user_level)
        
        conn.close()
        
        return {
            'level': combined_level,
            'system_level': system_level,
            'self_level': user_level, 
            'confidence': confidence,
            'message': message,
            'description': self.expertise_levels[combined_level]['description'],
            'points': user['points']
        }
    
    def _calculate_weighted_level(self, system_level: str, user_level: str, points: int) -> str:
        """Calculate weighted combined level"""
        
        # Convert levels to numeric values for calculation
        level_values = {'Beginner': 1, 'Intermediate': 2, 'Advanced': 3}
        
        system_numeric = level_values[system_level]
        user_numeric = level_values[user_level]
        
        # Use points to determine which level config to use for weighting
        current_config = self.expertise_levels[system_level]
        
        # Calculate weighted average
        weighted_score = (
            system_numeric * current_config['system_weight'] + 
            user_numeric * current_config['self_weight']
        )
        
        # Round to nearest level
        if weighted_score <= 1.5:
            return 'Beginner'
        elif weighted_score <= 2.5:
            return 'Intermediate'
        else:
            return 'Advanced'
    
    def _calculate_confidence(self, system_level: str, user_level: str) -> str:
        """Calculate confidence level based on agreement"""
        if system_level == user_level:
            return 'high'
        
        level_order = ['Beginner', 'Intermediate', 'Advanced']
        system_idx = level_order.index(system_level)
        user_idx = level_order.index(user_level)
        
        if abs(system_idx - user_idx) == 1:
            return 'medium'
        else:
            return 'low'
    
    def _generate_level_message(self, system_level: str, user_level: str, combined_level: str) -> str:
        """Generate encouraging message based on level comparison"""
        
        level_order = ['Beginner', 'Intermediate', 'Advanced']
        system_idx = level_order.index(system_level)
        user_idx = level_order.index(user_level)
        
        if system_idx > user_idx:
            return "You're doing better than you think! Keep going."
        elif system_idx < user_idx:
            return "Keep learning to match your ambitious goals!"
        else:
            return "Your self-assessment aligns well with your progress!"
    
    def get_simplified_user_profile(self, user_id: int) -> Dict:
        """Get simplified user profile with combined expertise level"""
        conn = self.get_db_connection()
        
        # Get basic user info
        user = conn.execute('''
            SELECT id, username, points, created_at
            FROM users WHERE id = ?
        ''', (user_id,)).fetchone()
        
        if not user:
            conn.close()
            return None
        
        # Get combined expertise level
        expertise_info = self.calculate_combined_expertise_level(user_id)
        
        # Get learning entries count (for progress tracking)
        learning_count = conn.execute('''
            SELECT COUNT(*) as count FROM learning_entries WHERE user_id = ?
        ''', (user_id,)).fetchone()['count']
        
        # Get recent learning streak (days with learning entries in last 30 days)
        recent_activity = conn.execute('''
            SELECT COUNT(DISTINCT DATE(date_added)) as active_days
            FROM learning_entries 
            WHERE user_id = ? AND date_added >= date('now', '-30 days')
        ''', (user_id,)).fetchone()['active_days']
        
        conn.close()
        
        return {
            'user': dict(user),
            'expertise': expertise_info,
            'stats': {
                'total_learnings': learning_count,
                'monthly_active_days': recent_activity,
                'points': user['points']
            }
        }
    
    def update_user_self_assessment(self, user_id: int, new_level: str) -> Dict:
        """Update user's self-assessment level"""
        if new_level not in ['Beginner', 'Intermediate', 'Advanced']:
            return {'success': False, 'message': 'Invalid level'}
        
        conn = self.get_db_connection()
        
        # Map simplified level back to old system for compatibility
        level_mapping = {
            'Beginner': 'Beginner',
            'Intermediate': 'Intermediate', 
            'Advanced': 'Expert'
        }
        
        old_system_level = level_mapping[new_level]
        
        conn.execute('''
            UPDATE users 
            SET user_selected_level = ?
            WHERE id = ?
        ''', (old_system_level, user_id))
        
        conn.commit()
        conn.close()
        
        # Return updated combined level
        return self.calculate_combined_expertise_level(user_id)


def migrate_to_simplified_system():
    """Migration helper to update existing users to simplified system"""
    manager = SimplifiedExpertiseManager()
    conn = manager.get_db_connection()
    
    # Get all users
    users = conn.execute('SELECT id, username FROM users').fetchall()
    
    migration_results = []
    
    for user in users:
        # Calculate new combined level
        result = manager.calculate_combined_expertise_level(user['id'])
        migration_results.append({
            'user_id': user['id'],
            'username': user['username'],
            'new_level': result['level'],
            'message': result['message']
        })
    
    conn.close()
    return migration_results


if __name__ == "__main__":
    # Test the simplified system
    manager = SimplifiedExpertiseManager()
    
    # Test with user ID 1
    profile = manager.get_simplified_user_profile(1)
    if profile:
        print("Simplified User Profile:")
        print(f"Username: {profile['user']['username']}")
        print(f"Expertise Level: {profile['expertise']['level']}")
        print(f"Description: {profile['expertise']['description']}")
        print(f"Message: {profile['expertise']['message']}")
        print(f"Confidence: {profile['expertise']['confidence']}")
        print(f"Points: {profile['stats']['points']}")
        print(f"Total Learnings: {profile['stats']['total_learnings']}")
        print(f"Monthly Active Days: {profile['stats']['monthly_active_days']}")
