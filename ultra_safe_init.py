#!/usr/bin/env python3
"""
EMERGENCY PATCH: Ultra-safe database initialization
This replaces ALL dangerous init_db() calls with truly safe logic
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def ultra_safe_init_db():
    """
    ULTRA SAFE: Initialize database without EVER calling init_db()
    Creates tables only if they don't exist, preserves ALL existing data
    """
    logger.info("🛡️ ULTRA_SAFE_INIT_DB: Starting completely safe database check...")
    
    try:
        # Connect or create database
        conn = sqlite3.connect('ai_learning.db')
        conn.row_factory = sqlite3.Row
        
        # Create tables ONLY if they don't exist (preserves all data)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                level TEXT DEFAULT 'Beginner',
                points INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                user_selected_level TEXT,
                login_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                skill_level TEXT NOT NULL,
                category TEXT,
                duration INTEGER,
                url TEXT,
                provider TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS learning_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                tags TEXT,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                custom_date DATE,
                is_global BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                completed BOOLEAN DEFAULT 0,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (course_id) REFERENCES courses (id)
            )
        ''')
        
        conn.commit()
        
        # Check existing data
        user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if user_count > 0:
            logger.info(f"✅ ULTRA_SAFE_INIT_DB: Found {user_count} existing users - ALL DATA PRESERVED")
            users = conn.execute("SELECT username FROM users").fetchall()
            usernames = [user[0] for user in users]
            logger.info(f"✅ ULTRA_SAFE_INIT_DB: Existing users: {usernames}")
        else:
            logger.info("📝 ULTRA_SAFE_INIT_DB: No existing users found - database ready for first use")
        
        conn.close()
        logger.info("🎯 ULTRA_SAFE_INIT_DB: Complete - database ready with zero data loss risk")
        return True
        
    except Exception as e:
        logger.error(f"❌ ULTRA_SAFE_INIT_DB: Error: {e}")
        return False

if __name__ == "__main__":
    # Test the ultra-safe initialization
    print("Testing ultra-safe database initialization...")
    success = ultra_safe_init_db()
    if success:
        print("✅ Ultra-safe initialization successful!")
    else:
        print("❌ Ultra-safe initialization failed!")
