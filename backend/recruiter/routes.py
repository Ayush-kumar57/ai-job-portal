from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from db import recruiters, jobs
from utils import role_required

recruiter_bp = Blueprint('recruiter', __name__, url_prefix='/recruiter')


def my_id():
    return session['user_id']


def to_oid(id):
    """URL wala text id -> MongoDB ObjectId. Galat id ho toh None."""
    try:
        return ObjectId(id)
    except InvalidId:
        return None


@recruiter_bp.route('/dashboard')
@role_required('recruiter')
def dashboard():
    job_count = jobs.count_documents({'recruiter_id': my_id()})
    open_count = jobs.count_documents({'recruiter_id': my_id(), 'status': 'open'})
    profile = recruiters.find_one({'user_id': my_id()})
    return render_template('recruiter/dashboard.html', job_count=job_count,
                           open_count=open_count, profile=profile)


@recruiter_bp.route('/company', methods=['GET', 'POST'])
@role_required('recruiter')
def company():
    if request.method == 'POST':
        recruiters.update_one({'user_id': my_id()}, {'$set': {
            'user_id': my_id(),
            'company_name': request.form['company_name'].strip(),
            'company_website': request.form['company_website'].strip(),
            'about': request.form['about'].strip(),
            'location': request.form['location'].strip()
        }}, upsert=True)
        flash('Company profile saved', 'success')
        return redirect(url_for('recruiter.dashboard'))
    profile = recruiters.find_one({'user_id': my_id()}) or {}
    return render_template('recruiter/company.html', p=profile)


def job_from_form():
    # "Python, Flask , MongoDB" -> ['python', 'flask', 'mongodb']
    skills = [s.strip().lower() for s in request.form['required_skills'].split(',') if s.strip()]
    return {
        'title': request.form['title'].strip(),
        'description': request.form['description'].strip(),
        'required_skills': skills,
        'location': request.form['location'].strip(),
        'job_type': request.form['job_type'],
        'salary_range': request.form['salary_range'].strip(),
    }


@recruiter_bp.route('/jobs/new', methods=['GET', 'POST'])
@role_required('recruiter')
def new_job():
    if request.method == 'POST':
        profile = recruiters.find_one({'user_id': my_id()}) or {}
        job = job_from_form()
        job.update({'recruiter_id': my_id(),
                    'company_name': profile.get('company_name', 'Unknown company'),
                    'status': 'open', 'clean_text': '',
                    'created_at': datetime.now()})
        jobs.insert_one(job)
        flash('Job posted', 'success')
        return redirect(url_for('recruiter.my_jobs'))
    return render_template('recruiter/job_form.html', job={}, mode='new')


@recruiter_bp.route('/jobs')
@role_required('recruiter')
def my_jobs():
    my_jobs = list(jobs.find({'recruiter_id': my_id()}).sort('created_at', -1))
    return render_template('recruiter/jobs.html', jobs=my_jobs)


@recruiter_bp.route('/jobs/<id>/edit', methods=['GET', 'POST'])
@role_required('recruiter')
def edit_job(id):
    oid = to_oid(id)
    job = jobs.find_one({'_id': oid, 'recruiter_id': my_id()}) if oid else None
    if not job:
        flash('Job not found', 'danger')
        return redirect(url_for('recruiter.my_jobs'))
    if request.method == 'POST':
        jobs.update_one({'_id': oid}, {'$set': job_from_form()})
        flash('Job updated', 'success')
        return redirect(url_for('recruiter.my_jobs'))
    return render_template('recruiter/job_form.html', job=job, mode='edit')


@recruiter_bp.route('/jobs/<id>/close', methods=['POST'])
@role_required('recruiter')
def close_job(id):
    oid = to_oid(id)
    if oid:
        jobs.update_one({'_id': oid, 'recruiter_id': my_id()}, {'$set': {'status': 'closed'}})
        flash('Job closed', 'info')
    return redirect(url_for('recruiter.my_jobs'))
