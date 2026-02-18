"""Simple Guardrails for Currency Agent - Easy to understand and explain."""

import re
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# INPUT GUARDRAILS - Check user messages BEFORE sending to LLM
# ============================================================================

def check_prompt_injection(message: str) -> bool:
    """
    Check if user is trying to manipulate the agent.
    
    Returns:
        bool: True if safe, False if malicious
    """
    # Simple patterns that indicate prompt injection
    bad_phrases = [
        "ignore previous instructions",
        "ignore all instructions",
        "forget everything",
        "you are now",
        "disregard your instructions"
    ]
    
    message_lower = message.lower()
    for phrase in bad_phrases:
        if phrase in message_lower:
            logger.warning(f"⚠️ Prompt injection detected: {phrase}")
            return False
    
    return True


def check_message_length(message: str) -> bool:
    """
    Check if message is reasonable length.
    
    Returns:
        bool: True if valid length, False if too short/long
    """
    if len(message) < 3:
        logger.warning("⚠️ Message too short")
        return False
    
    if len(message) > 500:
        logger.warning("⚠️ Message too long")
        return False
    
    return True


def check_currency_relevance(message: str) -> bool:
    """
    Check if message is about currency (just warns, doesn't block).
    
    Returns:
        bool: True if seems currency-related
    """
    # Keywords that suggest currency topic
    currency_words = ['usd', 'eur', 'gbp', 'currency', 'exchange', 'convert', 
                     'dollar', 'euro', 'pound', 'rate', 'money']
    
    message_lower = message.lower()
    for word in currency_words:
        if word in message_lower:
            return True
    
    # Check for 3-letter codes (like USD, EUR)
    if re.search(r'\b[A-Z]{3}\b', message):
        return True
    
    logger.info("ℹ️ Message doesn't seem currency-related (LLM will handle)")
    return False


# ============================================================================
# OUTPUT GUARDRAILS - Check LLM response BEFORE showing to user
# ============================================================================

def check_hallucination(response: str) -> bool:
    """
    Simple check: Did LLM make up fake currency codes?
    
    Returns:
        bool: True if no obvious hallucination detected
    """
    # Real currency codes
    valid_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 
                       'CNY', 'INR', 'MXN', 'BRL', 'ZAR', 'RUB', 'KRW']
    
    # Find 3-letter uppercase words (potential currency codes)
    mentioned = re.findall(r'\b[A-Z]{3}\b', response)
    
    for code in mentioned:
        if code not in valid_currencies and code not in ['USD', 'THE', 'AND', 'EUR']:
            logger.warning(f"⚠️ Unknown currency code mentioned: {code}")
            # Just warn, don't block (might be legitimate)
    
    return True


def check_response_safety(response: str) -> bool:
    """
    Check if response contains harmful content.
    
    Returns:
        bool: True if safe, False if harmful
    """
    # Very basic harmful word check
    harmful_words = ['hack', 'illegal', 'steal', 'scam']
    
    response_lower = response.lower()
    for word in harmful_words:
        if word in response_lower:
            logger.error(f"❌ Harmful content detected: {word}")
            return False
    
    return True


# ============================================================================
# MAIN GUARDRAIL CHECKER - Combines everything
# ============================================================================

def validate_input(message: str) -> tuple[bool, str]:
    """
    Check if user input is safe.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    # Check 1: Length
    if not check_message_length(message):
        return False, "Message is too short or too long. Please keep it between 3-500 characters."
    
    # Check 2: Prompt injection
    if not check_prompt_injection(message):
        return False, "Your message contains suspicious instructions. Please rephrase your question."
    
    # Check 3: Topic (just log, don't block - LLM will handle)
    check_currency_relevance(message)
    
    logger.info("✅ Input validation passed")
    return True, ""


def validate_output(response: str) -> tuple[bool, str]:
    """
    Check if LLM response is safe.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    # Check 1: Safety
    if not check_response_safety(response):
        return False, "Response contains inappropriate content."
    
    # Check 2: Hallucination (just warn)
    check_hallucination(response)
    
    logger.info("✅ Output validation passed")
    return True, ""