from __future__ import annotations

import datetime as dt

from sqlalchemy import select

from app.data.database import SessionLocal
from app.data.models import FocusSession


class FocusRepository:
    def start_session(self, profile_id):
        with SessionLocal() as session:
            focus_session = FocusSession(profile_id=profile_id, started_at=dt.datetime.utcnow())
            session.add(focus_session)
            session.commit()
            session.refresh(focus_session)
            return focus_session

    def stop_session(self, session_id):
        with SessionLocal() as db_session:
            focus_session = db_session.get(FocusSession, session_id)
            if focus_session is None:
                return None
            focus_session.ended_at = dt.datetime.utcnow()
            elapsed = (focus_session.ended_at - focus_session.started_at).total_seconds()
            focus_session.duration_seconds = int(elapsed)
            db_session.commit()
            db_session.refresh(focus_session)
            return focus_session

    def discard_session(self, session_id):
        with SessionLocal() as session:
            focus_session = session.get(FocusSession, session_id)
            if focus_session:
                session.delete(focus_session)
                session.commit()

    def get_total_seconds_this_month(self, profile_id):
        today = dt.date.today()
        month_start = dt.datetime(today.year, today.month, 1)
        with SessionLocal() as session:
            stmt = select(FocusSession).where(
                FocusSession.profile_id == profile_id,
                FocusSession.started_at >= month_start,
                FocusSession.ended_at.is_not(None),
            )
            sessions = session.scalars(stmt).all()
            return sum(s.duration_seconds for s in sessions)
