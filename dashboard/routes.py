from flask import Blueprint, render_template, session, redirect, url_for, flash, request, g
import sqlite3
from level_manager import LevelManager

dashboard_bp = Blueprint('dashboard', __name__)

def get_db_connection():
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_current_user():
    """Get current user from g object (set by before_request handler)"""
    return getattr(g, 'user', None)

# Initialize level manager
level_manager = LevelManager()

def calculate_user_level(user_id):
    """Calculate user level based on points earned and admin settings - DEPRECATED, use LevelManager"""
    return level_manager.calculate_level_from_points(user_id)

def update_user_points_from_courses(user_id):
    """Update user points based on completed courses - DEPRECATED, use LevelManager"""
    return level_manager.update_user_points_from_courses(user_id)

def update_user_level(user_id):
    """Update user level in database based on points - DEPRECATED, use LevelManager"""
    new_level, total_points, level_points = level_manager.update_user_points_from_courses(user_id)
    # Update session if needed
    if 'user_level' in session:
        session['user_level'] = new_level
    return new_level

def calculate_progress_percentage(current_level, user_points):
    """Calculate progress percentage toward next level based on points and admin settings"""
    breakdown = level_manager.get_level_points_breakdown(user_points, current_level)
    return int(breakdown['progress_percentage'])

def get_next_level_info(current_level):
    """Get information about the next level based on admin settings"""
    # Get level settings from level manager
    settings = level_manager.get_level_settings()
    
    # Find next level
    for i, level in enumerate(settings):
        if level['level_name'] == current_level:
            if i + 1 < len(settings):
                next_level = settings[i + 1]
                return f"{next_level['level_name']} ({next_level['points_required']}+ points)"
            break
    
    return "You've reached the top!"

@dashboard_bp.route('/dashboard')
def index():
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
    
    # If admin, redirect to admin dashboard
    if user['username'] == 'admin':
        return redirect(url_for('admin.index'))
    
    user_id = user['id']
    
    # Update user level based on current points from completed courses
    current_level = update_user_level(user_id)
    
    # Get user points
    conn = get_db_connection()
    user_points = conn.execute('SELECT points FROM users WHERE id = ?', (user_id,)).fetchone()['points']
    
    # For regular users, show their own + global learnings
    recent_entries = conn.execute('''
        SELECT * FROM learning_entries 
        WHERE (user_id = ? OR is_global = 1)
        ORDER BY date_added DESC 
        LIMIT 5
    ''', (user_id,)).fetchall()
    
    # Get available courses for user
    available_courses = conn.execute('''
        SELECT c.*, 
               CASE WHEN uc.completed IS NOT NULL THEN uc.completed ELSE 0 END as completed
        FROM courses c
        LEFT JOIN user_courses uc ON c.id = uc.course_id AND uc.user_id = ?
        ORDER BY c.level, c.points DESC
        LIMIT 5
    ''', (user_id,)).fetchall()
    
    # Calculate progress percentage based on points
    progress_percentage = calculate_progress_percentage(current_level, user_points)
    next_level_info = get_next_level_info(current_level)
    
    conn.close()
    
    return render_template('dashboard/index.html', 
                         recent_entries=recent_entries,
                         user_points=user_points,
                         current_level=current_level,
                         recommended_courses=available_courses,
                         progress_percentage=progress_percentage,
                         next_level_info=next_level_info)

@dashboard_bp.route('/enroll_course/<int:course_id>', methods=['POST'])
def enroll_course(course_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
    
    user_id = user['id']
    conn = get_db_connection()
    
    try:
        # Check if already enrolled
        existing = conn.execute('''
            SELECT id FROM user_courses 
            WHERE user_id = ? AND course_id = ?
        ''', (user_id, course_id)).fetchone()
        
        if existing:
            flash('You are already enrolled in this course!', 'info')
        else:
            # Enroll user in course
            conn.execute('''
                INSERT INTO user_courses (user_id, course_id)
                VALUES (?, ?)
            ''', (user_id, course_id))
            conn.commit()
            flash('Successfully enrolled in course!', 'success')
    except Exception as e:
        flash('Error enrolling in course. Please try again.', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/complete_course/<int:course_id>', methods=['POST'])
def complete_course(course_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
    
    user_id = user['id']
    conn = get_db_connection()
    
    try:
        # Mark course as completed
        conn.execute('''
            UPDATE user_courses 
            SET completed = 1, completion_date = CURRENT_TIMESTAMP
            WHERE user_id = ? AND course_id = ?
        ''', (user_id, course_id))
        
        # If not enrolled, enroll and complete
        if conn.rowcount == 0:
            conn.execute('''
                INSERT INTO user_courses (user_id, course_id, completed, completion_date)
                VALUES (?, ?, 1, CURRENT_TIMESTAMP)
            ''', (user_id, course_id))
        
        conn.commit()
        
        # Update user points and level
        update_user_points_from_courses(user_id)
        
        flash('Course completed! Points have been awarded.', 'success')
    except Exception as e:
        flash('Error completing course. Please try again.', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    """Enhanced profile route with comprehensive level management"""
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
    
    user_id = user['id']
    
    if request.method == 'POST':
        # Handle level update with enhanced validation
        user_selected_level = request.form.get('user_selected_level')
        
        if user_selected_level in ['Beginner', 'Intermediate', 'Advanced']:
            # Use level manager to update with validation
            result = level_manager.update_user_selected_level(user_id, user_selected_level)
            
            if result['success']:
                flash(result['message'], 'success')
                
                # Update session if needed
                if 'user_level' in session:
                    session['user_selected_level'] = user_selected_level
            else:
                flash(result['message'], 'error')
        else:
            flash('Invalid expertise level selected', 'error')
    
    # Get comprehensive user level information
    level_info = level_manager.get_user_level_info(user_id)
    
    # Get user data for display
    conn = get_db_connection()
    user_data = conn.execute('''
        SELECT username, level, points, level_points, user_selected_level, created_at, 
               last_login, last_activity, login_count
        FROM users 
        WHERE id = ?
    ''', (user_id,)).fetchone()
    
    # Get user's active sessions
    active_sessions = conn.execute('''
        SELECT session_token, created_at, expires_at, ip_address, user_agent,
               CASE WHEN expires_at > datetime('now') THEN 'Active' ELSE 'Expired' END as status
        FROM user_sessions 
        WHERE user_id = ? AND is_active = 1
        ORDER BY created_at DESC
        LIMIT 5
    ''', (user_id,)).fetchall()
    
    # Get user's learning stats
    total_learnings = conn.execute('''
        SELECT COUNT(*) as count 
        FROM learning_entries 
        WHERE user_id = ? AND is_global = 0
    ''', (user_id,)).fetchone()['count']
    
    completed_courses = conn.execute('''
        SELECT COUNT(*) as count 
        FROM user_courses 
        WHERE user_id = ? AND completed = 1
    ''', (user_id,)).fetchone()['count']
    
    enrolled_courses = conn.execute('''
        SELECT COUNT(*) as count 
        FROM user_courses 
        WHERE user_id = ? AND completed = 0
    ''', (user_id,)).fetchone()['count']
    
    # Get recent points log for user
    points_log = level_manager.get_user_points_log(user_id, limit=10)
    
    conn.close()
    
    return render_template('dashboard/profile.html',
                         user=user_data,
                         level_info=level_info,
                         active_sessions=active_sessions,
                         total_learnings=total_learnings,
                         completed_courses=completed_courses,
                         enrolled_courses=enrolled_courses,
                         points_log=points_log)

@dashboard_bp.route('/add_course', methods=['GET', 'POST'])
def add_course():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # Admin users should use admin panel for adding courses
    if session.get('username') == 'admin':
        flash('Admin users should use the admin panel to add courses.', 'info')
        return redirect(url_for('admin.add_course'))
    
    if request.method == 'POST':
        title = request.form['title']
        source = request.form['source']
        course_url = request.form['course_url']
        description = request.form['description']
        completion_date = request.form['completion_date'] if request.form['completion_date'] else None
        user_id = get_current_user()['id']
        
        if title and source and course_url:
            conn = get_db_connection()
            try:
                # Check for duplicates by title and URL for this user
                existing_title = conn.execute('''
                    SELECT id FROM user_personal_courses 
                    WHERE user_id = ? AND LOWER(title) = LOWER(?)
                ''', (user_id, title)).fetchone()
                
                existing_url = conn.execute('''
                    SELECT id FROM user_personal_courses 
                    WHERE user_id = ? AND course_url = ?
                ''', (user_id, course_url)).fetchone()
                
                if existing_title:
                    flash('You already have a course with this title.', 'error')
                elif existing_url:
                    flash('You already have a course with this URL.', 'error')
                else:
                    conn.execute('''
                        INSERT INTO user_personal_courses (user_id, title, source, course_url, description, completion_date)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (user_id, title, source, course_url, description, completion_date))
                    conn.commit()
                    flash(f'Course "{title}" added successfully!', 'success')
                    return redirect(url_for('dashboard.my_courses'))
            except Exception as e:
                flash(f'Error adding course: {str(e)}', 'error')
            finally:
                conn.close()
        else:
            flash('Course title, source, and URL are required.', 'error')
    
    return render_template('dashboard/add_course.html')

@dashboard_bp.route('/my_courses')
def my_courses():
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
    
    # Admin users should use admin panel
    if user['username'] == 'admin':
        return redirect(url_for('admin.courses'))
    
    user_id = user['id']
    conn = get_db_connection()
    
    # Get user's personal courses
    personal_courses = conn.execute('''
        SELECT * FROM user_personal_courses 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    ''', (user_id,)).fetchall()
    
    conn.close()
    
    return render_template('dashboard/my_courses.html', courses=personal_courses)

@dashboard_bp.route('/edit_course/<int:course_id>', methods=['GET', 'POST'])
def edit_course(course_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
    
    user_id = user['id']
    conn = get_db_connection()
    
    # Get the course and verify ownership
    course = conn.execute('''
        SELECT * FROM user_personal_courses 
        WHERE id = ? AND user_id = ?
    ''', (course_id, user_id)).fetchone()
    
    if not course:
        flash('Course not found or access denied', 'error')
        return redirect(url_for('dashboard.my_courses'))
    
    if request.method == 'POST':
        title = request.form['title']
        source = request.form['source']
        course_url = request.form['course_url']
        description = request.form['description']
        completion_date = request.form['completion_date'] if request.form['completion_date'] else None
        
        if title and source and course_url:
            try:
                # Check for duplicates (excluding current course)
                existing = conn.execute('''
                    SELECT id FROM user_personal_courses 
                    WHERE user_id = ? AND LOWER(title) = LOWER(?) AND id != ?
                ''', (user_id, title, course_id)).fetchone()
                
                if existing:
                    flash('You already have a course with this title.', 'error')
                else:
                    conn.execute('''
                        UPDATE user_personal_courses 
                        SET title = ?, source = ?, course_url = ?, description = ?, completion_date = ?
                        WHERE id = ? AND user_id = ?
                    ''', (title, source, course_url, description, completion_date, course_id, user_id))
                    conn.commit()
                    flash('Course updated successfully!', 'success')
                    return redirect(url_for('dashboard.my_courses'))
            except Exception as e:
                flash(f'Error updating course: {str(e)}', 'error')
        else:
            flash('Course title, source, and URL are required.', 'error')
    
    conn.close()
    return render_template('dashboard/edit_course.html', course=course)

@dashboard_bp.route('/delete_course/<int:course_id>', methods=['POST'])
def delete_course(course_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
    
    user_id = user['id']
    conn = get_db_connection()
    
    try:
        # Get course title for confirmation
        course = conn.execute('''
            SELECT title FROM user_personal_courses 
            WHERE id = ? AND user_id = ?
        ''', (course_id, user_id)).fetchone()
        
        if not course:
            flash('Course not found or access denied.', 'error')
        else:
            # Delete the course
            conn.execute('''
                DELETE FROM user_personal_courses 
                WHERE id = ? AND user_id = ?
            ''', (course_id, user_id))
            conn.commit()
            flash(f'Course "{course["title"]}" deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting course: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('dashboard.my_courses'))

@dashboard_bp.route('/toggle_course_completion/<int:course_id>', methods=['POST'])
def toggle_course_completion(course_id):
    """Toggle course completion status with enhanced level management"""
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
    
    user_id = user['id']
    completed = request.form.get('completed') == '1'
    
    # Use level manager to handle completion
    result = level_manager.mark_course_completion(user_id, course_id, completed)
    
    if result['success']:
        flash(result['message'], 'success')
        
        # Show level progression information if level changed
        if result.get('points_change', 0) != 0:
            points_msg = f"Points: {'+'  if result['points_change'] > 0 else ''}{result['points_change']}"
            flash(f"{points_msg} | Level: {result['new_level']} ({result['level_points']} at level)", 'info')
        
        # Update session level if it changed
        if 'user_level' in session and session['user_level'] != result['new_level']:
            session['user_level'] = result['new_level']
    else:
        flash(result['message'], 'error')
    
    return redirect(url_for('dashboard.my_courses'))

@dashboard_bp.route('/level_info')
def level_info():
    """Get current user's level information as JSON"""
    user = get_current_user()
    if not user:
        return {'error': 'Not authenticated'}, 401
    
    level_info = level_manager.get_user_level_info(user['id'])
    return level_info

@dashboard_bp.route('/points_log')
def points_log():
    """View user's points transaction history"""
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
    
    user_id = user['id']
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get points log with pagination
    points_log = level_manager.get_user_points_log(user_id, limit=per_page * page)
    level_info = level_manager.get_user_level_info(user_id)
    
    return render_template('dashboard/points_log.html',
                         points_log=points_log,
                         level_info=level_info,
                         page=page)
