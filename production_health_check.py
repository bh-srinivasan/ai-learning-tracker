#!/usr/bin/env python3
"""
Production Health Check and Validation Script
This script performs thorough validation before declaring production issues resolved.
"""
import requests
import time
import sys
from urllib.parse import urljoin

class ProductionValidator:
    def __init__(self, base_url):
        self.base_url = base_url
        self.issues = []
        self.warnings = []
        
    def log_issue(self, severity, message):
        """Log production issues with severity levels"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        issue_msg = f"[{timestamp}] {severity}: {message}"
        
        if severity in ['CRITICAL', 'ERROR']:
            self.issues.append(issue_msg)
            print(f"❌ {issue_msg}")
        elif severity == 'WARNING':
            self.warnings.append(issue_msg)
            print(f"⚠️  {issue_msg}")
        else:
            print(f"ℹ️  {issue_msg}")
    
    def test_basic_connectivity(self):
        """Test if the application responds to HTTP requests"""
        try:
            print(f"\n🔍 Testing connectivity to {self.base_url}")
            response = requests.get(self.base_url, timeout=60)  # Increased timeout for Azure cold start
            
            if response.status_code == 200:
                self.log_issue("INFO", f"HTTP connectivity successful (Status: {response.status_code})")
                return True
            elif response.status_code >= 500:
                self.log_issue("CRITICAL", f"Server error (Status: {response.status_code})")
                return False
            elif response.status_code >= 400:
                self.log_issue("ERROR", f"Client error (Status: {response.status_code})")
                return False
            else:
                self.log_issue("WARNING", f"Unexpected status code: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            self.log_issue("CRITICAL", "Request timeout - application not responding")
            return False
        except requests.exceptions.ConnectionError:
            self.log_issue("CRITICAL", "Connection failed - application likely down")
            return False
        except Exception as e:
            self.log_issue("CRITICAL", f"Connectivity test failed: {str(e)}")
            return False
    
    def test_application_health(self):
        """Test specific application endpoints"""
        test_endpoints = [
            ('/', 'Main page'),
            ('/auth/login', 'Login page'),
        ]
        
        success_count = 0
        total_tests = len(test_endpoints)
        
        for endpoint, description in test_endpoints:
            try:
                url = urljoin(self.base_url, endpoint)
                response = requests.get(url, timeout=30)  # Increased timeout
                
                if response.status_code == 200:
                    self.log_issue("INFO", f"{description} accessible ({endpoint})")
                    success_count += 1
                else:
                    self.log_issue("ERROR", f"{description} returned status {response.status_code} ({endpoint})")
                    
            except Exception as e:
                self.log_issue("ERROR", f"{description} test failed: {str(e)}")
        
        success_rate = (success_count / total_tests) * 100
        if success_rate < 50:
            self.log_issue("CRITICAL", f"Application health critical: {success_rate:.1f}% endpoints responding")
            return False
        elif success_rate < 100:
            self.log_issue("WARNING", f"Application health degraded: {success_rate:.1f}% endpoints responding")
            return True
        else:
            self.log_issue("INFO", f"Application health good: {success_rate:.1f}% endpoints responding")
            return True
    
    def test_error_pages(self):
        """Check if we're getting error pages instead of the actual application"""
        try:
            response = requests.get(self.base_url, timeout=30)  # Increased timeout
            content = response.text.lower()
            
            error_indicators = [
                'application error',
                'internal server error', 
                'service unavailable',
                'bad gateway',
                'connection failed',
                'timeout',
                'the website is temporarily unable',
                'this site can\'t be reached'
            ]
            
            for indicator in error_indicators:
                if indicator in content:
                    self.log_issue("CRITICAL", f"Error page detected: Found '{indicator}' in response")
                    return False
            
            # Check for Azure-specific error pages
            if 'azurewebsites.net' in content and 'error' in content:
                self.log_issue("CRITICAL", "Possible Azure error page detected")
                return False
                
            self.log_issue("INFO", "No error page indicators found")
            return True
            
        except Exception as e:
            self.log_issue("ERROR", f"Error page check failed: {str(e)}")
            return False
    
    def validate_production_readiness(self):
        """Comprehensive validation before declaring production ready"""
        print("🚀 PRODUCTION READINESS VALIDATION")
        print("=" * 50)
        
        tests = [
            ("Basic Connectivity", self.test_basic_connectivity),
            ("Error Page Check", self.test_error_pages), 
            ("Application Health", self.test_application_health),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 Running: {test_name}")
            try:
                if test_func():
                    passed_tests += 1
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                print(f"💥 {test_name}: EXCEPTION - {str(e)}")
                self.log_issue("CRITICAL", f"{test_name} threw exception: {str(e)}")
        
        print(f"\n📊 VALIDATION SUMMARY")
        print("=" * 30)
        print(f"Tests passed: {passed_tests}/{total_tests}")
        print(f"Critical issues: {len([i for i in self.issues if 'CRITICAL' in i])}")
        print(f"Errors: {len([i for i in self.issues if 'ERROR' in i])}")
        print(f"Warnings: {len(self.warnings)}")
        
        if self.issues:
            print(f"\n🚨 PRODUCTION ISSUES DETECTED:")
            for issue in self.issues:
                print(f"  {issue}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  {warning}")
        
        # Determine overall status
        critical_issues = len([i for i in self.issues if 'CRITICAL' in i])
        error_issues = len([i for i in self.issues if 'ERROR' in i])
        
        if critical_issues > 0:
            print(f"\n🔴 PRODUCTION STATUS: CRITICAL FAILURE")
            print(f"❌ The application has {critical_issues} critical issue(s)")
            print(f"🚫 DO NOT DECLARE PRODUCTION RESOLVED")
            return False
        elif error_issues > 0:
            print(f"\n🟡 PRODUCTION STATUS: DEGRADED")
            print(f"⚠️  The application has {error_issues} error(s)")
            print(f"🔧 REQUIRES IMMEDIATE ATTENTION")
            return False
        elif len(self.warnings) > 0:
            print(f"\n🟢 PRODUCTION STATUS: OPERATIONAL WITH WARNINGS")
            print(f"✅ Application is functional but has {len(self.warnings)} warning(s)")
            return True
        else:
            print(f"\n🟢 PRODUCTION STATUS: FULLY OPERATIONAL")
            print(f"✅ All systems functioning normally")
            print(f"🎉 PRODUCTION RESOLUTION CONFIRMED")
            return True

if __name__ == "__main__":
    validator = ProductionValidator("https://ai-learning-tracker-bharath.azurewebsites.net")
    is_healthy = validator.validate_production_readiness()
    
    sys.exit(0 if is_healthy else 1)
