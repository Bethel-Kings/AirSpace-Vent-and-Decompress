"""
AirSpace MVP — Demo Data Seeder for November 4 Pitch Presentation
Run this script to populate realistic sample data into the database.
"""
import sys
import os
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from datetime import datetime, timedelta, timezone
from app.db.session import SessionLocal, engine, Base
from app.models.user import User
from app.models.session import AirSpaceSession
from app.models.check_in import CheckIn
from app.models.reflection import Reflection
from app.core.security import hash_password


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if demo user already exists
        email = "demo@airspace.me"
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                password_hash=hash_password("AirSpaceDemo2026!"),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Created demo user: {email}")

        # Sample Session 1: Work overload & presentation anxiety
        now = datetime.now(timezone.utc)
        s1 = AirSpaceSession(
            user_id=user.id,
            content=(
                "I have three deadlines colliding this Thursday and my mind feels completely shattered. "
                "I feel like I'm letting my teammates down and no matter how early I wake up, the inbox never stops growing. "
                "I just needed to say this out loud because I've been smiling through every Zoom call pretending everything is fine."
            ),
            created_at=now - timedelta(days=2),
        )
        db.add(s1)
        db.flush()

        db.add(CheckIn(session_id=s1.id, stage="before", value="Overwhelmed (1/5)"))
        db.add(CheckIn(session_id=s1.id, stage="after", value="Clear-Headed (4/5)"))
        db.add(
            Reflection(
                session_id=s1.id,
                content=(
                    "🌿 **What We Hear**\n"
                    "You are carrying an immense load of invisible expectations, and masking that stress on calls is depleting your energy even further. Releasing that mask right here took courage.\n\n"
                    "💡 **Untangling the Thoughts**\n"
                    "The core tension is feeling solely responsible for an impossible volume of work. Responsibility has turned into self-blame.\n\n"
                    "🔄 **A Gentle Reframe**\n"
                    "Having high demands placed on you does not mean you have failed. It means the workload is unbalanced. You are allowed to be human, and communicating boundaries is professional, not a weakness.\n\n"
                    "✨ **One Grounding Step**\n"
                    "Pick just ONE non-essential task from your Thursday list and message the team: 'I'll need to push this to Friday to ensure quality.' Then step away from screens for 15 minutes."
                ),
            )
        )

        # Sample Session 2: Personal reset
        s2 = AirSpaceSession(
            user_id=user.id,
            content=(
                "Felt an unexpected wave of heavy exhaustion today. Nothing catastrophic happened, "
                "just an accumulation of everyday noise and constant connectivity. Taking a pause to reset."
            ),
            created_at=now - timedelta(hours=5),
        )
        db.add(s2)
        db.flush()

        db.add(CheckIn(session_id=s2.id, stage="before", value="Heavy (2/5)"))
        db.add(CheckIn(session_id=s2.id, stage="after", value="Much Calmer (4/5)"))
        db.add(
            Reflection(
                session_id=s2.id,
                content=(
                    "🌿 **What We Hear**\n"
                    "You don't need a crisis to justify feeling tired. Low-grade sensory overload is real and deserves honor.\n\n"
                    "💡 **Untangling the Thoughts**\n"
                    "Your nervous system is simply asking for quiet digestion time.\n\n"
                    "🔄 **A Gentle Reframe**\n"
                    "Rest is not a reward you earn after finishing everything; it is a prerequisite for being well.\n\n"
                    "✨ **One Grounding Step**\n"
                    "Put your phone in 'Do Not Disturb' mode for the next hour and enjoy a warm cup of herbal tea."
                ),
            )
        )

        db.commit()
        print("Successfully seeded demo sessions, reflections, and check-ins!")
        print("Demo Credentials -> Email: demo@airspace.me | Password: AirSpaceDemo2026!")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
