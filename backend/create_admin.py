# Ek baar chalao: python create_admin.py
from werkzeug.security import generate_password_hash
from datetime import datetime
from db import users

if not users.find_one({'email': 'admin@portal.com'}):
    users.insert_one({'name': 'Admin', 'email': 'admin@portal.com',
                      'password_hash': generate_password_hash('admin123'),
                      'role': 'admin', 'created_at': datetime.now()})
    print('Admin created: admin@portal.com / admin123')
else:
    print('Admin already exists: admin@portal.com')
