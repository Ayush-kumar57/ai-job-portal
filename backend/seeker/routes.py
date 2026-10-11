from flask import Blueprint, render_template
from utils import role_required

seeker_bp = Blueprint('seeker', __name__, url_prefix='/seeker')


@seeker_bp.route('/dashboard')
@role_required('seeker')
def dashboard():
    return render_template('seeker/dashboard.html')
