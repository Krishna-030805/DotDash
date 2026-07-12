"""Firebase storage back-end for the DotDash Recovery Module."""
from __future__ import annotations
from typing import List, Optional
from datetime import datetime

from .models import RecoveryProfile, RecoverySession, RecoveryQuestion, QuestionType, SessionStatus
from .storage import AbstractStorage

# Import the existing initialized db from firebase_enhanced
from firebase_enhanced import db

class FirebaseStorage(AbstractStorage):
    """Firestore-backed storage implementation."""
    
    def __init__(self):
        self.profiles_ref = db.collection("recovery_profiles")
        self.sessions_ref = db.collection("recovery_sessions")

    # ── Profile persistence ─────────────────────────────────────────────
    def save_profile(self, profile: RecoveryProfile) -> None:
        data = {
            "user_id": profile.user_id,
            "questions": [
                {
                    "question_id": q.question_id,
                    "prompt": q.prompt,
                    "question_type": q.question_type.name,
                    "options": q.options
                } for q in profile.questions
            ],
            "answer_hashes": list(profile.answer_hashes),
            "created_at": profile.created_at.isoformat(),
            "updated_at": profile.updated_at.isoformat() if profile.updated_at else None
        }
        self.profiles_ref.document(profile.user_id).set(data)

    def get_profile(self, user_id: str) -> Optional[RecoveryProfile]:
        doc = self.profiles_ref.document(user_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        questions = [
            RecoveryQuestion(
                question_id=q["question_id"],
                prompt=q["prompt"],
                question_type=QuestionType[q["question_type"]],
                options=tuple(q["options"]) if q.get("options") else None
            ) for q in data["questions"]
        ]
        return RecoveryProfile(
            user_id=data["user_id"],
            questions=tuple(questions),
            answer_hashes=tuple(data["answer_hashes"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        )

    def delete_profile(self, user_id: str) -> None:
        self.profiles_ref.document(user_id).delete()

    # ── Session persistence ─────────────────────────────────────────────
    def save_session(self, session: RecoverySession) -> None:
        data = {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "selected_question_ids": list(session.selected_question_ids),
            "status": session.status.name,
            "attempt_count": session.attempt_count,
            "created_at": session.created_at.isoformat(),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None
        }
        self.sessions_ref.document(session.session_id).set(data)

    def get_session(self, session_id: str) -> Optional[RecoverySession]:
        doc = self.sessions_ref.document(session_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        return RecoverySession(
            session_id=data["session_id"],
            user_id=data["user_id"],
            selected_question_ids=tuple(data["selected_question_ids"]),
            status=SessionStatus[data["status"]],
            attempt_count=data["attempt_count"],
            created_at=datetime.fromisoformat(data["created_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
        )

    def delete_session(self, session_id: str) -> None:
        self.sessions_ref.document(session_id).delete()

    def list_sessions_for_user(self, user_id: str) -> List[RecoverySession]:
        docs = self.sessions_ref.where("user_id", "==", user_id).stream()
        sessions = []
        for doc in docs:
            data = doc.to_dict()
            sessions.append(RecoverySession(
                session_id=data["session_id"],
                user_id=data["user_id"],
                selected_question_ids=tuple(data["selected_question_ids"]),
                status=SessionStatus[data["status"]],
                attempt_count=data["attempt_count"],
                created_at=datetime.fromisoformat(data["created_at"]),
                completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
            ))
        return sessions
