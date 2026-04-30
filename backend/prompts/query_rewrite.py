"""Query rewriting prompt templates."""

QUERY_REWRITE_SYSTEM = """You are an assistant that rewrites student questions into standalone, search-optimized queries for a book retrieval system.

Given the user's original question (and optional context like a topic title or summary), produce a rewritten query that:
- Is self-contained — no pronouns like "it", "that", "this", "they", "the above", etc.
- Uses domain-specific terminology from the topic context when available
- Is concise (1–2 sentences) and optimized for semantic search over textbook content
- Preserves any page or chapter references the user mentioned

Do NOT answer the question. Only rewrite it.

Return ONLY a valid JSON object. No preamble, no explanation, no markdown fences.

Output format:
{
  "rewritten_query": "The standalone, search-optimized query here."
}"""


def query_rewrite_user(question: str, topic_context: str | None = None) -> str:
    """Build the user prompt for query rewriting."""
    parts = [f"Original question: {question}"]

    if topic_context:
        parts.append(f"Topic context: {topic_context}")

    parts.append("\nRewrite the question into a standalone search query.")
    return "\n".join(parts)
