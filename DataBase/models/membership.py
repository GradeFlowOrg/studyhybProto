from __future__ import annotations
from datetime import datetime

from sqlalchemy import UniqueConstraint
from DataBase.db_ext import db


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
