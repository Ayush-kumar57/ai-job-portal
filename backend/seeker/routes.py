import os
import time
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file
from werkzeug.utils import secure_filename
from pymongo.errors import DuplicateKeyError
from datetime import datetime
import config
from db import job_seekers, jobs, applications, resumes
from utils import role_required, to_oid
from ai.parser import extract_text
from ai.nlp import clean_text, extract_skills
from ai.matcher import final_score
from recommend import recommend_jobs          # Day 8

# Do blueprints: /seeker/... (profile, dashboard, applications) aur /jobs/... (bina prefix)
seeker_bp = Blueprint('seeker', __name__, url_prefix='/seeker')
jobs_bp = Blueprint('jobs', __name__)


def my_id():
    return session['user_id']


@seeker_bp.route('/dashboard')
@role_required('seeker')
def dashboard():
    applied = applications.count_documents({'seeker_id': my_id()})
    shortlisted = applications.count_documents({'seeker_id': my_id(), 'status': 'shortlisted'})
    profile = job_seekers.find_one({'user_id': my_id()})
    top = recommend_jobs(my_id(), limit=3)          # Day 8: top 3 matches (None = resume nahi)
    return render_template('seeker/dashboard.html', applied=applied,
                           shortlisted=shortlisted, profile=profile, top=top)


@seeker_bp.route('/recommended')
@role_required('seeker')
def recommended():
    # Day 8: resume ke hisaab se top 5 open jobs. jobs=None -> "Upload a resume" empty state
    return render_template('seeker/recommended.html', jobs=recommend_jobs(my_id(), limit=5))


@seeker_bp.route('/profile', methods=['GET', 'POST'])
@role_required('seeker')
def profile():
    if request.method == 'POST':
        # "Python, SQL " -> ['python', 'sql'] (Day 7 mein AI isi list se match karega)
        skills = [s.strip().lower() for s in request.form['skills'].split(',') if s.strip()]
        job_seekers.update_one({'user_id': my_id()}, {'$set': {
            'user_id': my_id(),
            'phone': request.form['phone'].strip(),
            'skills': skills,
            'experience_years': float(request.form['experience_years'] or 0),
            'education': request.form['education'].strip(),
            'location': request.form['location'].strip(),
        }}, upsert=True)   # pehli baar: create; agli baar: update
        flash('Profile saved', 'success')
        return redirect(url_for('seeker.dashboard'))
    p = job_seekers.find_one({'user_id': my_id()}) or {}
    return render_template('seeker/profile.html', p=p)


@jobs_bp.route('/jobs')
@role_required('seeker')
def browse():
    q = request.args.get('q', '').strip()          # /jobs?q=python
    query = {'status': 'open'}                      # sirf open jobs dikhao
    if q:
        # title mein q aaye (case ignore) YA skills list mein q ho
        query['$or'] = [{'title': {'$regex': q, '$options': 'i'}},
                        {'required_skills': q.lower()}]
    all_jobs = list(jobs.find(query).sort('created_at', -1))
    return render_template('seeker/jobs.html', jobs=all_jobs, q=q)


@jobs_bp.route('/jobs/<id>')
@role_required('seeker')
def detail(id):
    oid = to_oid(id)
    job = jobs.find_one({'_id': oid}) if oid else None
    if not job:
        flash('Job not found', 'danger')
        return redirect(url_for('jobs.browse'))
    already = applications.find_one({'job_id': id, 'seeker_id': my_id()}) is not None
    # Day 6: resume ki skills vs job ki required skills -> have / missing
    r = current_resume()
    mine = set(r.get('extracted_skills', [])) if r else set()
    have = [sk for sk in job['required_skills'] if sk in mine]
    missing = [sk for sk in job['required_skills'] if sk not in mine]
    score = score_for(job, r)                       # Day 7: None agar resume nahi
    return render_template('seeker/job_detail.html', job=job, already=already,
                           have=have, missing=missing, has_resume=r is not None, score=score)


@jobs_bp.route('/jobs/<id>/apply', methods=['POST'])
@role_required('seeker')
def apply(id):
    oid = to_oid(id)
    job = jobs.find_one({'_id': oid, 'status': 'open'}) if oid else None
    if not job:
        flash('This job is closed or does not exist', 'warning')
        return redirect(url_for('jobs.browse'))
    # Bina resume ke apply nahi (Day 7 mein match score resume text se banega)
    p = job_seekers.find_one({'user_id': my_id()}) or {}
    if not p.get('resume_id'):
        flash('Upload your resume before applying', 'warning')
        return redirect(url_for('seeker.resume'))
    score = score_for(job) or 0                     # Day 7: apply ke waqt ka score save hota hai
    try:
        applications.insert_one({'job_id': id, 'seeker_id': my_id(), 'resume_id': p['resume_id'],
                                 'status': 'applied', 'match_score': score,
                                 'applied_at': datetime.now()})
        flash('Applied successfully', 'success')
    except DuplicateKeyError:
        # unique index (job_id, seeker_id) ne dusri entry rok di
        flash('You already applied to this job', 'warning')
    return redirect(url_for('jobs.detail', id=id))


@seeker_bp.route('/applications')
@role_required('seeker')
def my_applications():
    apps = list(applications.find({'seeker_id': my_id()}).sort('applied_at', -1))
    # MongoDB mein JOIN nahi hota, isliye har application ke liye job alag se uthate hain
    for a in apps:
        a['job'] = jobs.find_one({'_id': to_oid(a['job_id'])}) or {}
    return render_template('seeker/applications.html', apps=apps)


# ---------- Resume upload (Day 5) ----------

def allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXT


def current_resume():
    """Seeker ka latest resume document (ya None)."""
    p = job_seekers.find_one({'user_id': my_id()}) or {}
    return resumes.find_one({'_id': to_oid(p['resume_id'])}) if p.get('resume_id') else None


def score_for(job, r=None):
    """Logged-in seeker ke resume ka is job se match (0-100). Resume nahi -> None."""
    r = r or current_resume()
    if not r:
        return None
    return final_score(r.get('clean_text', ''), job.get('clean_text', ''),
                       r.get('extracted_skills', []), job.get('required_skills', []))


@seeker_bp.route('/resume', methods=['GET', 'POST'])
@role_required('seeker')
def resume():
    if request.method == 'POST':
        f = request.files.get('resume')           # form mein enctype="multipart/form-data" zaroori
        if not f or f.filename == '':
            flash('Choose a file first', 'warning')
            return redirect(url_for('seeker.resume'))
        if not allowed(f.filename):
            flash('Only PDF or DOCX allowed', 'danger')
            return redirect(url_for('seeker.resume'))

        # Size check disk pe likhne se PEHLE: stream ke end tak jao, position = size, wapas start pe aao
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(0)
        if size > config.MAX_FILE_MB * 1024 * 1024:
            flash(f'File too large (max {config.MAX_FILE_MB} MB)', 'danger')
            return redirect(url_for('seeker.resume'))

        ext = f.filename.rsplit('.', 1)[1].lower()
        os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
        saved_name = f"{my_id()}_{int(time.time())}.{ext}"      # unique, safe naam (user ka naam nahi)
        path = os.path.join(config.UPLOAD_FOLDER, saved_name)
        f.save(path)

        text = extract_text(path)
        if len(text) < 50:
            os.remove(path)                        # bekaar file mat rakho
            flash('Could not read text from this file. Upload a text PDF, not a scanned image.', 'danger')
            return redirect(url_for('seeker.resume'))

        result = resumes.insert_one({
            'user_id': my_id(),
            'file_name': secure_filename(f.filename),   # original naam, bas safe banaya
            'file_path': path, 'file_type': ext,
            'raw_text': text,
            'clean_text': clean_text(text),            # Day 6: TF-IDF ke liye saaf text
            'extracted_skills': extract_skills(text),  # Day 6: skills.txt se mili skills
            'uploaded_at': datetime.now()})
        # profile hamesha LATEST resume ki taraf point kare
        job_seekers.update_one({'user_id': my_id()},
                               {'$set': {'user_id': my_id(), 'resume_id': str(result.inserted_id)}},
                               upsert=True)
        flash('Resume uploaded and read successfully', 'success')
        return redirect(url_for('seeker.resume'))
    return render_template('seeker/resume.html', r=current_resume())


@seeker_bp.route('/resume/download')
@role_required('seeker')
def resume_download():
    r = current_resume()
    if not r or not os.path.exists(r['file_path']):
        flash('No resume uploaded yet', 'warning')
        return redirect(url_for('seeker.resume'))
    return send_file(os.path.abspath(r['file_path']), as_attachment=True, download_name=r['file_name'])
