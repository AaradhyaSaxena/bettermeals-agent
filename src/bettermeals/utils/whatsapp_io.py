def to_user_text(plan_or_status: dict) -> str:
    """Map internal api_result into a concise WhatsApp-safe message string."""
    # Keep messages short; prefer bullets; avoid jargon
    return str(plan_or_status)[:1000]
