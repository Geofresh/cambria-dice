from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from models import User, db
from functools import wraps
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

auth = Blueprint('auth', __name__)

def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_super_admin:
            flash('Super admin privileges required.')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@auth.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.login'))

    login_user(user, remember=remember)
    return redirect(url_for('index'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@auth.route('/admin/users')
@login_required
@super_admin_required
def manage_users():
    users = User.query.filter(User.id != current_user.id).all()
    return render_template('manage_users.html', users=users)

@auth.route('/admin/users/create', methods=['POST'])
@login_required
@super_admin_required
def create_user():
    username = request.form.get('username')
    password = request.form.get('password')
    is_admin = request.form.get('is_admin') == 'true'

    if not username or not password:
        flash('Username and password are required.')
        return redirect(url_for('auth.manage_users'))

    if User.query.filter_by(username=username).first():
        flash('Username already exists.')
        return redirect(url_for('auth.manage_users'))

    new_user = User(
        username=username,
        is_admin=is_admin,
        is_super_admin=False,
        created_by=current_user.id
    )
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    flash(f'User {username} created successfully.')
    return redirect(url_for('auth.manage_users'))

@auth.route('/admin/users/<int:user_id>/toggle_admin', methods=['POST'])
@login_required
@super_admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.is_super_admin:
        return jsonify({'error': 'Cannot modify super admin status'}), 403
        
    user.is_admin = not user.is_admin
    db.session.commit()
    
    return jsonify({
        'success': True,
        'is_admin': user.is_admin
    })

@auth.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@super_admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.is_super_admin:
        return jsonify({'error': 'Cannot delete super admin'}), 403
        
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'success': True})

def init_admin():
    """Initialize super admin user if it doesn't exist"""
    admin_username = os.getenv('ADMIN_USERNAME', 'admin')
    admin_password = os.getenv('ADMIN_PASSWORD')
    
    if not admin_password:
        raise ValueError("ADMIN_PASSWORD must be set in .env file")
    
    # Check if super admin exists
    admin = User.query.filter_by(username=admin_username).first()
    if not admin:
        admin = User(
            username=admin_username,
            is_admin=True,
            is_super_admin=True
        )
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit() 