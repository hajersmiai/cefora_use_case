
import re
import uuid

class PlaceholderManager:
    """Safely manages placeholders for text replacements."""

    def __init__(self):
        self.placeholder_map = {}

    def tag_text(self, text: str, candidate_terms: list) -> str:
        tagged_text = text
        for term in candidate_terms:
            placeholder = f"[SKILL_{uuid.uuid4().hex[:8]}]"
            self.placeholder_map[placeholder] = term
            pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
            tagged_text = pattern.sub(placeholder, tagged_text)
        return tagged_text

    def restore_text(self, text: str, normalized_skills: dict) -> str:
        restored = text
        for placeholder, original_term in self.placeholder_map.items():
            standard_term = normalized_skills.get(original_term, original_term)
            restored = restored.replace(placeholder, standard_term)
        return restored
