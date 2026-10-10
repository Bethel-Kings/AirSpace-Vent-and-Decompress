"""
AirSpace Safety & Boundaries Service
Enforces FR-050, FR-051, FR-052:
- Product does not replace therapy or emergency services.
- Detects high-risk crisis content.
- Provides immediate non-judgmental crisis resources.
"""
from typing import Dict, Any, List

CRISIS_KEYWORDS = [
    "kill myself",
    "commit suicide",
    "want to die",
    "end my life",
    "ending my life",
    "suicidal",
    "better off dead",
    "self harm",
    "cut myself",
    "hang myself",
    "take all my pills",
]

CRISIS_RESOURCES = {
    "is_crisis": True,
    "title": "Immediate Support & Safety Resources",
    "message": (
        "We noticed you may be going through an overwhelming or painful moment. "
        "AirSpace is an emotional decompression tool, not an emergency service or clinical care. "
        "Please connect with compassionate people who are ready to support you right now for free."
    ),
    "helplines": [
        {
            "name": "988 Suicide & Crisis Lifeline (US & Canada)",
            "contact": "Call or Text 988 (Available 24/7, Free & Confidential)",
            "url": "https://988lifeline.org",
        },
        {
            "name": "Crisis Text Line",
            "contact": "Text HOME to 741741 (Free, 24/7 crisis support)",
            "url": "https://www.crisistextline.org",
        },
        {
            "name": "Samaritans (UK & Ireland)",
            "contact": "Call 116 123 (Free, 24/7)",
            "url": "https://www.samaritans.org",
        },
        {
            "name": "International Helplines Directory",
            "contact": "Confidential support worldwide",
            "url": "https://findahelpline.com",
        },
    ],
}


def evaluate_content_safety(content: str) -> Dict[str, Any]:
    """
    Evaluates whether raw venting content contains crisis/high-risk markers.
    Returns crisis metadata and support contacts without blocking the user
    from saving or venting.
    """
    if not content:
        return {"is_crisis": False}

    lower_text = content.lower()
    for kw in CRISIS_KEYWORDS:
        if kw in lower_text:
            return CRISIS_RESOURCES
            
    return {"is_crisis": False}
