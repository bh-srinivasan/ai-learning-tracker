#!/usr/bin/env python3
"""
Add comprehensive row detail logging to upload functions
"""

import re

def add_row_detail_logging(file_path):
    """Add row detail logging for all cases in upload functions"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add row detail logging for validation errors
    validation_error_pattern = r"(stats\['error_details'\]\.append\(error_detail\)\s+stats\['errors'\] \+= 1\s+continue)"
    
    enhanced_validation_error = """stats['error_details'].append(error_detail)
                        stats['errors'] += 1
                        
                        # Add row detail to report
                        if report_id and reports_manager:
                            try:
                                reports_manager.add_row_detail(
                                    report_id=report_id,
                                    row_number=index + 1,
                                    status='failed',
                                    message=error_detail,
                                    course_title=title if title else 'N/A',
                                    course_url=url if url else 'N/A'
                                )
                            except Exception as detail_error:
                                print(f"Warning: Could not add error row detail: {detail_error}")
                        continue"""
    
    content = re.sub(validation_error_pattern, enhanced_validation_error, content)
    
    # Add row detail logging for skipped duplicates
    skip_pattern = r"(stats\['skipped'\] \+= 1\s+continue)"
    
    enhanced_skip = """stats['skipped'] += 1
                        
                        # Add row detail to report
                        if report_id and reports_manager:
                            try:
                                reports_manager.add_row_detail(
                                    report_id=report_id,
                                    row_number=index + 1,
                                    status='skipped',
                                    message='Duplicate course already exists',
                                    course_title=title,
                                    course_url=url
                                )
                            except Exception as detail_error:
                                print(f"Warning: Could not add skipped row detail: {detail_error}")
                        continue"""
    
    content = re.sub(skip_pattern, enhanced_skip, content)
    
    # Add row detail logging for database insert errors
    db_error_pattern = r"(stats\['error_details'\]\.append\(error_detail\)\s+stats\['errors'\] \+= 1\s+print\(f\"Database insert error for row \{index \+ 1\}: \{str\(db_error\)\}\"\)\s+continue)"
    
    enhanced_db_error = """stats['error_details'].append(error_detail)
                        stats['errors'] += 1
                        print(f"Database insert error for row {index + 1}: {str(db_error)}")
                        
                        # Add row detail to report
                        if report_id and reports_manager:
                            try:
                                reports_manager.add_row_detail(
                                    report_id=report_id,
                                    row_number=index + 1,
                                    status='failed',
                                    message=error_detail,
                                    course_title=title,
                                    course_url=url
                                )
                            except Exception as detail_error:
                                print(f"Warning: Could not add DB error row detail: {detail_error}")
                        continue"""
    
    content = re.sub(db_error_pattern, enhanced_db_error, content)
    
    # Add row detail logging for general processing errors
    processing_error_pattern = r"(stats\['error_details'\]\.append\(error_detail\)\s+stats\['errors'\] \+= 1\s+print\(f\"Row processing error for row \{index \+ 1\}: \{str\(row_error\)\}\"\)\s+continue)"
    
    enhanced_processing_error = """stats['error_details'].append(error_detail)
                    stats['errors'] += 1
                    print(f"Row processing error for row {index + 1}: {str(row_error)}")
                    
                    # Add row detail to report
                    if report_id and reports_manager:
                        try:
                            reports_manager.add_row_detail(
                                report_id=report_id,
                                row_number=index + 1,
                                status='failed',
                                message=error_detail,
                                course_title='Unknown',
                                course_url='Unknown'
                            )
                        except Exception as detail_error:
                            print(f"Warning: Could not add processing error row detail: {detail_error}")
                    continue"""
    
    content = re.sub(processing_error_pattern, enhanced_processing_error, content)
    
    return content

if __name__ == "__main__":
    file_path = "app.py"
    
    try:
        enhanced_content = add_row_detail_logging(file_path)
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(enhanced_content)
        
        print("✅ Successfully added comprehensive row detail logging")
        print("🔧 Added logging for:")
        print("   1. Validation errors")
        print("   2. Duplicate skips")
        print("   3. Database insert errors")
        print("   4. General processing errors")
        
    except Exception as e:
        print(f"❌ Error adding row detail logging: {e}")
        import traceback
        traceback.print_exc()
