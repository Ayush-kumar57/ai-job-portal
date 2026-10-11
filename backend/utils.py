from functools import wraps
from flask import session, redirect, url_for, flash


def role_required(role):
    """Chowkidar: route chalne se pehle check karta hai ki login wale ka role sahi hai."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if session.get('role') != role:
                flash('Please login as ' + role, 'warning')
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return wrapper
    return decorator
