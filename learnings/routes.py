from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g
import sqlite3
from datetime import datetime

learnings_bp = Blueprint('learnings', __name__)

def get_db_connection():
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_current_user():
    """Get current user from g object (set by before_request handler)"""
    return getattr(g, 'user', None)

@learnings_bp.route('/learnings')
def index():
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
    
    # Admin users should not see "My Learnings" - redirect to dashboard
    if user['username'] == 'admin':
        flash('Admin users manage global learnings from the admin panel.', 'info')
        return redirect(url_for('dashboard.index'))
    
    user_id = user['id']
    conn = get_db_connection()
    
    # Get user's own entries + global entries
    entries = conn.execute('''
        SELECT *, 
               CASE WHEN is_global = 1 THEN 'Global' ELSE 'Personal' END as entry_type
        FROM learning_entries 
        WHERE user_id = ? OR is_global = 1
        ORDER BY date_added DESC
    ''', (user_id,)).fetchall()
    conn.close()
    
    return render_template('learnings/index.html', entries=entries)

@learnings_bp.route('/learnings/add', methods=['GET', 'POST'])
def add():
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        # Import sanitization function
        from app import sanitize_input
        
        title = sanitize_input(request.form['title'])
        description = sanitize_input(request.form['description'])
        tags = sanitize_input(request.form['tags'])
        custom_date = request.form['custom_date'] if request.form['custom_date'] else None
        user_id = user['id']
        
        # Validate required fields
        if not title or len(title.strip()) == 0:
            flash('Title is required', 'error')
            return render_template('learnings/add.html')
        
        if len(title) > 200:
            flash('Title must be less than 200 characters', 'error')
            return render_template('learnings/add.html')
        
        if description and len(description) > 1000:
            flash('Description must be less than 1000 characters', 'error')
            return render_template('learnings/add.html')
        
        # Check if admin - admin entries are global
        is_global = 1 if user['username'] == 'admin' else 0
        
        if title:
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO learning_entries (user_id, title, description, tags, custom_date, is_global)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, title, description, tags, custom_date, is_global))
            conn.commit()
            conn.close()
            
            if is_global:
                flash('Global learning entry added successfully! Available to all users.', 'success')
            else:
                flash('Learning entry added successfully!', 'success')
            return redirect(url_for('learnings.index'))
        else:
            flash('Title is required', 'error')
    
    return render_template('learnings/add.html')

@learnings_bp.route('/learnings/edit/<int:entry_id>', methods=['GET', 'POST'])
def edit(entry_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
    
    user_id = user['id']
    conn = get_db_connection()
    
    # Get the entry and verify ownership
    entry = conn.execute('''
        SELECT * FROM learning_entries 
        WHERE id = ? AND user_id = ?
    ''', (entry_id, user_id)).fetchone()
    
    if not entry:
        flash('Entry not found or access denied', 'error')
        return redirect(url_for('learnings.index'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        tags = request.form['tags']
        
        if title:
            conn.execute('''
                UPDATE learning_entries 
                SET title = ?, description = ?, tags = ?
                WHERE id = ? AND user_id = ?
            ''', (title, description, tags, entry_id, user_id))
            conn.commit()
            conn.close()
            
            flash('Learning entry updated successfully!', 'success')
            return redirect(url_for('learnings.index'))
        else:
            flash('Title is required', 'error')
    
    conn.close()
    return render_template('learnings/edit.html', entry=entry)

@learnings_bp.route('/learnings/delete/<int:entry_id>', methods=['POST'])
def delete(entry_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
    
    user_id = user['id']
    conn = get_db_connection()
    
    # Verify ownership before deletion
    result = conn.execute('''
        DELETE FROM learning_entries 
        WHERE id = ? AND user_id = ?
    ''', (entry_id, user_id))
    
    if result.rowcount > 0:
        flash('Learning entry deleted successfully!', 'success')
    else:
        flash('Entry not found or access denied', 'error')
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('learnings.index'))
