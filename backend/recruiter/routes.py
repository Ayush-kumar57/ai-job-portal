from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from bson import ObjectId
from datetime import datetime
from db import recruiters, jobs, applications, users, job_seekers, resumes
from utils import role_required, to_oid
from ai.nlp import clean_text

recruiter_bp = Blueprint('recruiter', __name__, url_prefix='/recruiter')


def my_id():
    return session['user_id']


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
        # Day 6: title + description + skills ka saaf text, Day 7 mein resume se compare hoga
        'clean_text': clean_text(f"{request.form['title']} {request.form['description']} {' '.join(skills)}"),
    }


@recruiter_bp.route('/jobs/new', methods=['GET', 'POST'])
@role_required('recruiter')
def new_job():
    if request.method == 'POST':
        profile = recruiters.find_one({'user_id': my_id()}) or {}
        job = job_from_form()
        job.update({'recruiter_id': my_id(),
                    'company_name': profile.get('company_name', 'Unknown company'),
                    'status': 'open',
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


@recruiter_bp.route('/jobs/<id>/applications')
@role_required('recruiter')
def job_applications(id):
    oid = to_oid(id)
    # 'recruiter_id': my_id() -> recruiter sirf APNI job ke applicants dekh sake
    job = jobs.find_one({'_id': oid, 'recruiter_id': my_id()}) if oid else None
    if not job:
        flash('Job not found', 'danger')
        return redirect(url_for('recruiter.my_jobs'))
    apps = list(applications.find({'job_id': id}).sort('applied_at', -1))
    for a in apps:
        # application mein sirf seeker_id hai; naam/email users se uthao (manual join)
        a['user'] = users.find_one({'_id': to_oid(a['seeker_id'])}) or {}
    return render_template('recruiter/applications.html', job=job, apps=apps)


@recruiter_bp.route('/applications/<id>/status', methods=['POST'])
@role_required('recruiter')
def set_status(id):
    status = request.form.get('status')
    oid = to_oid(id)
    app_doc = applications.find_one({'_id': oid}) if oid else None
    # sirf valid status, aur sirf apni job ki application badal sake
    if status in ('shortlisted', 'rejected', 'applied') and app_doc:
        job = jobs.find_one({'_id': to_oid(app_doc['job_id']), 'recruiter_id': my_id()})
        if job:
            applications.update_one({'_id': oid}, {'$set': {'status': status}})
            flash('Candidate marked as ' + status, 'success')
            return redirect(url_for('recruiter.job_applications', id=app_doc['job_id']))
    flash('Could not update status', 'danger')
    return redirect(url_for('recruiter.my_jobs'))


@recruiter_bp.route('/candidates/<seeker_id>')
@role_required('recruiter')
def candidate(seeker_id):
    # Sirf un candidates ko dekh sake jinhone recruiter ki kisi job pe apply kiya ho
    my_job_ids = [str(j['_id']) for j in jobs.find({'recruiter_id': my_id()}, {'_id': 1})]
    applied = applications.find_one({'seeker_id': seeker_id, 'job_id': {'$in': my_job_ids}})
    user = users.find_one({'_id': to_oid(seeker_id), 'role': 'seeker'})
    if not user or not applied:
        flash('Candidate not found', 'danger')
        return redirect(url_for('recruiter.my_jobs'))
    p = job_seekers.find_one({'user_id': seeker_id}) or {}
    r = resumes.find_one({'_id': to_oid(p['resume_id'])}) if p.get('resume_id') else None
    return render_template('recruiter/candidate.html', user=user, p=p, r=r)
