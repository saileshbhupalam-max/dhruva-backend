"""WhatsApp Message Templates for Citizen Empowerment.

All messages must be < 1024 characters for WhatsApp.
Supports Telugu (te) and English (en) languages.
"""

from typing import Any, List


# ============================================
# Opt-In Prompt Templates
# ============================================

OPT_IN_PROMPT_TE = """మీ కేసు #{case_id} నమోదు అయింది.
{department} కు పంపబడింది.

మీకు సహాయపడే సమాచారం కావాలా?
(Want helpful information about your rights?)

[1] అవును, నాకు చెప్పండి (Yes, tell me)
[2] వద్దు, ధన్యవాదాలు (No, thanks)
[3] తర్వాత అడగండి (Ask me later)"""

OPT_IN_PROMPT_EN = """Your case #{case_id} has been registered.
Sent to {department}.

Want helpful information about your rights?

[1] Yes, tell me
[2] No, thanks
[3] Ask me later"""


# ============================================
# Rights Message Templates
# ============================================

RIGHTS_LEVEL_1_TE = """మీ హక్కులు (Your Rights):

{rights_list}

మరింత సమాచారం కోసం "MORE" అని రిప్లై చేయండి"""

RIGHTS_LEVEL_1_EN = """Your Rights:

{rights_list}

Reply "MORE" for additional information"""

LEVEL_UP_AVAILABLE_TE = """మరింత సమాచారం అందుబాటులో ఉంది.
[అధికారి వివరాలు చూడండి]"""

LEVEL_UP_AVAILABLE_EN = """More information is available.
[View officer details]"""


# ============================================
# Proactive Trigger Templates
# ============================================

PROACTIVE_SLA_50_TE = """మీ కేసు #{case_id} {days_elapsed} రోజులు అయింది (అనుమతించిన సమయంలో 50%).
స్థితి: {status}

ట్రాకింగ్ సహాయం కావాలా?
[1] చిట్కాలు పంపండి
[2] అధికారిని సంప్రదించండి"""

PROACTIVE_SLA_50_EN = """Your case #{case_id} is {days_elapsed} days old (50% of allowed time).
Status: {status}

Need help tracking?
[1] Send tips
[2] Contact officer"""

PROACTIVE_SLA_APPROACHING_TE = """హెచ్చరిక: మీ కేసు #{case_id} గడువు {days_remaining} రోజుల్లో ఉంది.

పరిష్కారం లేకపోతే auto-escalate అవుతుంది.

ఏదైనా అప్‌డేట్ వచ్చిందా?
[1] అవును
[2] లేదు - escalate చేయండి"""

PROACTIVE_SLA_APPROACHING_EN = """ALERT: Your case #{case_id} deadline is in {days_remaining} days.

If not resolved, it will auto-escalate.

Have you received any update?
[1] Yes
[2] No - please escalate"""

PROACTIVE_NO_UPDATE_TE = """మీ కేసు #{case_id} కు 7 రోజులుగా అప్‌డేట్ లేదు.

మీ హక్కులు తెలుసుకోవాలా?
[1] అవును, చెప్పండి
[2] అధికారిని సంప్రదించాలా"""

PROACTIVE_NO_UPDATE_EN = """Your case #{case_id} has no update in 7 days.

Want to know your rights?
[1] Yes, tell me
[2] Contact officer"""


# ============================================
# Helper Functions
# ============================================


def format_rights_list(rights: List[Any], language: str) -> str:
    """Format rights list for message.

    Args:
        rights: List of right info objects with description and legal_reference
        language: Language code (te/en)

    Returns:
        Formatted string with numbered rights
    """
    lines: List[str] = []
    for i, right in enumerate(rights, 1):
        lines.append(f"{i}. {right.description}")
        if right.legal_reference:
            lines.append(f"   ({right.legal_reference})")
    return "\n".join(lines)


def get_opt_in_prompt(language: str) -> str:
    """Get opt-in prompt template for language."""
    return OPT_IN_PROMPT_TE if language == "te" else OPT_IN_PROMPT_EN


def get_rights_template(language: str) -> str:
    """Get rights message template for language."""
    return RIGHTS_LEVEL_1_TE if language == "te" else RIGHTS_LEVEL_1_EN


def get_proactive_sla_50_template(language: str) -> str:
    """Get SLA 50% proactive template for language."""
    return PROACTIVE_SLA_50_TE if language == "te" else PROACTIVE_SLA_50_EN


def get_proactive_sla_approaching_template(language: str) -> str:
    """Get SLA approaching proactive template for language."""
    return PROACTIVE_SLA_APPROACHING_TE if language == "te" else PROACTIVE_SLA_APPROACHING_EN


def get_proactive_no_update_template(language: str) -> str:
    """Get no update proactive template for language."""
    return PROACTIVE_NO_UPDATE_TE if language == "te" else PROACTIVE_NO_UPDATE_EN
