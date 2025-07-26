# Enhanced upload route with user-friendly error descriptions
from flask import Flask, jsonify

def add_enhanced_upload_route(app, get_db_connection, get_current_user):
    """Add enhanced upload route to Flask app"""
    
    @app.route('/admin/upload_excel_courses_enhanced', methods=['POST'])
    def admin_upload_excel_courses_enhanced():
        """Upload courses from Excel file with enhanced error descriptions - Admin only"""
        from enhanced_upload import handle_excel_upload_with_descriptions
        return handle_excel_upload_with_descriptions(get_db_connection, get_current_user)
    
    return app
