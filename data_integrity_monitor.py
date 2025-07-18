"""
Data Integrity Monitor - Azure Deployment Safety System
======================================================

This module implements comprehensive data integrity checks during Azure restart/deployment
to prevent data loss and ensure robust deployment processes.

CRITICAL FEATURES:
- Pre/post deployment user count validation
- Schema consistency checks
- Data integrity validation with checksums
- Atomic transaction monitoring
- Comprehensive deployment logging
- Alert system for data anomalies
"""

import sqlite3
import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import os
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_integrity.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DataIntegrityMonitor')

class IntegrityCheckResult(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"

@dataclass
class DataSnapshot:
    """Represents a snapshot of database state"""
    timestamp: datetime
    user_count: int
    course_count: int
    learning_entries_count: int
    user_courses_count: int
    schema_hash: str
    data_checksums: Dict[str, str]
    critical_tables: List[str]

@dataclass
class IntegrityCheckReport:
    """Report of integrity check results"""
    check_time: datetime
    overall_result: IntegrityCheckResult
    user_count_change: int
    missing_records: List[str]
    schema_changes: List[str]
    data_corruption_detected: bool
    recommendations: List[str]
    alert_level: str

class DataIntegrityMonitor:
    """
    Monitors data integrity during Azure deployments and restarts
    """
    
    def __init__(self, db_path: str = 'ai_learning.db'):
        self.db_path = db_path
        self.snapshot_file = 'pre_deployment_snapshot.json'
        self.integrity_log_file = 'integrity_checks.log'
        
    def get_db_connection(self):
        """Get database connection with proper error handling"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def calculate_table_checksum(self, table_name: str) -> str:
        """Calculate checksum for a table's data"""
        conn = self.get_db_connection()
        try:
            # Get all data from table ordered by primary key for consistency
            cursor = conn.execute(f"SELECT * FROM {table_name} ORDER BY id")
            rows = cursor.fetchall()
            
            # Create a string representation of all data
            data_string = ""
            for row in rows:
                data_string += str(dict(row))
            
            # Calculate MD5 hash
            return hashlib.md5(data_string.encode()).hexdigest()
        except sqlite3.Error as e:
            logger.error(f"Error calculating checksum for {table_name}: {e}")
            return "ERROR"
        finally:
            conn.close()
    
    def get_schema_hash(self) -> str:
        """Get hash of database schema"""
        conn = self.get_db_connection()
        try:
            # Get schema for all tables
            cursor = conn.execute("""
                SELECT name, sql FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            schema_info = cursor.fetchall()
            
            schema_string = ""
            for table in schema_info:
                schema_string += f"{table['name']}: {table['sql']}\n"
            
            return hashlib.md5(schema_string.encode()).hexdigest()
        except sqlite3.Error as e:
            logger.error(f"Error getting schema hash: {e}")
            return "ERROR"
        finally:
            conn.close()
    
    def get_current_snapshot(self) -> DataSnapshot:
        """Get current database snapshot"""
        conn = self.get_db_connection()
        try:
            # Get table counts
            user_count = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()['count']
            course_count = conn.execute("SELECT COUNT(*) as count FROM courses").fetchone()['count']
            
            # Handle tables that might not exist
            try:
                learning_entries_count = conn.execute("SELECT COUNT(*) as count FROM learning_entries").fetchone()['count']
            except sqlite3.OperationalError:
                learning_entries_count = 0
            
            try:
                user_courses_count = conn.execute("SELECT COUNT(*) as count FROM user_courses").fetchone()['count']
            except sqlite3.OperationalError:
                user_courses_count = 0
            
            # Get schema hash
            schema_hash = self.get_schema_hash()
            
            # Calculate checksums for critical tables
            critical_tables = ['users', 'courses']
            data_checksums = {}
            
            for table in critical_tables:
                try:
                    data_checksums[table] = self.calculate_table_checksum(table)
                except:
                    data_checksums[table] = "ERROR"
            
            return DataSnapshot(
                timestamp=datetime.now(),
                user_count=user_count,
                course_count=course_count,
                learning_entries_count=learning_entries_count,
                user_courses_count=user_courses_count,
                schema_hash=schema_hash,
                data_checksums=data_checksums,
                critical_tables=critical_tables
            )
        finally:
            conn.close()
    
    def save_pre_deployment_snapshot(self) -> bool:
        """Save snapshot before deployment"""
        try:
            snapshot = self.get_current_snapshot()
            
            # Convert to dictionary for JSON serialization
            snapshot_dict = {
                'timestamp': snapshot.timestamp.isoformat(),
                'user_count': snapshot.user_count,
                'course_count': snapshot.course_count,
                'learning_entries_count': snapshot.learning_entries_count,
                'user_courses_count': snapshot.user_courses_count,
                'schema_hash': snapshot.schema_hash,
                'data_checksums': snapshot.data_checksums,
                'critical_tables': snapshot.critical_tables
            }
            
            with open(self.snapshot_file, 'w') as f:
                json.dump(snapshot_dict, f, indent=2)
            
            logger.info(f"Pre-deployment snapshot saved: {snapshot.user_count} users, {snapshot.course_count} courses")
            return True
        except Exception as e:
            logger.error(f"Failed to save pre-deployment snapshot: {e}")
            return False
    
    def load_pre_deployment_snapshot(self) -> Optional[DataSnapshot]:
        """Load pre-deployment snapshot"""
        try:
            if not os.path.exists(self.snapshot_file):
                logger.warning("No pre-deployment snapshot found")
                return None
            
            with open(self.snapshot_file, 'r') as f:
                data = json.load(f)
            
            return DataSnapshot(
                timestamp=datetime.fromisoformat(data['timestamp']),
                user_count=data['user_count'],
                course_count=data['course_count'],
                learning_entries_count=data['learning_entries_count'],
                user_courses_count=data['user_courses_count'],
                schema_hash=data['schema_hash'],
                data_checksums=data['data_checksums'],
                critical_tables=data['critical_tables']
            )
        except Exception as e:
            logger.error(f"Failed to load pre-deployment snapshot: {e}")
            return None
    
    def run_post_deployment_check(self) -> IntegrityCheckReport:
        """Run comprehensive post-deployment integrity check"""
        logger.info("Starting post-deployment integrity check...")
        
        # Get current state
        current_snapshot = self.get_current_snapshot()
        pre_snapshot = self.load_pre_deployment_snapshot()
        
        if not pre_snapshot:
            return IntegrityCheckReport(
                check_time=datetime.now(),
                overall_result=IntegrityCheckResult.WARNING,
                user_count_change=0,
                missing_records=[],
                schema_changes=[],
                data_corruption_detected=False,
                recommendations=["No pre-deployment snapshot available for comparison"],
                alert_level="WARNING"
            )
        
        # Initialize check results
        issues = []
        warnings = []
        recommendations = []
        
        # Check 1: User count validation
        user_count_change = current_snapshot.user_count - pre_snapshot.user_count
        if user_count_change < 0:
            issues.append(f"CRITICAL: User count decreased by {abs(user_count_change)} users!")
            recommendations.append("Immediate data recovery required - users have been lost")
        elif user_count_change > 100:  # Suspicious large increase
            warnings.append(f"WARNING: User count increased by {user_count_change} (verify if expected)")
        
        # Check 2: Course count validation
        course_count_change = current_snapshot.course_count - pre_snapshot.course_count
        if course_count_change < -10:  # Allow small variations
            issues.append(f"CRITICAL: Course count decreased by {abs(course_count_change)} courses!")
        
        # Check 3: Schema consistency
        schema_changes = []
        if current_snapshot.schema_hash != pre_snapshot.schema_hash:
            schema_changes.append("Database schema has changed")
            warnings.append("Schema modification detected - verify intentional")
        
        # Check 4: Data integrity via checksums
        data_corruption_detected = False
        missing_records = []
        
        for table in pre_snapshot.critical_tables:
            if table in current_snapshot.data_checksums and table in pre_snapshot.data_checksums:
                if current_snapshot.data_checksums[table] != pre_snapshot.data_checksums[table]:
                    if table == 'users' and user_count_change != 0:
                        # Expected change due to user count difference
                        continue
                    elif table == 'courses' and course_count_change != 0:
                        # Expected change due to course count difference
                        continue
                    else:
                        data_corruption_detected = True
                        missing_records.append(f"Data integrity issue in {table} table")
        
        # Determine overall result
        if issues or data_corruption_detected:
            overall_result = IntegrityCheckResult.FAIL
            alert_level = "CRITICAL"
        elif warnings:
            overall_result = IntegrityCheckResult.WARNING
            alert_level = "WARNING"
        else:
            overall_result = IntegrityCheckResult.PASS
            alert_level = "INFO"
        
        # Generate recommendations
        if overall_result == IntegrityCheckResult.FAIL:
            recommendations.extend([
                "IMMEDIATE ACTION REQUIRED",
                "1. Stop all application traffic",
                "2. Initiate emergency data recovery procedure",
                "3. Restore from latest backup",
                "4. Investigate deployment process"
            ])
        elif overall_result == IntegrityCheckResult.WARNING:
            recommendations.extend([
                "Review deployment logs",
                "Verify expected data changes",
                "Monitor for additional anomalies"
            ])
        else:
            recommendations.append("Deployment successful - data integrity maintained")
        
        report = IntegrityCheckReport(
            check_time=datetime.now(),
            overall_result=overall_result,
            user_count_change=user_count_change,
            missing_records=missing_records,
            schema_changes=schema_changes,
            data_corruption_detected=data_corruption_detected,
            recommendations=recommendations,
            alert_level=alert_level
        )
        
        # Log results
        self.log_integrity_check(report, current_snapshot, pre_snapshot)
        
        return report
    
    def log_integrity_check(self, report: IntegrityCheckReport, 
                          current: DataSnapshot, pre: DataSnapshot):
        """Log detailed integrity check results"""
        log_entry = {
            'timestamp': report.check_time.isoformat(),
            'result': report.overall_result.value,
            'alert_level': report.alert_level,
            'user_count_change': report.user_count_change,
            'current_users': current.user_count,
            'previous_users': pre.user_count,
            'current_courses': current.course_count,
            'previous_courses': pre.course_count,
            'schema_changed': len(report.schema_changes) > 0,
            'data_corruption': report.data_corruption_detected,
            'missing_records': report.missing_records,
            'recommendations': report.recommendations
        }
        
        # Write to integrity log file
        with open(self.integrity_log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        # Log to standard logger
        if report.overall_result == IntegrityCheckResult.FAIL:
            logger.critical(f"INTEGRITY CHECK FAILED: {report.recommendations}")
        elif report.overall_result == IntegrityCheckResult.WARNING:
            logger.warning(f"Integrity check warnings: {report.missing_records}")
        else:
            logger.info(f"Integrity check passed: {current.user_count} users maintained")
    
    def send_alert(self, report: IntegrityCheckReport):
        """Send alert for critical integrity issues"""
        if report.alert_level == "CRITICAL":
            # In production, this would integrate with Azure Monitor, email, Slack, etc.
            alert_message = f"""
            🚨 CRITICAL DATA INTEGRITY ALERT 🚨
            
            Time: {report.check_time}
            Status: {report.overall_result.value}
            User Count Change: {report.user_count_change}
            
            Issues Detected:
            {chr(10).join(report.missing_records)}
            
            Immediate Actions Required:
            {chr(10).join(report.recommendations)}
            """
            
            logger.critical(alert_message)
            
            # TODO: Integrate with actual alerting system
            # - Azure Monitor alerts
            # - Email notifications
            # - Slack/Teams webhooks
            # - SMS alerts for critical issues
    
    def validate_acid_compliance(self) -> bool:
        """Test ACID compliance of database operations"""
        conn = self.get_db_connection()
        try:
            # Test atomicity with a transaction
            conn.execute("BEGIN TRANSACTION")
            
            # Insert test data
            test_user_id = 99999
            conn.execute("INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)",
                        (test_user_id, "test_acid", "test_hash"))
            
            # Verify data exists within transaction
            result = conn.execute("SELECT * FROM users WHERE id = ?", (test_user_id,)).fetchone()
            if not result:
                logger.error("ACID test failed: Data not visible within transaction")
                conn.rollback()
                return False
            
            # Rollback transaction
            conn.rollback()
            
            # Verify data was rolled back
            result = conn.execute("SELECT * FROM users WHERE id = ?", (test_user_id,)).fetchone()
            if result:
                logger.error("ACID test failed: Data persisted after rollback")
                return False
            
            logger.info("ACID compliance test passed")
            return True
            
        except Exception as e:
            logger.error(f"ACID compliance test failed: {e}")
            try:
                conn.rollback()
            except:
                pass
            return False
        finally:
            conn.close()

def run_pre_deployment_check():
    """Entry point for pre-deployment checks"""
    monitor = DataIntegrityMonitor()
    
    logger.info("=== PRE-DEPLOYMENT DATA INTEGRITY CHECK ===")
    
    # Save snapshot
    if monitor.save_pre_deployment_snapshot():
        logger.info("✅ Pre-deployment snapshot saved successfully")
    else:
        logger.error("❌ Failed to save pre-deployment snapshot")
        return False
    
    # Test ACID compliance
    if monitor.validate_acid_compliance():
        logger.info("✅ ACID compliance validated")
    else:
        logger.error("❌ ACID compliance test failed")
        return False
    
    logger.info("=== PRE-DEPLOYMENT CHECK COMPLETE ===")
    return True

def run_post_deployment_check():
    """Entry point for post-deployment checks"""
    monitor = DataIntegrityMonitor()
    
    logger.info("=== POST-DEPLOYMENT DATA INTEGRITY CHECK ===")
    
    # Run comprehensive check
    report = monitor.run_post_deployment_check()
    
    # Send alerts if needed
    monitor.send_alert(report)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"DEPLOYMENT INTEGRITY CHECK RESULTS")
    print(f"{'='*50}")
    print(f"Overall Result: {report.overall_result.value}")
    print(f"Alert Level: {report.alert_level}")
    print(f"User Count Change: {report.user_count_change}")
    print(f"Data Corruption: {report.data_corruption_detected}")
    print(f"\nRecommendations:")
    for rec in report.recommendations:
        print(f"- {rec}")
    print(f"{'='*50}\n")
    
    return report.overall_result == IntegrityCheckResult.PASS

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "pre":
            success = run_pre_deployment_check()
            sys.exit(0 if success else 1)
        elif sys.argv[1] == "post":
            success = run_post_deployment_check()
            sys.exit(0 if success else 1)
    
    print("Usage: python data_integrity_monitor.py [pre|post]")
    print("  pre  - Run pre-deployment snapshot and checks")
    print("  post - Run post-deployment integrity validation")
