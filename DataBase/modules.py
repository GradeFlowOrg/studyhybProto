from datetime import datetime

from sqlalchemy import func

from flask_login import UserMixin
from sqlalchemy import CheckConstraint, UniqueConstraint
from werkzeug.security import check_password_hash, generate_password_hash

from DataBase.db_ext import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    group_id = db.Column(db.Integer, db.ForeignKey("study_groups.id"), nullable=False, index=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    paid_member = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    test_submissions = db.relationship("TestSubmission", backref="student", lazy="selectin",
                                       cascade="all, delete-orphan")

    groups_led = db.relationship(
        "StudyGroup", backref="owner", lazy=True, cascade="all, delete-orphan"
    )
    memberships = db.relationship(
        "GroupMembership", back_populates="user", lazy=True, cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

class TestSubmission(db.Model):
    __tablename__ = 'test_submissions'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    topic = db.Column(db.String(120), nullable=False)
    notes = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    __table_args__ = (
        CheckConstraint("length(title) >= 3", name="ck_submission_title_length"),
        CheckConstraint("length(topic) >= 2", name="ck_submission_topic_length"),
    )
class StudyGroup(db.Model):
    __tablename__ = "study_groups"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(120), nullable=False)
    tutor_name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    capacity = db.Column(db.Integer, nullable=False, default=25)
    is_private = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    memberships = db.relationship(
        "GroupMembership", back_populates="group", lazy=True, cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("capacity >= 2", name="ck_group_capacity_min"),
        CheckConstraint("length(name) >= 3", name="ck_group_name_length"),
    )

@property
def member_count(self) -> int:
    return db.session.query(func.count(GroupMembership.id))\
        .filter(GroupMembership.group_id == self.id)\
        .scalar() or 0

def set_password(self, password: str) -> None:
    self.password_hash = generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)



class GroupMembership(db.Model):
    __tablename__ = "group_memberships"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey("study_groups.id"), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="memberships")
    group = db.relationship("StudyGroup", back_populates="memberships")

    __table_args__ = (
        UniqueConstraint("user_id", "group_id", name="uq_user_group_membership"),
    )