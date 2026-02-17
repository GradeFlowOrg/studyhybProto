from __future__ import annotations
from datetime import datetime

from sqlalchemy import CheckConstraint
from DataBase.db_ext import db


class TestSubmission(db.Model):
    __tablename__ = "test_submissions"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    topic = db.Column(db.String(120), nullable=False)
    notes = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    student = db.relationship("User", back_populates="test_submissions")

    __table_args__ = (
        CheckConstraint("length(title) >= 3", name="ck_submission_title_length"),
        CheckConstraint("length(topic) >= 2", name="ck_submission_topic_length"),
    )
