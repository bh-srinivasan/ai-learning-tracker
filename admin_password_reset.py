#!/usr/bin/env python3
"""
Backend-Only Admin Password Reset Utility

This script provides a secure way to reset the admin password from the backend.
It validates password strength and securely hashes the password before storage.

Usage:
    python admin_password_reset.py "NewSecurePassword123!"

Security Features:
- Password strength validation
- Secure password hashing
- Audit logging
- No frontend exposure
"""

import sys
import sqlite3
import re
import secrets
from datetime import datetime
from werkzeug.security import generate_password_hash

def validate_password_strength(password):
    """
    Validate password meets security requirements
    
    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    
    Args:
        password (str): Password to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:,.<>?]', password):
        return False, "Password must contain at least one special character (!@#$%^&*)"
    
    return True, "Password meets security requirements"

def log_password_reset_event(admin_id, success, details=""):
    """
    Log the password reset event for audit purposes
    
    Args:
        admin_id (int): Admin user ID
        success (bool): Whether the reset was successful
        details (str): Additional details about the event
    """
    try:
        conn = sqlite3.connect('ai_learning.db')
        
        # Create security_logs table if it doesn't exist
        conn.execute('''
            CREATE TABLE IF NOT EXISTS security_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                description TEXT NOT NULL,
                ip_address TEXT,
                user_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN NOT NULL
            )
        ''')
        
        # Log the event
        event_type = "admin_password_reset_backend"
        description = f"Backend admin password reset attempt. {details}"
        
        conn.execute('''
            INSERT INTO security_logs (event_type, description, ip_address, user_id, success)
            VALUES (?, ?, ?, ?, ?)
        ''', (event_type, description, "backend_script", admin_id, success))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"⚠️  Warning: Could not log security event: {str(e)}")

def reset_admin_password(new_password):
    """
    Reset the admin password with security validation
    
    Args:
        new_password (str): The new password to set
        
    Returns:
        tuple: (success, message)
    """
    print("🔒 BACKEND ADMIN PASSWORD RESET")
    print("=" * 50)
    
    # Step 1: Validate password strength
    print("1. 🔍 Validating password strength...")
    is_valid, validation_message = validate_password_strength(new_password)
    
    if not is_valid:
        print(f"❌ Password validation failed: {validation_message}")
        log_password_reset_event(1, False, f"Password validation failed: {validation_message}")
        return False, validation_message
    
    print(f"✅ {validation_message}")
    
    # Step 2: Connect to database
    print("2. 🗄️  Connecting to database...")
    try:
        conn = sqlite3.connect('ai_learning.db')
        conn.row_factory = sqlite3.Row
    except Exception as e:
        error_msg = f"Database connection failed: {str(e)}"
        print(f"❌ {error_msg}")
        log_password_reset_event(1, False, error_msg)
        return False, error_msg
    
    try:
        # Step 3: Verify admin user exists
        print("3. 👤 Verifying admin user...")
        admin_user = conn.execute(
            'SELECT id, username FROM users WHERE username = ?',
            ('admin',)
        ).fetchone()
        
        if not admin_user:
            error_msg = "Admin user not found in database"
            print(f"❌ {error_msg}")
            log_password_reset_event(None, False, error_msg)
            return False, error_msg
        
        admin_id = admin_user['id']
        print(f"✅ Found admin user (ID: {admin_id})")
        
        # Step 4: Generate secure password hash
        print("4. 🔐 Generating secure password hash...")
        password_hash = generate_password_hash(new_password)
        print(f"✅ Password hash generated (length: {len(password_hash)} chars)")
        
        # Step 5: Update admin password
        print("5. 💾 Updating admin password in database...")
        cursor = conn.execute(
            'UPDATE users SET password_hash = ? WHERE username = ?',
            (password_hash, 'admin')
        )
        
        if cursor.rowcount != 1:
            error_msg = "Failed to update admin password in database"
            print(f"❌ {error_msg}")
            log_password_reset_event(admin_id, False, error_msg)
            return False, error_msg
        
        conn.commit()
        print("✅ Admin password successfully updated")
        
        # Step 6: Verify the update
        print("6. ✅ Verifying password update...")
        updated_user = conn.execute(
            'SELECT password_hash FROM users WHERE username = ?',
            ('admin',)
        ).fetchone()
        
        if updated_user and updated_user['password_hash'] == password_hash:
            print("✅ Password update verified")
            log_password_reset_event(admin_id, True, "Admin password successfully reset via backend script")
            return True, "Password reset successful"
        else:
            error_msg = "Password verification failed"
            print(f"❌ {error_msg}")
            log_password_reset_event(admin_id, False, error_msg)
            return False, error_msg
            
    except Exception as e:
        error_msg = f"Database operation failed: {str(e)}"
        print(f"❌ {error_msg}")
        log_password_reset_event(admin_id if 'admin_id' in locals() else None, False, error_msg)
        return False, error_msg
        
    finally:
        conn.close()

def generate_secure_password():
    """
    Generate a secure password that meets all requirements
    
    Returns:
        str: A secure password
    """
    # Character sets
    uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    lowercase = "abcdefghijklmnopqrstuvwxyz"
    digits = "0123456789"
    special = "!@#$%^&*"
    
    # Ensure at least one character from each required set
    password = [
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(digits),
        secrets.choice(special)
    ]
    
    # Fill the rest with random characters from all sets
    all_chars = uppercase + lowercase + digits + special
    for _ in range(8):  # Total length will be 12
        password.append(secrets.choice(all_chars))
    
    # Shuffle the password
    secrets.SystemRandom().shuffle(password)
    
    return ''.join(password)

def main():
    """Main function to handle command line execution"""
    
    if len(sys.argv) < 2:
        print("🔒 BACKEND ADMIN PASSWORD RESET UTILITY")
        print("=" * 50)
        print()
        print("Usage:")
        print("   python admin_password_reset.py \"YourNewPassword123!\"")
        print("   python admin_password_reset.py --generate")
        print()
        print("Password Requirements:")
        print("   • Minimum 8 characters")
        print("   • At least one uppercase letter (A-Z)")
        print("   • At least one lowercase letter (a-z)")
        print("   • At least one number (0-9)")
        print("   • At least one special character (!@#$%^&*)")
        print()
        print("Examples:")
        print("   python admin_password_reset.py \"SecureAdmin2024!\"")
        print("   python admin_password_reset.py \"MyStr0ng@Passw0rd\"")
        print("   python admin_password_reset.py --generate")
        print()
        sys.exit(1)
    
    # Handle password generation option
    if sys.argv[1] == "--generate":
        print("🎲 GENERATING SECURE PASSWORD")
        print("=" * 50)
        
        generated_password = generate_secure_password()
        print(f"Generated password: {generated_password}")
        print()
        
        # Ask if user wants to use this password
        confirm = input("Do you want to use this password? (y/N): ").strip().lower()
        if confirm in ['y', 'yes']:
            new_password = generated_password
        else:
            print("Password generation cancelled.")
            sys.exit(0)
    else:
        new_password = sys.argv[1]
    
    # Reset the password
    success, message = reset_admin_password(new_password)
    
    if success:
        print("\n" + "=" * 50)
        print("🎉 SUCCESS!")
        print("   Admin password has been reset successfully")
        print("   The new password is secure and meets all requirements")
        print("   You can now login with the new password")
        print("   Event has been logged for audit purposes")
        print("=" * 50)
        sys.exit(0)
    else:
        print("\n" + "=" * 50)
        print("❌ FAILED!")
        print(f"   {message}")
        print("   Please check the requirements and try again")
        print("=" * 50)
        sys.exit(1)

if __name__ == "__main__":
    main()
