"""
User-friendly error description generator for file uploads
"""

def generate_user_friendly_error_description(stats, error_type=None, details=None):
    """Generate user-friendly error descriptions for file uploads"""
    descriptions = []
    
    if error_type:
        # Specific error types
        error_messages = {
            'no_file': "Please select a file before clicking upload.",
            'empty_file': "The selected file appears to be empty or corrupted.",
            'invalid_format': "Only Excel files (.xlsx or .xls) are supported for course uploads.",
            'read_error': f"Unable to read the Excel file. {details if details else 'Please ensure the file is a valid Excel format and not password-protected.'}",
            'missing_columns': f"Your Excel file is missing required columns: {details}. Please download the template for the correct format.",
            'processing_error': f"Error occurred while processing the file. {details if details else 'Please try again.'}",
            'database_error': "Unable to save courses to database. Please try again or contact support.",
            'server_error': f"An unexpected server error occurred. {details if details else 'Please try again or contact support if the problem persists.'}"
        }
        return error_messages.get(error_type, f"An error occurred: {details if details else 'Unknown error'}")
    
    # Summary based on stats
    if stats and isinstance(stats, dict):
        if stats.get('added', 0) > 0:
            descriptions.append(f"Successfully added {stats['added']} new courses to the database.")
        
        if stats.get('skipped', 0) > 0:
            descriptions.append(f"Skipped {stats['skipped']} courses that already exist (same title and URL).")
        
        if stats.get('errors', 0) > 0:
            descriptions.append(f"Found {stats['errors']} rows with missing or invalid data that couldn't be processed.")
        
        if not descriptions:
            if stats.get('total_processed', 0) == 0:
                return "No courses were found in the uploaded file."
            else:
                return "All courses in the file were processed successfully."
    
    return " ".join(descriptions) if descriptions else "Upload completed."
