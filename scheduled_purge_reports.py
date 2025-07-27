#!/usr/bin/env python3
"""
Automated Upload Reports Purging Script
Scheduled task to automatically purge old upload reports and maintain database size
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from upload_reports_manager import UploadReportsManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('upload_reports_purge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutomatedPurgeManager:
    """Manages automated purging of old upload reports"""
    
    def __init__(self):
        self.reports_manager = UploadReportsManager()
    
    def purge_reports(self, days_to_keep: int = 90, dry_run: bool = False) -> Dict[str, int]:
        """
        Purge old upload reports
        
        Args:
            days_to_keep: Number of days of reports to retain
            dry_run: If True, only count what would be purged without deleting
        
        Returns:
            Dictionary with purge statistics
        """
        logger.info(f"🧹 Starting {'DRY RUN' if dry_run else 'LIVE'} purge of reports older than {days_to_keep} days")
        
        try:
            if dry_run:
                # Count what would be purged
                cutoff_date = datetime.now() - timedelta(days=days_to_keep)
                
                # Get counts without deleting
                from database_environment_manager import DatabaseEnvironmentManager
                db_manager = DatabaseEnvironmentManager()
                db_manager.connect()
                cursor = db_manager.connection.cursor()
                
                # Count reports
                cursor.execute("""
                    SELECT COUNT(*) FROM excel_upload_reports 
                    WHERE upload_timestamp < ?
                """, (cutoff_date,))
                reports_count = cursor.fetchone()[0]
                
                # Count details
                cursor.execute("""
                    SELECT COUNT(*) FROM excel_upload_row_details 
                    WHERE report_id IN (
                        SELECT id FROM excel_upload_reports 
                        WHERE upload_timestamp < ?
                    )
                """, (cutoff_date,))
                details_count = cursor.fetchone()[0]
                
                db_manager.disconnect()
                
                result = {
                    'reports_purged': reports_count,
                    'details_purged': details_count,
                    'dry_run': True
                }
                
                logger.info(f"📊 DRY RUN: Would purge {reports_count} reports and {details_count} details")
                
            else:
                # Perform actual purge
                result = self.reports_manager.purge_old_reports(days_to_keep)
                result['dry_run'] = False
                
                logger.info(f"✅ LIVE PURGE: Purged {result['reports_purged']} reports and {result['details_purged']} details")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error during purge operation: {e}")
            raise
    
    def get_purge_recommendations(self) -> Dict:
        """
        Analyze the upload reports and provide purging recommendations
        """
        try:
            from database_environment_manager import DatabaseEnvironmentManager
            db_manager = DatabaseEnvironmentManager()
            db_manager.connect()
            cursor = db_manager.connection.cursor()
            
            # Get basic statistics
            cursor.execute("SELECT COUNT(*) FROM excel_upload_reports")
            total_reports = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM excel_upload_row_details")
            total_details = cursor.fetchone()[0]
            
            # Get oldest report
            cursor.execute("""
                SELECT MIN(upload_timestamp) FROM excel_upload_reports
            """)
            oldest_report = cursor.fetchone()[0]
            
            # Get count by age buckets
            now = datetime.now()
            age_buckets = {
                '30_days': now - timedelta(days=30),
                '90_days': now - timedelta(days=90),
                '180_days': now - timedelta(days=180),
                '1_year': now - timedelta(days=365)
            }
            
            counts_by_age = {}
            for bucket, cutoff in age_buckets.items():
                cursor.execute("""
                    SELECT COUNT(*) FROM excel_upload_reports 
                    WHERE upload_timestamp < ?
                """, (cutoff,))
                counts_by_age[bucket] = cursor.fetchone()[0]
            
            db_manager.disconnect()
            
            # Calculate recommendations
            recommendations = {
                'total_reports': total_reports,
                'total_details': total_details,
                'oldest_report': oldest_report,
                'counts_by_age': counts_by_age,
                'recommendations': []
            }
            
            if total_reports > 1000:
                recommendations['recommendations'].append({
                    'level': 'high',
                    'message': f'Database has {total_reports} reports. Consider purging to improve performance.',
                    'suggested_action': 'Purge reports older than 90 days'
                })
            
            if counts_by_age['1_year'] > 100:
                recommendations['recommendations'].append({
                    'level': 'medium',
                    'message': f'{counts_by_age["1_year"]} reports are older than 1 year.',
                    'suggested_action': 'Purge reports older than 365 days'
                })
            
            if total_details > 50000:
                recommendations['recommendations'].append({
                    'level': 'high',
                    'message': f'Database has {total_details} detail records. This may impact performance.',
                    'suggested_action': 'Consider more aggressive purging schedule'
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Error getting purge recommendations: {e}")
            return {'error': str(e)}

def main():
    """Main entry point for the purge script"""
    parser = argparse.ArgumentParser(description='Purge old upload reports')
    parser.add_argument('--days', type=int, default=90, 
                       help='Number of days of reports to keep (default: 90)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be purged without actually deleting')
    parser.add_argument('--recommendations', action='store_true',
                       help='Show purging recommendations based on current data')
    parser.add_argument('--quiet', action='store_true',
                       help='Reduce log output')
    
    args = parser.parse_args()
    
    # Adjust logging level
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    purge_manager = AutomatedPurgeManager()
    
    try:
        if args.recommendations:
            # Show recommendations
            logger.info("📋 Analyzing upload reports for purging recommendations...")
            recommendations = purge_manager.get_purge_recommendations()
            
            if 'error' in recommendations:
                logger.error(f"Failed to get recommendations: {recommendations['error']}")
                return 1
            
            print("\n" + "="*60)
            print("UPLOAD REPORTS PURGE RECOMMENDATIONS")
            print("="*60)
            print(f"Total Reports: {recommendations['total_reports']}")
            print(f"Total Detail Records: {recommendations['total_details']}")
            print(f"Oldest Report: {recommendations['oldest_report']}")
            print("\nReports by Age:")
            for bucket, count in recommendations['counts_by_age'].items():
                print(f"  Older than {bucket.replace('_', ' ')}: {count}")
            
            print("\nRecommendations:")
            if recommendations['recommendations']:
                for i, rec in enumerate(recommendations['recommendations'], 1):
                    level_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(rec['level'], "ℹ️")
                    print(f"  {i}. {level_icon} {rec['message']}")
                    print(f"     Suggested Action: {rec['suggested_action']}")
            else:
                print("  ✅ No specific recommendations. Database size is manageable.")
            print("="*60)
            
        else:
            # Perform purge
            if args.days < 7:
                logger.error("❌ Minimum retention period is 7 days for safety")
                return 1
            
            result = purge_manager.purge_reports(
                days_to_keep=args.days,
                dry_run=args.dry_run
            )
            
            # Log results
            if result['dry_run']:
                logger.info(f"📊 DRY RUN completed: Would purge {result['reports_purged']} reports, {result['details_purged']} details")
            else:
                logger.info(f"✅ Purge completed: Removed {result['reports_purged']} reports, {result['details_purged']} details")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Script failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
