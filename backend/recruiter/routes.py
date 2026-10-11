from flask import Blueprint, render_template
from utils import role_required

recruiter_bp = Blueprint('recruiter', __name__, url_prefix='/recruiter')


@recruiter_bp.route('/dashboard')
@role_required('recruiter')
def dashboard():
    return render_template('recruiter/dashboard.html')
