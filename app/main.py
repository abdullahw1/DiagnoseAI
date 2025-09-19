from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models import Case

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@bp.route('/dashboard')
@login_required
def dashboard():
    # Get user's cases for display
    cases = Case.query.filter_by(user_id=current_user.id).order_by(Case.created_at.desc()).all()
    return render_template('main/dashboard.html', title='Dashboard', cases=cases)