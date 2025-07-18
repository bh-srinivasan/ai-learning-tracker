#!/usr/bin/env python3
"""
Auto Startup Initializer
========================

This script runs automatically when the app starts and ensures admin user exists.
Will be called from app.py during startup.
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection"""
    try:
        conn = sqlite3.connect('ai_learning.db')
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def ensure_admin_user_exists():
    """Ensure admin user exists - runs automatically on app startup"""
    
    logger.info("🔍 Checking if admin user exists...")
    
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("❌ Could not connect to database")
            return False
        
        cursor = conn.cursor()
        
        # Check if admin user exists
        cursor.execute("SELECT id, username FROM users WHERE username = 'admin'")
        admin_user = cursor.fetchone()
        
        if admin_user:
            logger.info(f"✅ Admin user already exists (ID: {admin_user['id']})")
            conn.close()
            return True
        
        # Admin user doesn't exist - create it
        logger.info("🚀 Creating admin user...")
        
        admin_password = os.environ.get('ADMIN_PASSWORD', 'YourSecureAdminPassword1223!')
        password_hash = generate_password_hash(admin_password)
        
        cursor.execute("""
            INSERT INTO users (
                username, password_hash, level, points, status,
                user_selected_level, login_count, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'admin', password_hash, 'Advanced', 100, 'active',
            'Advanced', 0, datetime.now().isoformat()
        ))
        
        admin_id = cursor.lastrowid
        
        # Also create demo user if it doesn't exist
        cursor.execute("SELECT id FROM users WHERE username = 'demo'")
        if not cursor.fetchone():
            demo_password = os.environ.get('DEMO_PASSWORD', 'demo123')
            demo_hash = generate_password_hash(demo_password)
            
            cursor.execute("""
                INSERT INTO users (
                    username, password_hash, level, points, status,
                    user_selected_level, login_count, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'demo', demo_hash, 'Beginner', 0, 'active',
                'Beginner', 0, datetime.now().isoformat()
            ))
            
            logger.info("✅ Demo user created")
        
        conn.commit()
        conn.close()
        
        logger.info(f"🎉 Admin user created successfully! (ID: {admin_id})")
        logger.info("✅ Application is ready for login")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating admin user: {e}")
        return False

def startup_initialization():
    """Main startup initialization function"""
    
    logger.info("=" * 50)
    logger.info("🚀 AI Learning Tracker - Startup Initialization")
    logger.info("=" * 50)
    
    # Ensure admin user exists
    success = ensure_admin_user_exists()
    
    if success:
        logger.info("✅ Startup initialization completed successfully")
    else:
        logger.warning("⚠️ Startup initialization had issues")
    
    logger.info("🔗 Application ready at: https://ai-learning-tracker-bharath.azurewebsites.net/")
    logger.info("=" * 50)
    
    return success

if __name__ == "__main__":
    startup_initialization()
