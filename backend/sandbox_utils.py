import json
import re

def parse_agent_action(action_text: str):
    """
    Parses the raw LLM output text to determine a simple 'emotion' and simplified 'status' text
    for the sandbox view based on keywords.
    """
    text_lower = action_text.lower()
    
    # Very basic entity/intent extraction
    emotion = "💬" # Default: speaking / active
    current_action = "Wandering"
    target_location = None # None means just wander randomly
    
    if any(word in text_lower for word in ["sleep", "rest", "night", "tired"]):
        emotion = "💤"
        current_action = "Resting"
    elif any(word in text_lower for word in ["think", "ponder", "wonder", "reflect"]):
        emotion = "🤔"
        current_action = "Thinking"
    elif any(word in text_lower for word in ["discover", "found", "aha", "idea"]):
        emotion = "💡"
        current_action = "Discovering"
    elif any(word in text_lower for word in ["talk", "discuss", "speak", "ask", "say"]):
        emotion = "💬"
        current_action = "Conversing"
    elif any(word in text_lower for word in ["confused", "lost", "don't know", "what"]):
        emotion = "❓"
        current_action = "Confused"
        
    # Extract maybe a short quote for the speech bubble (first sentence)
    speech_bubble = action_text.split('.')[0] + "..." if len(action_text) > 20 else action_text

    return {
        "emotion": emotion,
        "action": current_action,
        "speech": speech_bubble
    }
