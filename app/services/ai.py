import os
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger("airspace")

SYSTEM_INSTRUCTION_V1 = """
You are AirSpace's Decompress & Reframe Assistant.
Your sole purpose is to help the user decompress after a raw, stream-of-consciousness venting session.

Guidelines:
1. Empathy First: Gently acknowledge and validate what the user is feeling without toxic positivity or judgment.
2. Untangle the Chaos: Help the user organize what feels overwhelming by identifying the primary stressor or underlying emotion.
3. Constructive Reframe: Offer a compassionate, realistic reframe or alternative perspective on the situation.
4. Grounding Next Step: Provide 1-2 immediate, low-effort micro-steps the user can take right now to find clarity and calm.
5. Safety & Boundaries: Do NOT diagnose, label psychiatric conditions, offer clinical therapy, or give medical advice.
Always maintain a grounded, warm, and supportive tone.
Format the output cleanly with clear sections:
- 🌿 **What We Hear** (Validation)
- 💡 **Untangling the Thoughts** (Core Theme)
- 🔄 **A Gentle Reframe** (Constructive Perspective)
- ✨ **One Grounding Step** (Actionable micro-step)
"""


class AIServiceError(Exception):
    """Raised when the AI provider fails or times out."""
    pass


class AIReflectionService:
    def __init__(self):
        self.provider = settings.AI_PROVIDER
        self.api_key = settings.AI_PROVIDER_API_KEY
        self.model_name = settings.AI_MODEL_NAME
        self.prompt_version = settings.AI_PROMPT_VERSION

    def generate_reflection(self, vent_content: str, focus: Optional[str] = None) -> str:
        """
        Sends the user's raw vent to the configured AI provider
        and returns a structured reflection.
        """
        if not vent_content or not vent_content.strip():
            raise ValueError("Venting content cannot be empty.")

        # If provider is mock or API key is not configured in development, use mock generator
        if self.provider == "mock" or not self.api_key:
            return self._generate_mock_reflection(vent_content)

        if self.provider == "gemini":
            return self._call_gemini(vent_content, focus)

        # Fallback to mock if unknown provider
        return self._generate_mock_reflection(vent_content)

    def _call_gemini(self, vent_content: str, focus: Optional[str] = None) -> str:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            prompt = vent_content
            if focus:
                prompt = f"Focus Area: {focus}\n\nUser Venting Entry:\n{vent_content}"

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION_V1,
                    temperature=0.7,
                ),
            )
            if response and response.text:
                return response.text.strip()
            else:
                raise AIServiceError("Empty response returned by AI provider.")
        except Exception as e:
            logger.error("AI Provider execution encountered an error: %s", type(e).__name__)
            raise AIServiceError(f"AI service temporarily unavailable: {str(e)}")

    def _generate_mock_reflection(self, vent_content: str) -> str:
        """Fallback simulated reflection for offline development and automated testing."""
        first_few_words = " ".join(vent_content.split()[:8])
        return (
            "🌿 **What We Hear**\n"
            f"It sounds like a great deal of weight has been accumulating, especially around: \"{first_few_words}...\". "
            "Releasing that onto the page was an essential first step.\n\n"
            "💡 **Untangling the Thoughts**\n"
            "When thoughts remain in our minds, they tend to compound and feel impossible to resolve. "
            "Notice how beneath the frustration or exhaustion is a natural desire for peace, control, and rest.\n\n"
            "🔄 **A Gentle Reframe**\n"
            "You do not have to solve every moving piece of this challenge today. Feeling overwhelmed is not a sign of failure; "
            "it is simply a signal that your capacity has been stretched.\n\n"
            "✨ **One Grounding Step**\n"
            "Take one deep breath, drink a glass of water, and give yourself permission to step away from this problem for the next 20 minutes."
        )


ai_reflection_service = AIReflectionService()
