#!/usr/bin/env python3
"""
Minimal admin fix for Azure deployment - replaces the admin index route with maximum error handling
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g, jsonify
from werkzeug.security import generate_password_hash
import sqlite3
import traceback

admin_bp = Blueprint('admin', __name__)

def get_db_connection():
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_current_user():
    """Get current user from g object (set by before_request handler)"""
    return getattr(g, 'user', None)

def is_admin():
    """Check if current user is admin"""
    user = get_current_user()
    return user and user['username'] == 'admin'

@admin_bp.route('/admin')
def index():
    """Admin dashboard with maximum error handling for Azure"""
    if not is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Initialize default values
    total_users = 0
    total_courses = 0
    total_global_learnings = 0
    recent_users = []
    
    try:
        conn = get_db_connection()
        
        # Get total users count (most basic query)
        try:
            result = conn.execute('SELECT COUNT(*) as count FROM users WHERE username != "admin"').fetchone()
            total_users = result['count'] if result else 0
        except Exception as e:
            print(f"Error getting total_users: {e}")
            total_users = 0
        
        # Get total courses count
        try:
            result = conn.execute('SELECT COUNT(*) as count FROM courses').fetchone()
            total_courses = result['count'] if result else 0
        except Exception as e:
            print(f"Error getting total_courses: {e}")
            total_courses = 0
        
        # Get total learning entries count
        try:
            result = conn.execute('SELECT COUNT(*) as count FROM learning_entries').fetchone()
            total_global_learnings = result['count'] if result else 0
        except Exception as e:
            print(f"Error getting total_global_learnings: {e}")
            total_global_learnings = 0
        
        # Get recent users - try the most basic query first
        try:
            recent_users = conn.execute('''
                SELECT username, created_at 
                FROM users 
                WHERE username != "admin"
                ORDER BY created_at DESC 
                LIMIT 5
            ''').fetchall()
            
            # Convert to list of dicts and add default values
            recent_users_list = []
            for user in recent_users:
                user_dict = {
                    'username': user['username'],
                    'level': 'Beginner',  # Default value
                    'points': 0,  # Default value
                    'created_at': user['created_at']
                }
                recent_users_list.append(user_dict)
            recent_users = recent_users_list
            
        except Exception as e:
            print(f"Error getting recent_users: {e}")
            recent_users = []
        
        conn.close()
        
    except Exception as e:
        print(f"Database connection error in admin index: {e}")
        print(f"Full traceback: {traceback.format_exc()}")
        # Use default values if database access fails completely
        pass
    
    return render_template('admin/index.html',
                         total_users=total_users,
                         total_courses=total_courses,
                         total_global_learnings=total_global_learnings,
                         recent_users=recent_users)

# Add debug route to test database connectivity
@admin_bp.route('/admin/debug')
def debug():
    """Debug route to test database connectivity"""
    if not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        conn = get_db_connection()
        
        # Test basic connectivity
        result = conn.execute('SELECT 1').fetchone()
        
        # Test table existence
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [t['name'] for t in tables]
        
        # Test users table
        users_count = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'database_connection': 'OK',
            'tables': table_names,
            'users_count': users_count
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500
