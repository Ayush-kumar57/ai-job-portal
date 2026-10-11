from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from db import users

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        if users.find_one({'email': email}):
            flash('Email already registered', 'danger')
            return redirect(url_for('auth.register'))
        role = request.form['role']
        if role not in ('seeker', 'recruiter'):   # admin form se nahi ban sakta
            flash('Invalid role', 'danger')
            return redirect(url_for('auth.register'))
        users.insert_one({
            'name': request.form['name'].strip(),
            'email': email,
            'password_hash': generate_password_hash(request.form['password']),
            'role': role,
            'created_at': datetime.now()
        })
        flash('Account created. Please login.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        user = users.find_one({'email': email})
        if user and check_password_hash(user['password_hash'], request.form['password']):
            session['user_id'] = str(user['_id'])
            session['name'] = user['name']
            session['role'] = user['role']
            return redirect(url_for(user['role'] + '.dashboard'))
        flash('Wrong email or password', 'danger')
    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'info')
    return redirect(url_for('index'))


@auth_bp.route('/forgot-password')
def forgot():
    return render_template('auth/forgot.html')
