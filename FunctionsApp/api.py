from __future__ import annotations

from functools import wraps

from flask import Blueprint, jsonify, request, current_app
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func


from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from DataBase.db_ext import db, login_manager
from DataBase.modules import GroupMembership, User, StudyGroup, TestSubmission

api_bp = Blueprint('api', __name__)

limiter = Limiter(get_remote_address)

def require_json():
    if not request.is_json:
        return _error("JSON body required.", 415)
    return None

def _error(message: str, status: int=400):
    return jsonify({'ok': False, 'error': message}), status

def success(data: dict, status: int=200):
    payload = ({'ok': True})
    if data:
        payload.update(data)
    return jsonify(payload), status

def _field(name:str, lowercase: bool=False) -> str:
    if not request.js_json:
        return ''
    value = str(request.json.get(name,'')).strip()
    return value.lower() if lowercase else value

def _premium_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return _error("Login required.", 401)
        if not current_user.paid_member:
            return _error("Premium membership is required for this action.", 403)
        return view_func(*args, **kwargs)
    return wrapper

@api_bp.post('/auth/register')
@limiter.limit("5 per minute")
def register():

    err = require_json()
    if err:
        return err

    full_name = _field('Full Name')
    email = _field('Email', lowercase=True)
    password = _field('Password')

    if not full_name or not email or not password:
        return _error('full_name, email and password are required.', 400)
    if len(password) < 8:
        return _error('Password must be at least 8 characters long.', 400)
    if User.query.filter_by(email=email).first():
        return _error('Email already exists.', 409)

    user = User(full_name=full_name, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return success({'message': 'Account created successfully.'}, 201)

@api_bp.post('/auth/login')
@limiter.limit("3 per minute")
def login():

    err = require_json()
    if err:
        return err

    email = _field('Email', lowercase=True)
    password = _field('Password')

    if not email or not password:
        return _error('email and password are required.', 400)

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return _error('Invalid email or password.', 401)

    login_user(user)
    return success({'message': 'Login success.'}, 200)

@api_bp.post('/auth/logout')
def logout():

    err = require_json()
    if err:
        return err

    logout_user()
    return success({'message': 'Logout success.'}, 200)

@api_bp.get('/dashboard')
@login_required
def dashboard():
    submissions = TestSubmission.query.filter_by(user_id=current_user.id).all()
    my_groups = StudyGroup.query.filter_by(owner_id=current_user.id).all()
    joined_groups = (
        StudyGroup.query.join(GroupMembership)
        .filter(GroupMembership.user_id==current_user.id)
        .all()
    )

    return success(
        {
            'user': {
                'id': current_user.id,
                'full_name': current_user.full_name,
                'email': current_user.email,
                'paid_member': current_user.paid_member,
            },
            'submissions': [
                {'id': t.id, 'title': t.title, 'topic': t.topic, 'notes': t.notes}
                for t in submissions
            ],
            'groups_created': [
                {'id': g.id, 'name': g.name, 'subject': g.subject}
                for g in my_groups
            ],
            'groups_joined': [
                {'id': i.id, 'name': i.name, 'subject': i.subject}
                for i in joined_groups
            ],
        }
    )

@api_bp.post('/test')
@login_required
def submit_test():

    err = require_json()
    if err:
        return err

    title = _field('title')
    topic = _field('topic')
    notes = _field('notes')

    if not title or not topic or not notes:
        return _error('Title, topic and notes are required.', 400)
    if len(notes) < 10:
        return _error('Notes must be at least 10 characters long.', 400)

    submission = TestSubmission(
        title=title,
        topic=topic,
        notes=notes,
        user_id=current_user.id
    )
    db.session.add(submission)
    db.session.commit()

    return success({'message': 'Submission created successfully.', 'id': submission.id}, 201)

@api_bp.post('/membership/upgrade')
@login_required
def upgrade_membership():

    if not current_app.debug:
        return _error('Not allowed', 400)

    err = require_json()
    if err:
        return err

    current_user.paid_member = True
    db.session.commit()
    return success({'message': 'Membership upgraded successfully.'}, 200)

@api_bp.get('/groups')
def list_groups():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=20, type=int)
    per_page = max(1, min(per_page, 50))  # защита

    pagination = StudyGroup.query.order_by(StudyGroup.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)

    groups = pagination.items

    return success(
        {
            'groups': [
                {
                    'id': g.id,
                    'name': g.name,
                    'subject': g.subject,
                    'tutor_name': g.tutor_name,
                    'description': g.description,
                    'capacity': g.capacity,
                    'member_count': g.member_count,
                    'is_private': g.is_private,
                }
                for g in groups
            ]
        }
    )

@api_bp.get('/groups/<int:group_id>')
def get_group(group_id):
    group = StudyGroup.query.get_or404(group_id)
    return success(
        {
            'group': {
                'id': group.id,
                'name': group.name,
                'subject': group.subject,
                'tutor_name': group.tutor_name,
                'description': group.description,
                'capacity': group.capacity,
                'member_count': group.member_count,
                'is_private': group.is_private,
                'owner': group.owner.full_name,
            }
        }
    )

@api_bp.post("/groups")
@login_required
@_premium_required
def create_group():

    err = require_json()
    if err:
        return err

    name = _field("name")
    subject = _field("subject")
    tutor_name = _field("tutor_name")
    description = _field("description")
    is_private = bool(request.json.get("is_private", False)) if request.is_json else False

    try:
        capacity = int(request.json.get("capacity", 25)) if request.is_json else 25
    except (TypeError, ValueError):
        return _error("capacity must be a number.")

    if not all([name, subject, tutor_name, description]):
        return _error("name, subject, tutor_name and description are required.")
    if capacity < 2:
        return _error("Group capacity should be at least 2.")

    group = StudyGroup(
        name=name,
        subject=subject,
        tutor_name=tutor_name,
        description=description,
        capacity=capacity,
        is_private=is_private,
        owner_id=current_user.id,
    )
    db.session.add(group)
    db.session.commit()

    return success({"message": "Study group created successfully.", "id": group.id}, 201)

@api_bp.post("/groups/<int:group_id>/join")
@login_required
def join_group(group_id: int):

    err = require_json()
    if err:
        return err

    group = StudyGroup.query.get_or_404(group_id)

    existing = GroupMembership.query.filter_by(
        user_id=current_user.id,
        group_id=group.id,
    ).first()
    if existing:
        return _error("You already joined this group.", 409)

    members_now = db.session.query(func.count(GroupMembership.id)).filter(GroupMembership.group_id == group.id).scalar() or 0

    if members_now >= group.capacity:
        return _error("This group has reached full capacity.", 409)

    membership = GroupMembership(user_id=current_user.id, group_id=group.id)
    db.session.add(membership)
    db.session.commit()

    return success({"message": "You successfully joined the study group."}, 201)

@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({"ok": False, "error": "Login required."}), 401