#!/usr/bin/env python3
"""
Test Enhanced Security Guard - Verify Authorization Requirements
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from security_guard import SecurityGuard, SecurityGuardError

def test_authorization_requirements():
    """Test that authorization is required for destructive operations"""
    
    print("🧪 Testing Enhanced Security Guard Authorization Requirements")
    print("=" * 60)
    
    # Test operations requiring authorization
    test_cases = [
        {
            'operation': 'user_delete',
            'username': 'bharath',
            'should_block': True,
            'reason': 'User deletion requires explicit authorization'
        },
        {
            'operation': 'database_cleanup', 
            'username': None,
            'should_block': True,
            'reason': 'Database cleanup requires explicit authorization'
        },
        {
            'operation': 'password_reset',
            'username': 'admin',
            'should_block': False,
            'reason': 'Password reset allowed for test users'
        }
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        operation = test_case['operation']
        username = test_case['username']
        should_block = test_case['should_block']
        reason = test_case['reason']
        
        print(f"\n{i}. Testing {operation} for user '{username}'")
        print(f"   Expected: {'BLOCKED' if should_block else 'ALLOWED'} - {reason}")
        
        try:
            # Test without explicit authorization
            SecurityGuard.validate_operation(
                operation=operation,
                username=username,
                explicit_authorization=False
            )
            
            if should_block:
                print(f"   ❌ FAIL: Operation was allowed but should have been blocked")
            else:
                print(f"   ✅ PASS: Operation correctly allowed")
                passed += 1
                
        except SecurityGuardError as e:
            if should_block:
                print(f"   ✅ PASS: Operation correctly blocked - {str(e)}")
                passed += 1
            else:
                print(f"   ❌ FAIL: Operation was blocked but should have been allowed - {str(e)}")
        
        except Exception as e:
            print(f"   ❌ ERROR: Unexpected error - {str(e)}")
    
    print(f"\n" + "=" * 60)
    print(f"🏆 AUTHORIZATION TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All authorization requirements working correctly!")
        return True
    else:
        print("❌ Some authorization tests failed!")
        return False

def test_explicit_authorization_override():
    """Test that explicit authorization allows blocked operations"""
    
    print("\n🔓 Testing Explicit Authorization Override")
    print("=" * 60)
    
    try:
        # This should normally be blocked
        SecurityGuard.validate_operation(
            operation='user_delete',
            username='bharath',
            explicit_authorization=True  # Override with explicit auth
        )
        print("✅ PASS: Explicit authorization correctly overrides blocking")
        return True
        
    except SecurityGuardError as e:
        print(f"❌ FAIL: Explicit authorization did not override - {str(e)}")
        return False
    except Exception as e:
        print(f"❌ ERROR: Unexpected error - {str(e)}")
        return False

if __name__ == "__main__":
    print("🛡️  Enhanced Security Guard Authorization Test Suite")
    print("=" * 60)
    
    # Set development environment for testing
    os.environ['FLASK_ENV'] = 'development'
    
    success1 = test_authorization_requirements()
    success2 = test_explicit_authorization_override()
    
    print(f"\n" + "=" * 60)
    if success1 and success2:
        print("🎉 ALL ENHANCED SECURITY TESTS PASSED!")
        print("🔒 Authorization requirements are working correctly")
    else:
        print("⚠️  Some enhanced security tests failed")
        sys.exit(1)
