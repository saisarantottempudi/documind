from functools import lru_cache

from langchain_ollama import OllamaLLM

from app.core.config import settings
from app.core.logging import logger

# Chain-of-Thought system prompt used for every query
COT_SYSTEM_PROMPT = """\
You are DocuMind, an expert document analyst for an enterprise.

When answering, follow these steps explicitly:
1. UNDERSTAND: Restate what the question is asking in one sentence.
2. SCAN: Identify which retrieved passages are most relevant and why.
3. REASON: Combine the evidence step by step to form your answer.
4. ANSWER: Give a clear, concise final answer.
5. CITE: List the source document names you used.

Always ground your answer strictly in the provided context.
If the context does not contain enough information, say so clearly.
"""

COT_HUMAN_TEMPLATE = """\
<context>
{context}
</context>

<question>
{question}
</question>

Think step by step before answering.
"""


@lru_cache(maxsize=1)
def get_llm() -> OllamaLLM:
    logger.info("initialising_llm", model=settings.ollama_model)
    return OllamaLLM(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        temperature=0.1,  # low temp = more factual
        num_predict=1024,
    )


def parse_cot_response(raw: str) -> tuple[str, list[str]]:
    """Split raw CoT output into (final_answer, reasoning_steps)."""
    lines = raw.strip().splitlines()
    steps, answer_lines = [], []
    in_answer = False
    for line in lines:
        upper = line.upper()
        if "4. ANSWER" in upper or upper.startswith("ANSWER:"):
            in_answer = True
        if in_answer:
            answer_lines.append(line)
        else:
            if line.strip():
                steps.append(line.strip())
    answer = "\n".join(answer_lines).replace("4. ANSWER:", "").strip() or raw.strip()
    return answer, steps
