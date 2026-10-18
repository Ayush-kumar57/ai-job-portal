import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import users, job_seekers, recruiters, jobs, resumes, applications
from utils import role_required, to_oid

# Day 9: admin = sirf Read + Delete, par SAARI collections pe (koi user_id filter nahi)
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard')
@role_required('admin')
def dashboard():
    # 5 counts: ye numbers MongoDB Compass ke counts se match hone chahiye
    s = {
        'users': users.count_documents({}),
        'seekers': users.count_documents({'role': 'seeker'}),
        'recruiters': users.count_documents({'role': 'recruiter'}),
        'jobs': jobs.count_documents({}),
        'applications': applications.count_documents({}),
    }
    latest_users = list(users.find({}, {'name': 1, 'email': 1, 'role': 1, 'created_at': 1})
                        .sort('created_at', -1).limit(5))
    latest_apps = list(applications.find().sort('applied_at', -1).limit(5))
    attach_job_and_user(latest_apps)
    return render_template('admin/dashboard.html', s=s, latest_users=latest_users, latest_apps=latest_apps)


# ---------- Users ----------

@admin_bp.route('/users')
@role_required('admin')
def manage_users():
    q = request.args.get('q', '').strip()
    role = request.args.get('role', '').strip()          # ?role=seeker filter (optional)
    query = {}
    if q:
        # naam YA email mein q aaye (case ignore) - Day 4 wali search jaisa
        query['$or'] = [{'name': {'$regex': q, '$options': 'i'}},
                        {'email': {'$regex': q, '$options': 'i'}}]
    if role in ('seeker', 'recruiter', 'admin'):
        query['role'] = role
    rows = list(users.find(query).sort('created_at', -1))
    return render_template('admin/users.html', users=rows, q=q, role=role)


def delete_user_everything(uid):
    """Cascade delete: user ke saath uska profile, resumes (file bhi), applications aur jobs.
    Ek hi function mein, warna site pe toote hue rows dikhte hain ('(deleted user)')."""
    # 1. resume files disk se hatao, phir records
    for r in resumes.find({'user_id': uid}, {'file_path': 1}):
        remove_file(r.get('file_path'))
    resumes.delete_many({'user_id': uid})
    # 2. seeker side: profile + jo applications usne ki
    job_seekers.delete_many({'user_id': uid})
    applications.delete_many({'seeker_id': uid})
    # 3. recruiter side: company profile + uski jobs + un jobs pe aayi applications
    recruiters.delete_many({'user_id': uid})
    job_ids = [str(j['_id']) for j in jobs.find({'recruiter_id': uid}, {'_id': 1})]
    if job_ids:
        applications.delete_many({'job_id': {'$in': job_ids}})
    jobs.delete_many({'recruiter_id': uid})
    # 4. aakhir mein user khud
    users.delete_one({'_id': to_oid(uid)})


@admin_bp.route('/users/<id>/delete', methods=['POST'])
@role_required('admin')
def delete_user(id):
    u = users.find_one({'_id': to_oid(id)}) if to_oid(id) else None
    if not u:
        flash('User not found', 'danger')
    elif u['role'] == 'admin':
        flash('Admin account cannot be deleted', 'danger')      # end-of-day check: admin delete nahi hota
    else:
        delete_user_everything(id)
        flash(f"{u['name']} and all their data deleted", 'info')
    return redirect(url_for('admin.manage_users', q=request.args.get('q', ''), role=request.args.get('role', '')))


# ---------- Recruiters ----------

@admin_bp.route('/recruiters')
@role_required('admin')
def manage_recruiters():
    profiles = list(recruiters.find())
    # batch lookup (Day 8 wala tareeka): N find_one ki jagah ek $in query
    user_map = {str(u['_id']): u for u in users.find(
        {'_id': {'$in': [to_oid(p['user_id']) for p in profiles]}})}
    rows = []
    for p in profiles:
        u = user_map.get(p['user_id'], {})
        rows.append({'user_id': p['user_id'], 'company': p.get('company_name'),
                     'location': p.get('location'), 'website': p.get('company_website'),
                     'name': u.get('name'), 'email': u.get('email'),
                     'jobs': jobs.count_documents({'recruiter_id': p['user_id']}),
                     'open': jobs.count_documents({'recruiter_id': p['user_id'], 'status': 'open'})})
    rows.sort(key=lambda r: r['jobs'], reverse=True)
    # recruiter accounts jinhone abhi company profile nahi bhara (table ke neeche dikhate hain)
    without_profile = list(users.find({'role': 'recruiter', '_id': {'$nin': [to_oid(p['user_id']) for p in profiles]}}))
    return render_template('admin/recruiters.html', rows=rows, without_profile=without_profile)


# ---------- Jobs ----------

@admin_bp.route('/jobs')
@role_required('admin')
def manage_jobs():
    status = request.args.get('status', '').strip()        # ?status=open / closed
    query = {'status': status} if status in ('open', 'closed') else {}
    rows = list(jobs.find(query).sort('created_at', -1))
    for j in rows:
        j['apps'] = applications.count_documents({'job_id': str(j['_id'])})
    return render_template('admin/jobs.html', jobs=rows, status=status)


@admin_bp.route('/jobs/<id>/delete', methods=['POST'])
@role_required('admin')
def delete_job(id):
    job = jobs.find_one({'_id': to_oid(id)}) if to_oid(id) else None
    if job:
        n = applications.delete_many({'job_id': id}).deleted_count   # pehle uski applications
        jobs.delete_one({'_id': job['_id']})
        flash(f"Job '{job['title']}' deleted along with {n} application(s)", 'info')
    else:
        flash('Job not found', 'danger')
    return redirect(url_for('admin.manage_jobs', status=request.args.get('status', '')))


# ---------- Applications ----------

def attach_job_and_user(apps):
    """Har application pe a['job'] aur a['user'] laga do (batch $in lookup, loop mein find_one nahi)."""
    if not apps:
        return apps
    job_map = {str(j['_id']): j for j in jobs.find(
        {'_id': {'$in': [to_oid(a['job_id']) for a in apps]}}, {'title': 1, 'company_name': 1, 'status': 1})}
    user_map = {str(u['_id']): u for u in users.find(
        {'_id': {'$in': [to_oid(a['seeker_id']) for a in apps]}}, {'name': 1, 'email': 1})}
    for a in apps:
        a['job'] = job_map.get(a['job_id'], {})       # {} = job delete ho chuki (template '(job removed)' dikhata hai)
        a['user'] = user_map.get(a['seeker_id'], {})
    return apps


@admin_bp.route('/applications')
@role_required('admin')
def manage_applications():
    status = request.args.get('status', '').strip()
    query = {'status': status} if status in ('applied', 'shortlisted', 'rejected') else {}
    rows = attach_job_and_user(list(applications.find(query).sort('applied_at', -1)))
    return render_template('admin/applications.html', apps=rows, status=status)


@admin_bp.route('/applications/<id>/delete', methods=['POST'])
@role_required('admin')
def delete_application(id):
    result = applications.delete_one({'_id': to_oid(id)}) if to_oid(id) else None
    if result and result.deleted_count:
        flash('Application deleted', 'info')
    else:
        flash('Application not found', 'danger')
    return redirect(url_for('admin.manage_applications', status=request.args.get('status', '')))


def remove_file(path):
    """Disk se file hatao; file pehle se gayab ho toh chup-chaap aage badho."""
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError:
        pass
