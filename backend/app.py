import os
import sys
from flask import Flask, render_template, request, jsonify
import config

# ai/ package project root mein hai (backend/ ke bahar), isliye root ko Python ke search path mein jodte hain
sys.path.insert(0, config.BASE_DIR)
from db import db, jobs, users
from auth.routes import auth_bp
from seeker.routes import seeker_bp, jobs_bp
from recruiter.routes import recruiter_bp
from admin.routes import admin_bp
from ai.nlp import clean_text, extract_skills
from ai.matcher import final_score

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


@app.route('/api/score', methods=['POST'])
def api_score():
    # Demo / Postman ke liye: JSON {"resume": "...", "job": "..."} -> {"score": 72.5, ...}
    d = request.get_json(silent=True) or {}
    resume, job = d.get('resume', ''), d.get('job', '')
    if not resume or not job:
        return jsonify({'error': 'send JSON with "resume" and "job" text'}), 400
    rs, js = extract_skills(resume), extract_skills(job)
    score = final_score(clean_text(resume), clean_text(job), rs, js)
    return jsonify({'score': score, 'resume_skills': rs, 'job_skills': js})


@app.route('/db-test')
def db_test():
    db['test'].insert_one({'msg': 'hello from flask'})
    count = db['test'].count_documents({})
    return f'MongoDB connected. Test records: {count}'


if __name__ == '__main__':
    app.run(debug=True)
