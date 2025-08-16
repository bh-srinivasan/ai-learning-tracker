#!/usr/bin/env python3
"""
Test script for safe_clean.py functionality
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from tools.safe_clean import FlaskAppLoader, RouteCrawler, StaticAnalyzer

def test_flask_app_loading():
    """Test Flask app loading functionality."""
    print("Testing Flask app loading...")
    
    app = FlaskAppLoader.load_app(repo_root)
    if app:
        print(f"✓ Flask app loaded successfully")
        print(f"  App name: {app.name}")
        print(f"  Testing mode: {app.config.get('TESTING')}")
        
        # Test route discovery
        crawler = RouteCrawler(app, repo_root)
        routes = crawler.get_safe_routes()
        print(f"  Safe GET routes found: {len(routes)}")
        
        if routes:
            print("  Sample routes:")
            for route in routes[:5]:
                print(f"    {route}")
        
        return True
    else:
        print("✗ Failed to load Flask app")
        return False

def test_static_analysis():
    """Test static analysis functionality."""
    print("\nTesting static analysis...")
    
    upload_dirs = StaticAnalyzer.find_upload_dirs(repo_root)
    print(f"✓ Upload directories found: {len(upload_dirs)}")
    
    for upload_dir in upload_dirs:
        print(f"  {upload_dir}")
    
    return True

def main():
    """Run all tests."""
    print("Safe Clean Tool Tests")
    print("=" * 40)
    
    success = True
    success &= test_flask_app_loading()
    success &= test_static_analysis()
    
    print("\n" + "=" * 40)
    if success:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed!")
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
