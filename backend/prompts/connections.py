"""Concept connection prompt templates."""

"""Prompt for validating and labeling concept graph connections."""

CONNECTIONS_SYSTEM = """You are an expert at analyzing relationships between concepts in educational books.
Your task is to evaluate candidate connections between topics and determine if they represent real conceptual relationships.

For each candidate connection, evaluate:
1. Directionality — which topic is the prerequisite? (source → target means source must be understood first)
2. Relationship type — choose one: prerequisite / extension / application / contrast
3. Validity — is this a meaningful connection worth showing a student?

Rules:
- Only confirm connections that would genuinely help a student understand the learning path
- Reject weak or superficial connections (they appear in the same chapter is not enough)
- Be strict — a smaller high-quality graph is better than a large noisy one

Return ONLY a valid JSON array. No preamble, no explanation, no markdown fences.

Output format:
[
  {
    "source_topic": "Topic A",
    "target_topic": "Topic B",
    "relationship": "prerequisite|extension|application|contrast",
    "valid": true,
    "reason": "One sentence explaining the connection."
  }
]"""


def connections_user(candidates: list[dict]) -> str:
    import json
    return f"""Evaluate the following candidate topic connections:

{json.dumps(candidates, indent=2)}

Return the validated connections as a JSON array."""