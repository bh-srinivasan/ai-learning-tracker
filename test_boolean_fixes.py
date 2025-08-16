#!/usr/bin/env python3
"""
Test script to validate Azure SQL boolean compatibility fixes
"""

import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_boolean_fixes():
    print("=== TESTING BOOLEAN COMPATIBILITY FIXES ===\n")
    
    try:
        from app import get_db_connection, is_azure_sql, get_session_table
        print("✅ Successfully imported app functions")
        
        # Test database connection
        conn = get_db_connection()
        session_table = get_session_table()
        
        print(f"✅ Database connection: {'Azure SQL' if is_azure_sql() else 'Local SQLite'}")
        print(f"✅ Session table: {session_table}")
        
        # Test the fixed query structure
        test_query = f"""
            SELECT s.*, u.username, u.level, u.points, u.is_admin 
            FROM {session_table} s 
            JOIN users u ON s.user_id = u.id 
            WHERE s.session_token = ? AND s.is_active = 1
        """
        
        # Test with dummy data
        result = conn.execute(test_query, ("dummy_token",)).fetchone()
        print("✅ Fixed query structure validates successfully")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_boolean_fixes()
