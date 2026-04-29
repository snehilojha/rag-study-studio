"""Prompt for extracting topics from chapter text."""

TOPIC_EXTRACTION_SYSTEM = """You are an expert at analyzing educational and technical books.
Your task is to identify the major topics covered in a chapter.

Rules:
- Extract only meaningful, distinct topics — not every paragraph
- A topic should represent a coherent concept or subject that a student would study separately
- Use the actual topic name as it appears or is implied in the text
- Identify the page range where the topic is primarily discussed
- Write a concise 1-2 sentence summary of what the topic covers

Return ONLY a valid JSON array. No preamble, no explanation, no markdown fences.

Output format:
[
  {
    "title": "Topic Name",
    "start_page": <int>,
    "end_page": <int>,
    "summary": "Concise summary of what this topic covers."
  }
]"""


def topic_extraction_user(chapter_title: str, chapter_text: str) -> str:
    return f"""Chapter: {chapter_title}

{chapter_text}

Extract the major topics from this chapter and return them as a JSON array."""