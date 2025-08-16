#!/usr/bin/env python3
"""
Workspace Problem Resolution Test Script
Tests the 7 problems that were identified and fixed
"""

import sys
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test 1: Verify all imports work correctly"""
    try:
        logger.info("🧪 Test 1: Testing imports...")
        
        # Test database environment manager
        from database_environment_manager import DatabaseEnvironmentManager
        logger.info("  ✅ DatabaseEnvironmentManager import successful")
        
        # Test upload reports manager
        from upload_reports_manager import UploadReportsManager
        logger.info("  ✅ UploadReportsManager import successful")
        
        # Test admin reports routes
        from admin_reports_routes import admin_reports_bp
        logger.info("  ✅ admin_reports_routes import successful")
        
        # Test enhanced excel upload
        from enhanced_excel_upload import ExcelUploadManager
        logger.info("  ✅ ExcelUploadManager import successful")
        
        return True
    except Exception as e:
        logger.error(f"  ❌ Import test failed: {e}")
        return False

def test_database_manager_methods():
    """Test 2: Verify DatabaseEnvironmentManager has required methods"""
    try:
        logger.info("🧪 Test 2: Testing DatabaseEnvironmentManager methods...")
        
        from database_environment_manager import DatabaseEnvironmentManager
        db_manager = DatabaseEnvironmentManager()
        
        # Check for required methods
        required_methods = ['is_azure_sql', 'connect', 'disconnect', 'connect_to_database', 'close_connection']
        for method in required_methods:
            if hasattr(db_manager, method):
                logger.info(f"  ✅ Method {method} exists")
            else:
                logger.error(f"  ❌ Method {method} missing")
                return False
        
        return True
    except Exception as e:
        logger.error(f"  ❌ Database manager test failed: {e}")
        return False

def test_schema_consistency():
    """Test 3: Verify schema is consistent between files"""
    try:
        logger.info("🧪 Test 3: Testing schema consistency...")
        
        from database_environment_manager import DatabaseSchemaManager
        schema = DatabaseSchemaManager.SCHEMA_DEFINITION
        
        # Check if upload reports tables exist
        if 'excel_upload_reports' in schema:
            logger.info("  ✅ excel_upload_reports table defined")
            
            # Check if it has the expected columns
            columns = schema['excel_upload_reports']['columns']
            expected_cols = ['user_id', 'filename', 'upload_timestamp', 'total_rows', 'success_count']
            
            column_text = ' '.join(columns)
            for col in expected_cols:
                if col in column_text:
                    logger.info(f"  ✅ Column {col} found")
                else:
                    logger.error(f"  ❌ Column {col} missing")
                    return False
        else:
            logger.error("  ❌ excel_upload_reports table not defined")
            return False
        
        if 'excel_upload_row_details' in schema:
            logger.info("  ✅ excel_upload_row_details table defined")
        else:
            logger.error("  ❌ excel_upload_row_details table not defined")
            return False
        
        return True
    except Exception as e:
        logger.error(f"  ❌ Schema consistency test failed: {e}")
        return False

def test_template_syntax():
    """Test 4: Basic template syntax check"""
    try:
        logger.info("🧪 Test 4: Testing template syntax...")
        
        # Check if template files exist
        template_files = [
            'templates/admin/upload_reports.html',
            'templates/admin/upload_report_details.html',
            'templates/admin/upload_report_table.html'
        ]
        
        for template in template_files:
            if os.path.exists(template):
                logger.info(f"  ✅ Template {template} exists")
                
                # Basic syntax check - look for obvious issues
                with open(template, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Check for unclosed blocks
                    if content.count('{% block') == content.count('{% endblock %}'):
                        logger.info(f"  ✅ Template {template} has matching blocks")
                    else:
                        logger.error(f"  ❌ Template {template} has unmatched blocks")
                        return False
            else:
                logger.error(f"  ❌ Template {template} missing")
                return False
        
        return True
    except Exception as e:
        logger.error(f"  ❌ Template syntax test failed: {e}")
        return False

def test_route_consistency():
    """Test 5: Verify route names are consistent"""
    try:
        logger.info("🧪 Test 5: Testing route consistency...")
        
        # Check admin_reports_routes for correct route references
        with open('admin_reports_routes.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Should NOT contain old route names
            problematic_routes = ['auth.login', 'admin.courses']
            for route in problematic_routes:
                if f"url_for('{route}')" in content:
                    logger.error(f"  ❌ Found old route reference: {route}")
                    return False
            
            # Should contain updated route names
            good_routes = ['auth.auth_login', 'admin_bp.courses']
            for route in good_routes:
                if f"url_for('{route}')" in content:
                    logger.info(f"  ✅ Found correct route reference: {route}")
                else:
                    logger.warning(f"  ⚠️ Route reference {route} not found (might be ok)")
        
        return True
    except Exception as e:
        logger.error(f"  ❌ Route consistency test failed: {e}")
        return False

def test_integration_points():
    """Test 6: Verify integration points are working"""
    try:
        logger.info("🧪 Test 6: Testing integration points...")
        
        # Check if app.py has the reports blueprint registered
        if os.path.exists('app.py'):
            with open('app.py', 'r', encoding='utf-8') as f:
                content = f.read()
                
                if 'from admin_reports_routes import admin_reports_bp' in content:
                    logger.info("  ✅ Admin reports blueprint imported in app.py")
                else:
                    logger.error("  ❌ Admin reports blueprint not imported in app.py")
                    return False
                
                if 'app.register_blueprint(admin_reports_bp)' in content:
                    logger.info("  ✅ Admin reports blueprint registered in app.py")
                else:
                    logger.error("  ❌ Admin reports blueprint not registered in app.py")
                    return False
        
        # Check if the courses template has the reports button
        courses_template = 'templates/admin/courses.html'
        if os.path.exists(courses_template):
            with open(courses_template, 'r', encoding='utf-8') as f:
                content = f.read()
                
                if 'admin_reports.upload_reports_list' in content:
                    logger.info("  ✅ Upload reports button added to courses template")
                else:
                    logger.error("  ❌ Upload reports button not found in courses template")
                    return False
        
        return True
    except Exception as e:
        logger.error(f"  ❌ Integration points test failed: {e}")
        return False

def test_file_completeness():
    """Test 7: Verify all required files exist"""
    try:
        logger.info("🧪 Test 7: Testing file completeness...")
        
        required_files = [
            'database_environment_manager.py',
            'upload_reports_manager.py',
            'admin_reports_routes.py',
            'enhanced_excel_upload.py',
            'scheduled_purge_reports.py',
            'integrate_upload_reports.py',
            'templates/admin/upload_reports.html',
            'templates/admin/upload_report_details.html',
            'templates/admin/upload_report_table.html',
            'UPLOAD_REPORTS_IMPLEMENTATION_COMPLETE.md'
        ]
        
        for file_path in required_files:
            if os.path.exists(file_path):
                logger.info(f"  ✅ Required file {file_path} exists")
            else:
                logger.error(f"  ❌ Required file {file_path} missing")
                return False
        
        return True
    except Exception as e:
        logger.error(f"  ❌ File completeness test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("🚀 Starting Workspace Problem Resolution Tests")
    logger.info("=" * 60)
    
    tests = [
        test_imports,
        test_database_manager_methods,
        test_schema_consistency,
        test_template_syntax,
        test_route_consistency,
        test_integration_points,
        test_file_completeness
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(tests, 1):
        result = test()
        if result:
            passed += 1
            logger.info(f"✅ Test {i} PASSED\n")
        else:
            failed += 1
            logger.error(f"❌ Test {i} FAILED\n")
    
    logger.info("=" * 60)
    logger.info(f"📊 TEST RESULTS: {passed} passed, {failed} failed")
    
    if failed == 0:
        logger.info("🎉 ALL TESTS PASSED - Workspace problems resolved!")
        return 0
    else:
        logger.error(f"⚠️ {failed} test(s) failed - Some problems remain")
        return 1

if __name__ == "__main__":
    sys.exit(main())
