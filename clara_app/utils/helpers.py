import hashlib
import datetime
import random
from zoneinfo import ZoneInfo
from clara_app.constants import USER_ID_SALT

def normalize_email(email: str) -> str:
    if not isinstance(email, str):
        return ""
    return email.strip().lower()

def is_master_email(email: str) -> bool:
    """Check if the given email belongs to a master/developer account."""
    from clara_app.constants import MASTER_EMAILS, MASTER_DOMAINS
    norm = normalize_email(email)
    if not norm:
        return False
    
    # Check specific emails
    if norm in [e.lower() for e in MASTER_EMAILS]:
        return True
    
    # Check domain suffixes
    if "@" in norm:
        domain = norm.split("@")[-1]
        if domain in [d.lower() for d in MASTER_DOMAINS]:
            return True
            
    return False

def email_to_user_id(email: str) -> str:
    """
    Derive a stable user id from an email login key.
    If USER_ID_SALT is set, it prevents trivial reverse-lookups.
    """
    normalized = normalize_email(email)
    if not normalized:
        return ""
    payload = f"{USER_ID_SALT}|{normalized}" if USER_ID_SALT else normalized
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def user_wants_full_answer(text: str) -> bool:
    if not isinstance(text, str):
        return False
    t = text.lower()
    return any(
        phrase in t
        for phrase in [
            "full answer",
            "complete answer",
            "all the details",
            "everything you know",
            "deep dive",
            "in detail",
            "detailed",
            "long answer",
            "be thorough",
            "expand on that",
            "tell me more",
            "explain in depth",
            "narrative",
            "tell me a story",
            "what's it like",
            "go into detail",
        ]
    )


# Common phrases Clara uses when she's pausing for pacing or conciseness.
TRIM_NUDGES = [
    "(I’m keeping this short. Tap Continue if you want the rest.)",
    "(I’ll pause there—tap Continue to go deeper.)",
    "(This is the ‘short version’. Tap Continue if you want the full picture.)",
    "(I’m summarizing a bit here. Tap Continue to unpack any of that.)",
    "(Tap Continue to keep going...)",
    "(There’s more to this—tap Continue and I'll keep going.)",
]

def trim_response_for_conciseness(text: str, max_chars: int = 700) -> str:
    """
    Keep Clara's replies concise by default.
    If the model returns a long answer, truncate it to a reasonable length
    and encourage the user to ask for more detail if they want it.
    """
    if not isinstance(text, str):
        return ""
    text = text.strip()
    if len(text) <= max_chars:
        return text

    truncated = text[:max_chars]
    # Try to end at a sentence boundary for readability
    last_sentence_end = max(truncated.rfind("."), truncated.rfind("!"), truncated.rfind("?"))
    if last_sentence_end > max_chars * 0.4:
        truncated = truncated[: last_sentence_end + 1]

    truncated = truncated.rstrip()
    
    # "Nudges" to let the user know there is more, without sounding robotic.
    # We check if the text ends consistently with a nudge pattern to avoid doubling up
    # if the model itself generated a pause message.
    msg_lower = truncated.lower().strip()
    if msg_lower.endswith(")") or "continue" in msg_lower[-50:] or "pause" in msg_lower[-50:]:
        return truncated

    return truncated + "\n\n" + random.choice(TRIM_NUDGES)

def should_show_continue_button(text: str) -> bool:
    """
    Determine if we should show a 'Continue' button.
    True if the message was trimmed (ends with a nudge) 
    or if Clara naturally asked if she should keep going.
    """
    if not isinstance(text, str):
        return False
    
    # Check if it ends with one of our conciseness nudges
    if any(nudge in text for nudge in TRIM_NUDGES):
        return True
    
    # Check for natural pacing phrases Clara is instructed to use
    t = text.lower()
    pacing_phrases = [
        "keep going",
        "shall i continue",
        "should i continue",
        "want the rest",
        "more to this",
        "continue the conversation",
        "carry on",
    ]
    return any(phrase in t for phrase in pacing_phrases)

def get_london_now():
    """Current datetime in London, as a timezone-aware object."""
    try:
        return datetime.datetime.now(ZoneInfo("Europe/London"))
    except Exception:
        # Fallback to UTC if zoneinfo is unavailable
        return datetime.datetime.now(datetime.timezone.utc)

def classify_conversation_topic(prompt: str) -> str:
    """
    Very coarse topic classification for aggregate analytics.
    Returns one of a small set of labels without storing any raw text.
    """
    if not isinstance(prompt, str):
        return "other"
    text = prompt.lower()

    if any(word in text for word in ["relationship", "partner", "girlfriend", "boyfriend", "marriage", "breakup", "family", "mum", "dad", "parents", "friend"]):
        return "relationships_family"
    if any(word in text for word in ["anxious", "anxiety", "depressed", "depression", "stressed", "burnout", "lonely", "overwhelmed", "mental health", "therapy"]):
        return "mental_health_emotions"
    if any(word in text for word in ["job", "career", "promotion", "boss", "coworker", "startup", "business", "work", "office"]):
        return "work_career"
    if any(word in text for word in ["money", "finance", "debt", "savings", "investment", "invest", "budget", "tax"]):
        return "money_finance"
    if any(word in text for word in ["health", "doctor", "symptom", "pain", "diet", "exercise", "workout", "sleep", "insomnia"]):
        return "health_body"
    if any(word in text for word in ["write", "writing", "story", "novel", "art", "creative", "song", "music", "paint", "design", "project", "side project"]):
        return "creativity_learning"

    return "other"

def name_to_id(name: str) -> str:
    """
    Sanitize a user's name into a consistent document ID.
    Example: "Max Scott" -> "max_scott"
    """
    if not isinstance(name, str):
        return ""
    return name.strip().lower().replace(" ", "_")
