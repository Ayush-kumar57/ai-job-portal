import os
import sys
from flask import Flask, render_template
import config

# ai/ package project root mein hai (backend/ ke bahar), isliye root ko Python ke search path mein jodte hain
sys.path.insert(0, config.BASE_DIR)
from db import db, jobs, users
from auth.routes import auth_bp
from seeker.routes import seeker_bp, jobs_bp
from recruiter.routes import recruiter_bp
from admin.routes import admin_bp

# HTML aur CSS frontend/ folder mein hain, isliye Flask ko unka rasta batate hain
FRONTEND_DIR = os.path.join(config.BASE_DIR, 'frontend')

app = Flask(__name__,
            template_folder=os.path.join(FRONTEND_DIR, 'templates'),
            static_folder=os.path.join(FRONTEND_DIR, 'static'))
app.config.from_object(config)

# Har role ke routes alag file (blueprint) mein hain, yahan sabko jodte hain
app.register_blueprint(auth_bp)
app.register_blueprint(seeker_bp)
app.register_blueprint(jobs_bp)      # /jobs, /jobs/<id>, /jobs/<id>/apply
app.register_blueprint(recruiter_bp)
app.register_blueprint(admin_bp)


@app.route('/')
def index():
    # Front page pe live numbers dikhane ke liye
    stats = {
        'open_jobs': jobs.count_documents({'status': 'open'}),
        'seekers': users.count_documents({'role': 'seeker'}),
        'recruiters': users.count_documents({'role': 'recruiter'}),
    }
    return render_template('index.html', stats=stats)


@app.route('/db-test')
def db_test():
    db['test'].insert_one({'msg': 'hello from flask'})
    count = db['test'].count_documents({})
    return f'MongoDB connected. Test records: {count}'


if __name__ == '__main__':
    app.run(debug=True)
