from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g, jsonify
from werkzeug.security import generate_password_hash
import sqlite3
from datetime import datetime
import threading
import logging

# Import the course validator
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from course_validator import CourseURLValidator

# Configure logging for admin operations
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)

def get_courses_for_topic(topic_name, search_keywords):
    """
    Placeholder function to get courses for a topic.
    In a real implementation, this would integrate with external APIs
    like Microsoft Learn, Coursera, etc.
    
    Args:
        topic_name: The topic to search for courses
        search_keywords: Additional keywords for refined search
        
    Returns:
        List of course dictionaries with keys: title, source, level, link, points, description
    """
    # For now, return an empty list to prevent errors
    # This should be replaced with actual API integration
    logger.info(f"Course search requested for topic: {topic_name}, keywords: {search_keywords}")
    
    # Placeholder courses (remove this in production and add real API integration)
    placeholder_courses = []
    
    return placeholder_courses

def get_db_connection():
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_current_user():
    """Get current user from g object (set by before_request handler)"""
    return getattr(g, 'user', None)

def is_admin():
    """Check if current user is admin"""
    user = get_current_user()
    return user and user['username'] == 'admin'

@admin_bp.route('/admin')
def index():
    if not is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    conn = get_db_connection()
    
    # Get stats
    total_users = conn.execute('SELECT COUNT(*) as count FROM users WHERE username != "admin"').fetchone()['count']
    total_courses = conn.execute('SELECT COUNT(*) as count FROM courses').fetchone()['count']
    total_global_learnings = conn.execute('SELECT COUNT(*) as count FROM learning_entries WHERE is_global = 1').fetchone()['count']
    
    # Get recent users
    recent_users = conn.execute('''
        SELECT username, level, points, created_at 
        FROM users 
        WHERE username != "admin"
        ORDER BY created_at DESC 
        LIMIT 5
    ''').fetchall()
    
    conn.close()
    
    return render_template('admin/index.html',
                         total_users=total_users,
                         total_courses=total_courses,
                         total_global_learnings=total_global_learnings,
                         recent_users=recent_users)

@admin_bp.route('/admin/users')
def users():
    if not is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    conn = get_db_connection()
    users = conn.execute('''
        SELECT id, username, level, points, status, user_selected_level, created_at 
        FROM users 
        WHERE username != "admin"
        ORDER BY created_at DESC
    ''').fetchall()
    conn.close()
    
    return render_template('admin/users.html', users=users)

@admin_bp.route('/admin/add_user', methods=['GET', 'POST'])
def add_user():
    if not is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        # Import security functions
        from app import sanitize_input, validate_password_strength, log_security_event
        
        username = sanitize_input(request.form['username'])
        password = request.form['password']
        
        # Validate input
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('admin/add_user.html')
        
        if len(username) < 3 or len(username) > 50:
            flash('Username must be between 3 and 50 characters', 'error')
            return render_template('admin/add_user.html')
        
        # Validate password strength
        is_valid, message = validate_password_strength(password)
        if not is_valid:
            flash(message, 'error')
            return render_template('admin/add_user.html')
        
        if username and password:
            conn = get_db_connection()
            try:
                # Check for duplicates
                existing = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
                if existing:
                    flash('Username already exists', 'error')
                else:
                    password_hash = generate_password_hash(password)
                    conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', 
                               (username, password_hash))
                    conn.commit()
                    
                    # Log user creation
                    new_user = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
                    log_security_event('user_created', f'User {username} created by admin', 
                                     request.remote_addr, new_user['id'])
                    
                    flash(f'User {username} created successfully!', 'success')
                    return redirect(url_for('admin.users'))
            except Exception as e:
                flash(f'Error creating user: {str(e)}', 'error')
            finally:
                conn.close()
        else:
            flash('Username and password are required', 'error')
    
    return render_template('admin/add_user.html')

@admin_bp.route('/admin/courses')
def courses():
    if not is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    conn = get_db_connection()
    courses = conn.execute('''
        SELECT id, title, source, level, link, url, points, description, created_at,
               url_status, last_url_check,
               CASE 
                   WHEN level = 'Expert' THEN 4
                   WHEN level = 'Intermediate' THEN 3
                   WHEN level = 'Learner' THEN 2
                   WHEN level = 'Beginner' THEN 1
                   ELSE 0
               END as level_sort_order
        FROM courses 
        ORDER BY level_sort_order DESC, points DESC, title ASC
    ''').fetchall()
    conn.close()
    
    return render_template('admin/courses.html', courses=courses)

@admin_bp.route('/admin/add_course', methods=['GET', 'POST'])
def add_course():
    if not is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        title = request.form['title']
        source = request.form['source']
        level = request.form['level']
        link = request.form['link']
        points = int(request.form['points']) if request.form['points'] else 0
        description = request.form['description']
        
        if title and source and level and link:
            conn = get_db_connection()
            try:
                # Check for duplicates by title or link
                existing_title = conn.execute('SELECT id, title FROM courses WHERE LOWER(title) = LOWER(?)', (title,)).fetchone()
                existing_link = conn.execute('SELECT id, title FROM courses WHERE link = ?', (link,)).fetchone()
                
                if existing_title:
                    flash(f'A course with the title "{existing_title["title"]}" already exists.', 'error')
                elif existing_link:
                    flash(f'A course with this link already exists: "{existing_link["title"]}"', 'error')
                else:
                    conn.execute('''
                        INSERT INTO courses (title, source, level, link, points, description)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (title, source, level, link, points, description))
                    conn.commit()
                    flash(f'Course "{title}" added successfully!', 'success')
                    return redirect(url_for('admin.courses'))
            except Exception as e:
                flash(f'Error adding course: {str(e)}', 'error')
            finally:
                conn.close()
        else:
            flash('All required fields must be filled', 'error')
    
    return render_template('admin/add_course.html')

@admin_bp.route('/admin/populate_linkedin_courses', methods=['POST'])
def populate_linkedin_courses():
    if not is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    # LinkedIn Learning AI Courses
    linkedin_courses = [
        {
            'title': 'Artificial Intelligence Foundations: Machine Learning',
            'level': 'Beginner',
            'points': 50,
            'description': 'Learn the fundamentals of machine learning and AI concepts',
            'link': 'https://www.linkedin.com/learning/artificial-intelligence-foundations-machine-learning'
        },
        {
            'title': 'Python for Data Science Essential Training',
            'level': 'Beginner',
            'points': 60,
            'description': 'Master Python programming for data science and AI applications',
            'link': 'https://www.linkedin.com/learning/python-for-data-science-essential-training-part-1'
        },
        {
            'title': 'Deep Learning: Getting Started',
            'level': 'Learner',
            'points': 70,
            'description': 'Introduction to neural networks and deep learning concepts',
            'link': 'https://www.linkedin.com/learning/deep-learning-getting-started'
        },
        {
            'title': 'Natural Language Processing with Python',
            'level': 'Intermediate',
            'points': 80,
            'description': 'Build NLP applications using Python and modern libraries',
            'link': 'https://www.linkedin.com/learning/nlp-with-python-for-machine-learning-essential-training'
        },
        {
            'title': 'Computer Vision: Essential Training',
            'level': 'Intermediate',
            'points': 85,
            'description': 'Learn computer vision techniques and image processing',
            'link': 'https://www.linkedin.com/learning/computer-vision-essential-training'
        },
        {
            'title': 'Machine Learning with Python: Foundations',
            'level': 'Learner',
            'points': 65,
            'description': 'Build your first machine learning models with Python',
            'link': 'https://www.linkedin.com/learning/machine-learning-with-python-foundations'
        },
        {
            'title': 'TensorFlow: Getting Started',
            'level': 'Intermediate',
            'points': 75,
            'description': 'Learn TensorFlow for building neural networks',
            'link': 'https://www.linkedin.com/learning/tensorflow-getting-started'
        },
        {
            'title': 'Advanced TensorFlow: Eager Execution',
            'level': 'Expert',
            'points': 100,
            'description': 'Master advanced TensorFlow techniques and eager execution',
            'link': 'https://www.linkedin.com/learning/advanced-tensorflow-eager-execution'
        },
        {
            'title': 'AI Ethics: Technology and Society',
            'level': 'Beginner',
            'points': 40,
            'description': 'Understand ethical implications of AI in society',
            'link': 'https://www.linkedin.com/learning/artificial-intelligence-and-ethics'
        },
        {
            'title': 'Data Science for Business Decisions',
            'level': 'Learner',
            'points': 55,
            'description': 'Apply data science techniques to business problems',
            'link': 'https://www.linkedin.com/learning/data-science-for-business-decisions'
        },
        {
            'title': 'Reinforcement Learning Foundations',
            'level': 'Expert',
            'points': 120,
            'description': 'Master reinforcement learning algorithms and applications',
            'link': 'https://www.linkedin.com/learning/reinforcement-learning-foundations'
        },
        {
            'title': 'Applied AI for Business Professionals',
            'level': 'Beginner',
            'points': 45,
            'description': 'Understand how AI can transform business processes',
            'link': 'https://www.linkedin.com/learning/applied-ai-for-business-professionals'
        }
    ]
    
    conn = get_db_connection()
    added_count = 0
    duplicate_count = 0
    error_count = 0
    
    # Get all existing course titles for efficient duplicate checking
    existing_titles = set()
    existing_courses = conn.execute('SELECT title FROM courses').fetchall()
    for course in existing_courses:
        existing_titles.add(course['title'].lower().strip())
    
    for course in linkedin_courses:
        try:
            # Check for duplicates (case-insensitive)
            if course['title'].lower().strip() in existing_titles:
                duplicate_count += 1
                continue
            
            # Add the course
            conn.execute('''
                INSERT INTO courses (title, source, level, link, url, points, description, category, difficulty)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (course['title'], 'LinkedIn Learning', course['level'], 
                  course['link'], course['link'], course['points'], course['description'],
                  'AI/ML', course['level']))
            
            # Add to our local set to prevent duplicates within this batch
            existing_titles.add(course['title'].lower().strip())
            added_count += 1
            
        except Exception as e:
            error_count += 1
            print(f"Error adding course {course['title']}: {str(e)}")
    
    conn.commit()
    conn.close()
    
    # Provide detailed feedback
    if added_count > 0:
        flash(f'Successfully added {added_count} LinkedIn Learning AI courses!', 'success')
    if duplicate_count > 0:
        flash(f'{duplicate_count} courses were skipped (already exist)', 'info')
    if error_count > 0:
        flash(f'{error_count} courses had errors and were not added', 'warning')
    
    if added_count == 0 and duplicate_count > 0:
        flash('All LinkedIn Learning courses already exist in the database', 'info')
    
    return redirect(url_for('admin.courses'))

@admin_bp.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if not is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    conn = get_db_connection()
    try:
        # Get username for confirmation
        user = conn.execute('SELECT username FROM users WHERE id = ? AND username != "admin"', (user_id,)).fetchone()
        if not user:
            flash('User not found or cannot delete admin user.', 'error')
            return redirect(url_for('admin.users'))
        
        # Delete user's learning entries and course enrollments first
        conn.execute('DELETE FROM learning_entries WHERE user_id = ?', (user_id,))
        conn.execute('DELETE FROM user_courses WHERE user_id = ?', (user_id,))
        
        # Delete the user
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        
        flash(f'User {user["username"]} deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting user: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/admin/toggle_user_status/<int:user_id>', methods=['POST'])
def toggle_user_status(user_id):
    if not is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    conn = get_db_connection()
    try:
        # Get current status
        user = conn.execute('SELECT username, status FROM users WHERE id = ? AND username != "admin"', (user_id,)).fetchone()
        if not user:
            flash('User not found or cannot modify admin user.', 'error')
            return redirect(url_for('admin.users'))
        
        # Toggle status
        new_status = 'inactive' if user['status'] == 'active' else 'active'
        conn.execute('UPDATE users SET status = ? WHERE id = ?', (new_status, user_id))
        conn.commit()
        
        action = 'paused' if new_status == 'inactive' else 'activated'
        flash(f'User {user["username"]} {action} successfully!', 'success')
    except Exception as e:
        flash(f'Error updating user status: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/admin/delete_course/<int:course_id>', methods=['POST'])
def delete_course(course_id):
    if not is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    conn = get_db_connection()
    try:
        # Get course title for confirmation
        course = conn.execute('SELECT title FROM courses WHERE id = ?', (course_id,)).fetchone()
        if not course:
            flash('Course not found.', 'error')
            return redirect(url_for('admin.courses'))
        
        # Delete course enrollments first
        conn.execute('DELETE FROM user_courses WHERE course_id = ?', (course_id,))
        
        # Delete the course
        conn.execute('DELETE FROM courses WHERE id = ?', (course_id,))
        conn.commit()
        
        flash(f'Course "{course["title"]}" deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting course: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin.courses'))

@admin_bp.route('/admin/edit_course/<int:course_id>', methods=['GET', 'POST'])
def edit_course(course_id):
    if not is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        title = request.form['title']
        source = request.form['source']
        level = request.form['level']
        link = request.form['link']
        points = int(request.form['points']) if request.form['points'] else 0
        description = request.form['description']
        
        if title and source and level and link:
            try:
                # Check for duplicates (excluding current course)
                existing = conn.execute('''
                    SELECT id FROM courses 
                    WHERE title = ? AND id != ?
                ''', (title, course_id)).fetchone()
                
                if existing:
                    flash('A course with this title already exists.', 'error')
                else:
                    conn.execute('''
                        UPDATE courses 
                        SET title = ?, source = ?, level = ?, link = ?, points = ?, description = ?
                        WHERE id = ?
                    ''', (title, source, level, link, points, description, course_id))
                    conn.commit()
                    flash('Course updated successfully!', 'success')
                    return redirect(url_for('admin.courses'))
            except Exception as e:
                flash(f'Error updating course: {str(e)}', 'error')
        else:
            flash('All required fields must be filled', 'error')
    
    # Get course data for editing
    course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    conn.close()
    
    if not course:
        flash('Course not found.', 'error')
        return redirect(url_for('admin.courses'))
    
    return render_template('admin/edit_course.html', course=course)

@admin_bp.route('/admin/settings', methods=['GET', 'POST'])
def settings():
    if not is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        try:
            # Update level settings
            for level in ['Beginner', 'Learner', 'Intermediate', 'Expert']:
                points = int(request.form[f'{level.lower()}_points'])
                conn.execute('''
                    UPDATE level_settings 
                    SET points_required = ? 
                    WHERE level_name = ?
                ''', (points, level))
            
            conn.commit()
            flash('Level settings updated successfully!', 'success')
        except Exception as e:
            flash(f'Error updating settings: {str(e)}', 'error')
    
    # Get current level settings
    level_settings = conn.execute('''
        SELECT level_name, points_required 
        FROM level_settings 
        ORDER BY points_required
    ''').fetchall()
    
    conn.close()
    
    return render_template('admin/settings.html', level_settings=level_settings)

@admin_bp.route('/admin/course_search_configs', methods=['GET', 'POST'])
def course_search_configs():
    if not is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            topic_name = request.form['topic_name']
            search_keywords = request.form['search_keywords']
            source = request.form['source']
            
            if topic_name and search_keywords and source:
                try:
                    conn.execute('''
                        INSERT INTO course_search_configs (topic_name, search_keywords, source)
                        VALUES (?, ?, ?)
                    ''', (topic_name, search_keywords, source))
                    conn.commit()
                    flash(f'Search configuration for "{topic_name}" added successfully!', 'success')
                except sqlite3.IntegrityError:
                    flash('A configuration with this topic name already exists.', 'error')
            else:
                flash('All fields are required.', 'error')
        
        elif action == 'toggle':
            config_id = request.form['config_id']
            current_status = request.form['current_status'] == '1'
            new_status = 0 if current_status else 1
            
            conn.execute('''
                UPDATE course_search_configs 
                SET is_active = ? 
                WHERE id = ?
            ''', (new_status, config_id))
            conn.commit()
            flash('Configuration status updated!', 'success')
        
        elif action == 'delete':
            config_id = request.form['config_id']
            conn.execute('DELETE FROM course_search_configs WHERE id = ?', (config_id,))
            conn.commit()
            flash('Configuration deleted!', 'success')
    
    # Get all configurations
    configs = conn.execute('''
        SELECT * FROM course_search_configs 
        ORDER BY topic_name
    ''').fetchall()
    
    conn.close()
    return render_template('admin/course_search_configs.html', configs=configs)

@admin_bp.route('/admin/search_and_import_courses', methods=['POST'])
def search_and_import_courses():
    if not is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    selected_topics = request.form.getlist('selected_topics')
    
    if not selected_topics:
        flash('Please select at least one topic to search for courses.', 'error')
        return redirect(url_for('admin.course_search_configs'))
    
    conn = get_db_connection()
    
    # Get existing course titles for duplicate checking
    existing_titles = set()
    existing_courses = conn.execute('SELECT title FROM courses').fetchall()
    for course in existing_courses:
        existing_titles.add(course['title'].lower().strip())
    
    total_added = 0
    total_duplicates = 0
    
    for topic_id in selected_topics:
        # Get the search configuration
        config = conn.execute('''
            SELECT * FROM course_search_configs 
            WHERE id = ? AND is_active = 1
        ''', (topic_id,)).fetchone()
        
        if not config:
            continue
        
        # Get courses based on the topic
        courses = get_courses_for_topic(config['topic_name'], config['search_keywords'])
        
        for course in courses:
            try:
                # Check for duplicates (case-insensitive)
                if course['title'].lower().strip() in existing_titles:
                    total_duplicates += 1
                    continue
                
                # Add the course
                conn.execute('''
                    INSERT INTO courses (title, source, level, link, points, description)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (course['title'], course['source'], course['level'], 
                      course['link'], course['points'], course['description']))
                
                # Add to our local set to prevent duplicates within this batch
                existing_titles.add(course['title'].lower().strip())
                total_added += 1
                
            except Exception as e:
                print(f"Error adding course {course['title']}: {str(e)}")
    
    conn.commit()
    conn.close()
    
    # Provide feedback
    if total_added > 0:
        flash(f'Successfully added {total_added} courses!', 'success')
    if total_duplicates > 0:
        flash(f'{total_duplicates} courses were skipped (already exist)', 'info')
    if total_added == 0 and total_duplicates > 0:
        flash('All found courses already exist in the database', 'info')
    elif total_added == 0:
        flash('No courses found for the selected topics', 'warning')
    
    return redirect(url_for('admin.courses'))

@admin_bp.route('/admin/sessions')
def sessions():
    """Admin route to view and manage user sessions"""
    if not is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    conn = get_db_connection()
    
    # Get active sessions with user information
    active_sessions = conn.execute('''
        SELECT us.*, u.username, u.level, u.status,
               CASE WHEN us.expires_at > datetime('now') THEN 'Active' ELSE 'Expired' END as session_status
        FROM user_sessions us
        JOIN users u ON us.user_id = u.id
        WHERE us.is_active = 1
        ORDER BY us.created_at DESC
    ''').fetchall()
    
    # Get session activity statistics
    activity_stats = conn.execute('''
        SELECT activity_type, COUNT(*) as count
        FROM session_activity
        WHERE timestamp >= datetime('now', '-7 days')
        GROUP BY activity_type
        ORDER BY count DESC
    ''').fetchall()
    
    # Get login statistics for the last 7 days
    login_stats = conn.execute('''
        SELECT DATE(timestamp) as login_date, COUNT(*) as login_count
        FROM session_activity
        WHERE activity_type = 'session_created' 
        AND timestamp >= datetime('now', '-7 days')
        GROUP BY DATE(timestamp)
        ORDER BY login_date DESC
    ''').fetchall()
    
    conn.close()
    
    return render_template('admin/sessions.html', 
                         active_sessions=active_sessions,
                         activity_stats=activity_stats,
                         login_stats=login_stats)

@admin_bp.route('/admin/invalidate_session/<session_token>', methods=['POST'])
def invalidate_user_session(session_token):
    """Admin route to invalidate a specific user session"""
    if not is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    from app import invalidate_session, log_session_activity
    
    # Get session info before invalidating
    conn = get_db_connection()
    session_info = conn.execute('''
        SELECT us.*, u.username 
        FROM user_sessions us
        JOIN users u ON us.user_id = u.id
        WHERE us.session_token = ?
    ''', (session_token,)).fetchone()
    conn.close()
    
    if session_info:
        invalidate_session(session_token)
        log_session_activity(session_token, 'admin_session_invalidated', 
                           f'Session invalidated by admin for user: {session_info["username"]}')
        flash(f'Session for user {session_info["username"]} has been invalidated.', 'success')
    else:
        flash('Session not found.', 'error')
    
    return redirect(url_for('admin.sessions'))

@admin_bp.route('/admin/invalidate_all_sessions/<int:user_id>', methods=['POST'])
def invalidate_all_sessions_for_user(user_id):
    """Admin route to invalidate all sessions for a specific user"""
    if not is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    from app import invalidate_all_user_sessions, log_session_activity
    
    # Get user info
    conn = get_db_connection()
    user_info = conn.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    if user_info:
        invalidate_all_user_sessions(user_id)
        log_session_activity(None, 'admin_all_sessions_invalidated', 
                           f'All sessions invalidated by admin for user: {user_info["username"]}')
        flash(f'All sessions for user {user_info["username"]} have been invalidated.', 'success')
    else:
        flash('User not found.', 'error')
    
    return redirect(url_for('admin.sessions'))

@admin_bp.route('/admin/security')
def security_dashboard():
    """Admin security monitoring dashboard"""
    if not is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    conn = get_db_connection()
    
    # Get recent security events
    security_events = conn.execute('''
        SELECT se.*, u.username
        FROM security_events se
        LEFT JOIN users u ON se.user_id = u.id
        ORDER BY se.timestamp DESC
        LIMIT 50
    ''').fetchall()
    
    # Get security statistics
    event_stats = conn.execute('''
        SELECT event_type, COUNT(*) as count
        FROM security_events
        WHERE timestamp >= datetime('now', '-24 hours')
        GROUP BY event_type
        ORDER BY count DESC
    ''').fetchall()
    
    # Get most active IPs
    active_ips = conn.execute('''
        SELECT ip_address, COUNT(*) as count
        FROM security_events
        WHERE timestamp >= datetime('now', '-24 hours')
        AND ip_address IS NOT NULL
        GROUP BY ip_address
        ORDER BY count DESC
        LIMIT 10
    ''').fetchall()
    
    # Get failed login attempts by hour
    failed_logins = conn.execute('''
        SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
        FROM security_events
        WHERE event_type = 'failed_login'
        AND timestamp >= datetime('now', '-24 hours')
        GROUP BY hour
        ORDER BY hour
    ''').fetchall()
    
    # Get suspicious activity alerts
    suspicious_alerts = conn.execute('''
        SELECT * FROM security_events
        WHERE event_type IN ('suspicious_activity', 'unauthorized_admin_access', 'ip_blocked')
        AND timestamp >= datetime('now', '-7 days')
        ORDER BY timestamp DESC
        LIMIT 20
    ''').fetchall()
    
    conn.close()
    
    return render_template('admin/security.html',
                         security_events=security_events,
                         event_stats=event_stats,
                         active_ips=active_ips,
                         failed_logins=failed_logins,
                         suspicious_alerts=suspicious_alerts)

@admin_bp.route('/admin/block_ip', methods=['POST'])
def block_ip_address():
    """Admin route to manually block an IP address"""
    if not is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    ip_address = request.form.get('ip_address')
    duration = int(request.form.get('duration', 60))  # minutes
    reason = request.form.get('reason', 'Manual admin block')
    
    if ip_address:
        from app import block_ip, log_security_event
        block_ip(ip_address, duration)
        log_security_event('admin_ip_block', 
                         f'IP {ip_address} blocked by admin for {duration} minutes. Reason: {reason}',
                         ip_address)
        flash(f'IP address {ip_address} has been blocked for {duration} minutes.', 'success')
    else:
        flash('Invalid IP address.', 'error')
    
    return redirect(url_for('admin.security_dashboard'))

@admin_bp.route('/admin/unblock_ip', methods=['POST'])
def unblock_ip_address():
    """Admin route to manually unblock an IP address"""
    if not is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    ip_address = request.form.get('ip_address')
    
    if ip_address:
        from app import blocked_ips, log_security_event
        if ip_address in blocked_ips:
            del blocked_ips[ip_address]
            log_security_event('admin_ip_unblock', f'IP {ip_address} unblocked by admin', ip_address)
            flash(f'IP address {ip_address} has been unblocked.', 'success')
        else:
            flash(f'IP address {ip_address} was not blocked.', 'info')
    else:
        flash('Invalid IP address.', 'error')
    
    return redirect(url_for('admin.security_dashboard'))

@admin_bp.route('/admin/debug-session')
def debug_session():
    """Debug route to check session information"""
    debug_info = {
        'session_data': dict(session),
        'user_id': session.get('user_id'),
        'username': session.get('username'),
        'is_admin_function': is_admin(),
        'g_user': getattr(g, 'user', None)
    }
    return f"<pre>{debug_info}</pre>"

# Import the course validator (moved to top of file)
from course_validator import CourseURLValidator

@admin_bp.route('/admin/url-validation')
def url_validation():
    """URL validation management page - Admin only"""
    if not is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    conn = get_db_connection()
    
    # Get validation summary
    try:
        validator = CourseURLValidator()
        summary = validator.get_validation_summary()
        
        # Get courses by status
        working_courses = validator.get_courses_by_status('Working')
        not_working_courses = validator.get_courses_by_status('Not Working')
        broken_courses = validator.get_courses_by_status('Broken')
        unchecked_courses = validator.get_courses_by_status('unchecked')
        
        # Get total courses with URLs
        total_courses_with_urls = conn.execute('''
            SELECT COUNT(*) as count 
            FROM courses 
            WHERE (url IS NOT NULL AND url != '') 
               OR (link IS NOT NULL AND link != '')
        ''').fetchone()['count']
        
    except Exception as e:
        logger.error(f"Error getting validation data: {e}")
        flash(f'Error loading validation data: {str(e)}', 'error')
        summary = {}
        working_courses = []
        not_working_courses = []
        broken_courses = []
        unchecked_courses = []
        total_courses_with_urls = 0
    finally:
        conn.close()
    
    return render_template('admin/url_validation.html',
                         summary=summary,
                         working_courses=working_courses,
                         not_working_courses=not_working_courses,
                         broken_courses=broken_courses,
                         unchecked_courses=unchecked_courses,
                         total_courses_with_urls=total_courses_with_urls)

@admin_bp.route('/admin/validate-urls', methods=['POST'])
def validate_urls():
    """Start URL validation process - Admin only"""
    if not is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    try:
        # Get parameters from form
        max_courses = request.form.get('max_courses', type=int)
        status_filter = request.form.get('status_filter')
        course_ids_str = request.form.get('course_ids', '').strip()
        
        # Parse course IDs if provided
        course_ids = None
        if course_ids_str:
            try:
                course_ids = [int(id.strip()) for id in course_ids_str.split(',') if id.strip()]
            except ValueError:
                flash('Invalid course IDs format. Use comma-separated numbers.', 'error')
                return redirect(url_for('admin.url_validation'))
        
        # Filter by status if requested
        if status_filter and status_filter != 'all':
            validator = CourseURLValidator()
            courses_to_validate = validator.get_courses_by_status(status_filter)
            course_ids = [course['id'] for course in courses_to_validate]
            if not course_ids:
                flash(f'No courses found with status "{status_filter}".', 'info')
                return redirect(url_for('admin.url_validation'))
        
        # Start validation in background thread
        def run_validation():
            try:
                validator = CourseURLValidator()
                stats = validator.validate_course_urls(
                    course_ids=course_ids,
                    max_courses=max_courses
                )
                logger.info(f"URL validation completed: {stats}")
            except Exception as e:
                logger.error(f"URL validation error: {e}")
        
        validation_thread = threading.Thread(target=run_validation)
        validation_thread.daemon = True
        validation_thread.start()
        
        flash('URL validation started in background. Results will be updated automatically.', 'info')
        
    except Exception as e:
        logger.error(f"Error starting URL validation: {e}")
        flash(f'Error starting validation: {str(e)}', 'error')
    
    return redirect(url_for('admin.url_validation'))

@admin_bp.route('/admin/validate-url/<int:course_id>', methods=['POST'])
def validate_single_url(course_id):
    """Validate a single course URL - Admin only"""
    if not is_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        validator = CourseURLValidator()
        stats = validator.validate_course_urls(course_ids=[course_id])
        
        if stats['total_processed'] > 0:
            # Get updated course info
            conn = get_db_connection()
            course = conn.execute('''
                SELECT id, title, url, link, url_status, last_url_check
                FROM courses WHERE id = ?
            ''', (course_id,)).fetchone()
            conn.close()
            
            if course:
                return jsonify({
                    'success': True,
                    'course_id': course_id,
                    'status': course['url_status'],
                    'last_check': course['last_url_check'],
                    'title': course['title']
                })
        
        return jsonify({'error': 'Validation failed'}), 500
        
    except Exception as e:
        logger.error(f"Error validating single URL for course {course_id}: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/admin/url-validation-status')
def url_validation_status():
    """Get current URL validation status - Admin only (AJAX endpoint)"""
    if not is_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        validator = CourseURLValidator()
        summary = validator.get_validation_summary()
        
        # Calculate totals
        total_checked = sum(info['count'] for status, info in summary.items() if status != 'unchecked')
        total_unchecked = summary.get('unchecked', {}).get('count', 0)
        
        return jsonify({
            'summary': summary,
            'total_checked': total_checked,
            'total_unchecked': total_unchecked,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting validation status: {e}")
        return jsonify({'error': str(e)}), 500

