"""
Admin Upload Reports Routes
Provides admin-only access to upload reports, detailed drilldown, and purging functionality
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta
import logging
from upload_reports_manager import (
    UploadReportsManager, get_upload_reports, get_report_details, 
    purge_old_reports
)

logger = logging.getLogger(__name__)

# Create Blueprint
admin_reports_bp = Blueprint('admin_reports', __name__, url_prefix='/admin/reports')

def get_current_user():
    """Get current user from g object (set by before_request handler)"""
    from flask import g
    return getattr(g, 'user', None)

def is_admin():
    """Check if current user is admin"""
    user = get_current_user()
    return user and user['username'] == 'admin'

def require_admin(f):
    """Decorator to require admin access"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin():
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_reports_bp.route('/')
@require_admin
def upload_reports_list():
    """Main upload reports list page"""
    try:
        # Get filter parameters
        days_back = request.args.get('days', 30, type=int)
        user_filter = request.args.get('user_id', type=int)
        
        # Validate days_back range
        if days_back < 1:
            days_back = 30
        elif days_back > 365:
            days_back = 365
        
        # Get reports
        reports = get_upload_reports(user_id=user_filter, days_back=days_back)
        
        # Get statistics
        manager = UploadReportsManager()
        stats = manager.get_upload_statistics(days_back=days_back)
        
        return render_template('admin/upload_reports.html', 
                             reports=reports, 
                             stats=stats,
                             days_back=days_back,
                             user_filter=user_filter)
        
    except Exception as e:
        logger.error(f"Error loading upload reports: {e}")
        flash(f'Error loading upload reports: {str(e)}', 'error')
        return redirect(url_for('admin.courses'))  # Fixed route name

@admin_reports_bp.route('/details/<int:report_id>')
@require_admin
def report_details(report_id):
    """Detailed view of a specific upload report"""
    try:
        report_summary, row_details = get_report_details(report_id)
        
        if not report_summary:
            flash('Upload report not found.', 'error')
            return redirect(url_for('admin_reports.upload_reports_list'))
        
        # Organize row details by status for easier viewing
        details_by_status = {
            'SUCCESS': [],
            'ERROR': [],
            'SKIPPED': []
        }
        
        for detail in row_details:
            status = detail['status']
            if status in details_by_status:
                details_by_status[status].append(detail)
        
        return render_template('admin/upload_report_details.html',
                             report=report_summary,
                             row_details=row_details,
                             details_by_status=details_by_status)
        
    except Exception as e:
        logger.error(f"Error loading report details for {report_id}: {e}")
        flash(f'Error loading report details: {str(e)}', 'error')
        return redirect(url_for('admin_reports.upload_reports_list'))

@admin_reports_bp.route('/purge', methods=['POST'])
@require_admin
def purge_reports():
    """Purge old upload reports"""
    try:
        days_to_keep = request.form.get('days_to_keep', 90, type=int)
        
        # Validate days_to_keep
        if days_to_keep < 7:
            flash('Minimum retention period is 7 days for safety.', 'warning')
            return redirect(url_for('admin_reports.upload_reports_list'))
        
        if days_to_keep > 1000:
            flash('Maximum retention period is 1000 days.', 'warning')
            return redirect(url_for('admin_reports.upload_reports_list'))
        
        # Perform purge
        result = purge_old_reports(days_to_keep)
        
        flash(f"Purged {result['reports_purged']} reports and {result['details_purged']} detail records older than {days_to_keep} days.", 'success')
        
    except Exception as e:
        logger.error(f"Error purging reports: {e}")
        flash(f'Error purging reports: {str(e)}', 'error')
    
    return redirect(url_for('admin_reports.upload_reports_list'))

@admin_reports_bp.route('/api/stats')
@require_admin
def api_stats():
    """API endpoint for upload statistics"""
    try:
        days_back = request.args.get('days', 30, type=int)
        manager = UploadReportsManager()
        stats = manager.get_upload_statistics(days_back=days_back)
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting upload stats: {e}")
        return jsonify({'error': str(e)}), 500

@admin_reports_bp.route('/export/<int:report_id>')
@require_admin
def export_report(report_id):
    """Export report details as CSV"""
    try:
        from flask import Response
        import csv
        from io import StringIO
        
        report_summary, row_details = get_report_details(report_id)
        
        if not report_summary:
            flash('Upload report not found.', 'error')
            return redirect(url_for('admin_reports.upload_reports_list'))
        
        # Create CSV content
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Row Number', 'Status', 'Course Title', 'Course URL', 'Message'
        ])
        
        # Write row details
        for detail in row_details:
            writer.writerow([
                detail['row_number'],
                detail['status'],
                detail['course_title'] or '',
                detail['course_url'] or '',
                detail['message'] or ''
            ])
        
        # Prepare response
        output.seek(0)
        filename = f"upload_report_{report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
        
    except Exception as e:
        logger.error(f"Error exporting report {report_id}: {e}")
        flash(f'Error exporting report: {str(e)}', 'error')
        return redirect(url_for('admin_reports.report_details', report_id=report_id))

# Register error handlers
@admin_reports_bp.errorhandler(403)
def forbidden(error):
    flash('Admin access required.', 'error')
    return redirect(url_for('auth.login'))  # Fixed route name

@admin_reports_bp.errorhandler(404)
def not_found(error):
    flash('Report not found.', 'error')
    return redirect(url_for('admin_reports.upload_reports_list'))

@admin_reports_bp.errorhandler(500)
def internal_error(error):
    flash('An internal error occurred.', 'error')
    return redirect(url_for('admin_reports.upload_reports_list'))
