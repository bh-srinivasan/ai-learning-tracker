#!/usr/bin/env python3
"""
Script to apply upload reports fixes to app.py
"""

import re

def fix_upload_excel_functions(file_path):
    """Fix all upload excel functions in app.py"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to find the import section of each upload function
    import_pattern = r'(import pandas as pd\s+from datetime import datetime\s+import hashlib)'
    
    # Replace with enhanced imports
    enhanced_imports = '''import pandas as pd
        from datetime import datetime
        import hashlib
        from upload_reports_manager import UploadReportsManager
        
        # Initialize upload reports manager
        try:
            reports_manager = UploadReportsManager()
        except Exception as e:
            print(f"Warning: Could not initialize upload reports manager: {e}")
            reports_manager = None'''
    
    content = re.sub(import_pattern, enhanced_imports, content)
    
    # Fix the stats response - change 'added' to 'successful'
    stats_pattern = r"'stats': stats"
    enhanced_stats = """'stats': {
                    'total_processed': stats['total_processed'],
                    'successful': stats['added'],  # Frontend expects 'successful' not 'added'
                    'skipped': stats['skipped'],
                    'errors': stats['errors'],
                    'warnings': len(stats['error_details']) if stats['error_details'] else 0
                }"""
    
    content = re.sub(stats_pattern, enhanced_stats, content)
    
    # Add upload report creation after stats initialization
    stats_init_pattern = r"(stats = \{\s+'total_processed': 0,\s+'added': 0,\s+'skipped': 0,\s+'errors': 0,\s+'error_details': \[\]\s+\})"
    
    enhanced_stats_init = """stats = {
                'total_processed': 0,
                'added': 0,
                'skipped': 0,
                'errors': 0,
                'error_details': []
            }
            
            # Create upload report entry
            report_id = None
            if reports_manager:
                try:
                    report_id = reports_manager.create_upload_report(
                        user_id=user['id'],
                        filename=file.filename,
                        total_rows=len(df),
                        processed_rows=0,
                        success_count=0,
                        error_count=0,
                        warnings_count=0
                    )
                except Exception as report_error:
                    print(f"Warning: Could not create upload report: {report_error}")
                    report_id = None"""
    
    content = re.sub(stats_init_pattern, enhanced_stats_init, content, flags=re.MULTILINE | re.DOTALL)
    
    # Add row detail logging for successful insertions
    success_insert_pattern = r"(existing_set\.add\(\(title\.lower\(\), url\.lower\(\)\)\)\s+stats\['added'\] \+= 1)"
    
    enhanced_success = """existing_set.add((title.lower(), url.lower()))
                        stats['added'] += 1
                        
                        # Add successful row detail to report
                        if report_id and reports_manager:
                            try:
                                reports_manager.add_row_detail(
                                    report_id=report_id,
                                    row_number=index + 1,
                                    status='success',
                                    message='Course added successfully',
                                    course_title=title,
                                    course_url=url
                                )
                            except Exception as detail_error:
                                print(f"Warning: Could not add row detail: {detail_error}")"""
    
    content = re.sub(success_insert_pattern, enhanced_success, content)
    
    # Add final report update before commit
    commit_pattern = r"(conn\.commit\(\)\s+print\(f\"Transaction committed successfully\. Stats: \{stats\}\"\))"
    
    enhanced_commit = """conn.commit()
                print(f"Transaction committed successfully. Stats: {stats}")
                
                # Update the upload report with final statistics
                if report_id and reports_manager:
                    try:
                        reports_manager.update_upload_report(
                            report_id=report_id,
                            processed_rows=stats['total_processed'],
                            success_count=stats['added'],
                            error_count=stats['errors'],
                            warnings_count=stats['skipped']
                        )
                    except Exception as update_error:
                        print(f"Warning: Could not update upload report: {update_error}")"""
    
    content = re.sub(commit_pattern, enhanced_commit, content)
    
    return content

if __name__ == "__main__":
    # Read original file
    file_path = "app.py"
    
    try:
        fixed_content = fix_upload_excel_functions(file_path)
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print("✅ Successfully applied upload reports fixes to app.py")
        print("🔧 Fixed issues:")
        print("   1. Added UploadReportsManager integration")
        print("   2. Fixed stats.successful vs stats.added mismatch")
        print("   3. Added upload report persistence for all uploads")
        
    except Exception as e:
        print(f"❌ Error applying fixes: {e}")
        import traceback
        traceback.print_exc()
