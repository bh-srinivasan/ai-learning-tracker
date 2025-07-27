"""
Upload Reports Manager - Persistent upload/audit reporting and management
Provides CRUD operations for upload reports, row details, and automatic purging
"""

import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from database_environment_manager import DatabaseEnvironmentManager

logger = logging.getLogger(__name__)

class UploadReportsManager:
    """Manages persistent upload reports and audit trails"""
    
    def __init__(self):
        self.db_manager = DatabaseEnvironmentManager()
    
    def create_upload_report(self, user_id: int, filename: str, 
                           total_rows: int, processed_rows: int, 
                           success_count: int, error_count: int,
                           warnings_count: int = 0) -> int:
        """
        Create a new upload report entry
        Returns the report_id for linking row details
        """
        try:
            self.db_manager.connect()
            cursor = self.db_manager.connection.cursor()
            
            if self.db_manager.is_azure_sql():
                sql = """
                INSERT INTO excel_upload_reports 
                (user_id, filename, upload_timestamp, total_rows, processed_rows, 
                 success_count, error_count, warnings_count)
                OUTPUT INSERTED.id
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(sql, (user_id, filename, datetime.now(), 
                               total_rows, processed_rows, success_count, 
                               error_count, warnings_count))
                report_id = cursor.fetchone()[0]
            else:
                # SQLite
                sql = """
                INSERT INTO excel_upload_reports 
                (user_id, filename, upload_timestamp, total_rows, processed_rows, 
                 success_count, error_count, warnings_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(sql, (user_id, filename, datetime.now(), 
                               total_rows, processed_rows, success_count, 
                               error_count, warnings_count))
                report_id = cursor.lastrowid
            
            self.db_manager.connection.commit()
            logger.info(f"✅ Created upload report {report_id} for file: {filename}")
            return report_id
            
        except Exception as e:
            logger.error(f"❌ Error creating upload report: {e}")
            if self.db_manager.connection:
                self.db_manager.connection.rollback()
            raise
        finally:
            self.db_manager.disconnect()
    
    def add_row_detail(self, report_id: int, row_number: int, 
                      status: str, message: str, course_title: str = None,
                      course_url: str = None) -> None:
        """Add a detailed row result to the upload report"""
        try:
            self.db_manager.connect()
            cursor = self.db_manager.connection.cursor()
            
            sql = """
            INSERT INTO excel_upload_row_details 
            (report_id, row_number, status, message, course_title, course_url)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            cursor.execute(sql, (report_id, row_number, status, message, 
                           course_title, course_url))
            
            self.db_manager.connection.commit()
            
        except Exception as e:
            logger.error(f"❌ Error adding row detail: {e}")
            if self.db_manager.connection:
                self.db_manager.connection.rollback()
            raise
        finally:
            self.db_manager.disconnect()
    
    def update_upload_report(self, report_id: int, processed_rows: int = None,
                           success_count: int = None, error_count: int = None,
                           warnings_count: int = None) -> None:
        """Update an existing upload report with final statistics"""
        try:
            self.db_manager.connect()
            cursor = self.db_manager.connection.cursor()
            
            # Build dynamic update query based on provided parameters
            update_fields = []
            params = []
            
            if processed_rows is not None:
                update_fields.append("processed_rows = ?")
                params.append(processed_rows)
            
            if success_count is not None:
                update_fields.append("success_count = ?")
                params.append(success_count)
            
            if error_count is not None:
                update_fields.append("error_count = ?")
                params.append(error_count)
            
            if warnings_count is not None:
                update_fields.append("warnings_count = ?")
                params.append(warnings_count)
            
            if not update_fields:
                return  # Nothing to update
            
            params.append(report_id)
            sql = f"""
            UPDATE excel_upload_reports 
            SET {', '.join(update_fields)}
            WHERE id = ?
            """
            
            cursor.execute(sql, params)
            self.db_manager.connection.commit()
            
        except Exception as e:
            logger.error(f"❌ Error updating upload report: {e}")
            if self.db_manager.connection:
                self.db_manager.connection.rollback()
            raise
        finally:
            self.db_manager.disconnect()
    
    def get_upload_reports(self, user_id: int = None, 
                          days_back: int = 30) -> List[Dict]:
        """
        Get upload reports with optional filtering
        Returns list of report summaries
        """
        try:
            self.db_manager.connect()
            cursor = self.db_manager.connection.cursor()
            
            # Base query
            sql = """
            SELECT r.id, r.user_id, u.username, r.filename, r.upload_timestamp,
                   r.total_rows, r.processed_rows, r.success_count, 
                   r.error_count, r.warnings_count
            FROM excel_upload_reports r
            JOIN users u ON r.user_id = u.id
            WHERE r.upload_timestamp >= ?
            """
            params = [datetime.now() - timedelta(days=days_back)]
            
            if user_id:
                sql += " AND r.user_id = ?"
                params.append(user_id)
            
            sql += " ORDER BY r.upload_timestamp DESC"
            
            cursor.execute(sql, params)
            results = cursor.fetchall()
            
            reports = []
            for row in results:
                # Convert timestamp string to datetime object
                timestamp_str = row[4]
                try:
                    if isinstance(timestamp_str, str):
                        # Parse SQLite timestamp string
                        upload_timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    else:
                        upload_timestamp = timestamp_str
                except (ValueError, TypeError):
                    # Fallback to current time if parsing fails
                    upload_timestamp = datetime.now()
                
                reports.append({
                    'id': row[0],
                    'user_id': row[1],
                    'username': row[2],
                    'filename': row[3],
                    'upload_timestamp': upload_timestamp,
                    'total_rows': row[5],
                    'processed_rows': row[6],
                    'success_count': row[7],
                    'error_count': row[8],
                    'warnings_count': row[9]
                })
            
            return reports
            
        except Exception as e:
            logger.error(f"❌ Error getting upload reports: {e}")
            return []
        finally:
            self.db_manager.disconnect()
    
    def get_report_details(self, report_id: int) -> Tuple[Dict, List[Dict]]:
        """
        Get full report with row-by-row details
        Returns (report_summary, row_details)
        """
        try:
            self.db_manager.connect()
            cursor = self.db_manager.connection.cursor()
            
            # Get report summary
            sql = """
            SELECT r.id, r.user_id, u.username, r.filename, r.upload_timestamp,
                   r.total_rows, r.processed_rows, r.success_count, 
                   r.error_count, r.warnings_count
            FROM excel_upload_reports r
            JOIN users u ON r.user_id = u.id
            WHERE r.id = ?
            """
            cursor.execute(sql, (report_id,))
            report_row = cursor.fetchone()
            
            if not report_row:
                return None, []
            
            # Convert timestamp string to datetime object
            timestamp_str = report_row[4]
            try:
                if isinstance(timestamp_str, str):
                    # Parse SQLite timestamp string
                    upload_timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                else:
                    upload_timestamp = timestamp_str
            except (ValueError, TypeError):
                # Fallback to current time if parsing fails
                upload_timestamp = datetime.now()

            report_summary = {
                'id': report_row[0],
                'user_id': report_row[1],
                'username': report_row[2],
                'filename': report_row[3],
                'upload_timestamp': upload_timestamp,
                'total_rows': report_row[5],
                'processed_rows': report_row[6],
                'success_count': report_row[7],
                'error_count': report_row[8],
                'warnings_count': report_row[9]
            }            # Get row details
            sql = """
            SELECT row_number, status, message, course_title, course_url
            FROM excel_upload_row_details
            WHERE report_id = ?
            ORDER BY row_number
            """
            cursor.execute(sql, (report_id,))
            detail_rows = cursor.fetchall()
            
            row_details = []
            for row in detail_rows:
                row_details.append({
                    'row_number': row[0],
                    'status': row[1],
                    'message': row[2],
                    'course_title': row[3],
                    'course_url': row[4]
                })
            
            return report_summary, row_details
            
        except Exception as e:
            logger.error(f"❌ Error getting report details: {e}")
            return None, []
        finally:
            self.db_manager.disconnect()
    
    def purge_old_reports(self, days_to_keep: int = 90) -> Dict[str, int]:
        """
        Purge old upload reports and their details
        Returns counts of purged records
        """
        try:
            self.db_manager.connect()
            cursor = self.db_manager.connection.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Get reports to be purged for counting
            cursor.execute("""
                SELECT id FROM excel_upload_reports 
                WHERE upload_timestamp < ?
            """, (cutoff_date,))
            report_ids = [row[0] for row in cursor.fetchall()]
            
            if not report_ids:
                return {'reports_purged': 0, 'details_purged': 0}
            
            # Delete row details first (foreign key constraint)
            if self.db_manager.is_azure_sql():
                # SQL Server supports IN with placeholders differently
                placeholders = ','.join(['?' for _ in report_ids])
                sql = f"DELETE FROM excel_upload_row_details WHERE report_id IN ({placeholders})"
                cursor.execute(sql, report_ids)
            else:
                # SQLite
                placeholders = ','.join(['?' for _ in report_ids])
                sql = f"DELETE FROM excel_upload_row_details WHERE report_id IN ({placeholders})"
                cursor.execute(sql, report_ids)
            
            details_purged = cursor.rowcount
            
            # Delete reports
            cursor.execute("""
                DELETE FROM excel_upload_reports 
                WHERE upload_timestamp < ?
            """, (cutoff_date,))
            reports_purged = cursor.rowcount
            
            self.db_manager.connection.commit()
            
            result = {
                'reports_purged': reports_purged,
                'details_purged': details_purged
            }
            
            logger.info(f"🧹 Purged {reports_purged} reports and {details_purged} details older than {days_to_keep} days")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error purging old reports: {e}")
            if self.db_manager.connection:
                self.db_manager.connection.rollback()
            raise
        finally:
            self.db_manager.disconnect()
    
    def get_upload_statistics(self, days_back: int = 30) -> Dict:
        """Get upload statistics for dashboard/admin overview"""
        try:
            self.db_manager.connect()
            cursor = self.db_manager.connection.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            sql = """
            SELECT 
                COUNT(*) as total_uploads,
                SUM(total_rows) as total_rows_processed,
                SUM(success_count) as total_successes,
                SUM(error_count) as total_errors,
                SUM(warnings_count) as total_warnings,
                COUNT(DISTINCT user_id) as unique_users
            FROM excel_upload_reports
            WHERE upload_timestamp >= ?
            """
            cursor.execute(sql, (cutoff_date,))
            stats = cursor.fetchone()
            
            return {
                'total_uploads': stats[0] or 0,
                'total_rows_processed': stats[1] or 0,
                'total_successes': stats[2] or 0,
                'total_errors': stats[3] or 0,
                'total_warnings': stats[4] or 0,
                'unique_users': stats[5] or 0,
                'days_back': days_back
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting upload statistics: {e}")
            return {}
        finally:
            self.db_manager.disconnect()

# Convenience functions for use in Flask routes
def create_upload_report(user_id: int, filename: str, total_rows: int, 
                        processed_rows: int, success_count: int, 
                        error_count: int, warnings_count: int = 0) -> int:
    """Convenience function to create upload report"""
    manager = UploadReportsManager()
    return manager.create_upload_report(user_id, filename, total_rows, 
                                       processed_rows, success_count, 
                                       error_count, warnings_count)

def add_row_detail(report_id: int, row_number: int, status: str, 
                  message: str, course_title: str = None, 
                  course_url: str = None) -> None:
    """Convenience function to add row detail"""
    manager = UploadReportsManager()
    manager.add_row_detail(report_id, row_number, status, message, 
                          course_title, course_url)

def get_upload_reports(user_id: int = None, days_back: int = 30) -> List[Dict]:
    """Convenience function to get upload reports"""
    manager = UploadReportsManager()
    return manager.get_upload_reports(user_id, days_back)

def get_report_details(report_id: int) -> Tuple[Dict, List[Dict]]:
    """Convenience function to get report details"""
    manager = UploadReportsManager()
    return manager.get_report_details(report_id)

def purge_old_reports(days_to_keep: int = 90) -> Dict[str, int]:
    """Convenience function to purge old reports"""
    manager = UploadReportsManager()
    return manager.purge_old_reports(days_to_keep)
