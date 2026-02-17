from __future__ import annotations
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from DataBase.db_ext import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    paid_member = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    role = db.Column(db.String(20), nullable=False, default="student")  # student / teacher

    test_submissions = db.relationship(
        "TestSubmission",
        back_populates="student",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    memberships = db.relationship(
        "GroupMembership",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    groups_led = db.relationship(
        "StudyGroup",
        back_populates="owner",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    @property
    def is_teacher(self) -> bool:
        return self.role == "teacher"

    @property
    def is_student(self) -> bool:
        return self.role == "student"

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(
            password, method="pbkdf2:sha256", salt_length=16
        )

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
