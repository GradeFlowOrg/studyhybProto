from __future__ import annotations
from datetime import datetime

from sqlalchemy import CheckConstraint, func
from DataBase.db_ext import db


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

    owner = db.relationship("User", back_populates="groups_led")
    memberships = db.relationship(
        "GroupMembership",
        back_populates="group",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("capacity >= 2", name="ck_group_capacity_min"),
        CheckConstraint("length(name) >= 3", name="ck_group_name_length"),
    )

    @property
    def member_count(self) -> int:
        from DataBase.models.membership import GroupMembership

        return (
            db.session.query(func.count(GroupMembership.id))
            .filter(GroupMembership.group_id == self.id)
            .scalar()
            or 0
        )