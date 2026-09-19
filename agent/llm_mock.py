"""
Mocked LLM boundary for generating rep-facing sales briefs.

The model ranking and sales action are determined before this module
is called. The LLM is only responsible for turning grounded evidence
into concise natural-language guidance.

A deterministic implementation is used so the take-home runs without
API credentials. The prompt, response schema, validation, and fallback
represent how a real LLM integration would be structured.
"""

from dataclasses import dataclass


SYSTEM_PROMPT = """
You are a sales assistant for a B2B workflow software company.

Generate a concise brief for a sales representative using ONLY the
account evidence provided to you.

The sales action has already been determined by deterministic business
logic. Do not change the action and do not invent account information.

Return:
- brief: concise rep-facing explanation
- talk_track: one practical suggested next step
"""


@dataclass
class LLMBrief:
    brief: str
    talk_track: str
    source: str


def build_prompt(context: dict) -> dict:
    """Build the structured payload that would be sent to a real LLM."""
    return {
        "system_prompt": SYSTEM_PROMPT,
        "account": {
            "account_id": context["account_id"],
            "action": context["action"],
            "conversion_probability": context["conversion_probability"],
            "reasons": context["reasons"],
            "next_step": context["next_step"],
        },
    }


def _mock_llm_call(context: dict) -> dict:
    """
    Stand-in for the external LLM call.

    A production implementation would replace only this function with
    an OpenAI/Azure OpenAI/etc. client call.
    """
    reasons = "; ".join(context["reasons"])

    return {
        "brief": (
            f"{context['action']}: {reasons}. "
            f"Suggested next step: {context['next_step']}"
        ),
        "talk_track": context["next_step"],
    }


def validate_response(response: dict) -> bool:
    """Validate the minimum response contract expected from the LLM."""
    if not isinstance(response, dict):
        return False

    if not isinstance(response.get("brief"), str):
        return False

    if not response["brief"].strip():
        return False

    if not isinstance(response.get("talk_track"), str):
        return False

    if not response["talk_track"].strip():
        return False

    return True


def _fallback(context: dict) -> LLMBrief:
    """Deterministic fallback if the LLM call or validation fails."""
    reasons = "; ".join(context["reasons"])

    return LLMBrief(
        brief=(
            f"{context['action']}: {reasons}. "
            f"Suggested next step: {context['next_step']}"
        ),
        talk_track=context["next_step"],
        source="fallback",
    )


def generate_brief(context: dict) -> LLMBrief:
    """
    Public interface for rep-brief generation.

    Builds the prompt, calls the mocked LLM, validates its response,
    and falls back safely if anything fails.
    """
    _ = build_prompt(context)

    try:
        response = _mock_llm_call(context)
    except Exception:
        return _fallback(context)

    if not validate_response(response):
        return _fallback(context)

    return LLMBrief(
        brief=response["brief"],
        talk_track=response["talk_track"],
        source="mock_llm",
    )