from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from pymongo.errors import DuplicateKeyError
from datetime import datetime
from db import job_seekers, jobs, applications
from utils import role_required, to_oid

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
    return render_template('seeker/dashboard.html', applied=applied,
                           shortlisted=shortlisted, profile=profile)


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
    return render_template('seeker/job_detail.html', job=job, already=already)


@jobs_bp.route('/jobs/<id>/apply', methods=['POST'])
@role_required('seeker')
def apply(id):
    oid = to_oid(id)
    job = jobs.find_one({'_id': oid, 'status': 'open'}) if oid else None
    if not job:
        flash('This job is closed or does not exist', 'warning')
        return redirect(url_for('jobs.browse'))
    try:
        applications.insert_one({'job_id': id, 'seeker_id': my_id(), 'resume_id': '',
                                 'status': 'applied', 'match_score': 0,
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
