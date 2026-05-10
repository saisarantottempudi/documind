from app.services.llm import parse_cot_response


def test_parse_cot_extracts_answer():
    raw = """
1. UNDERSTAND: The question asks about the return window.
2. SCAN: Passage 1 mentions 30 days.
3. REASON: The policy clearly states 30 days from purchase.
4. ANSWER: You have 30 days from the date of purchase to return the item.
5. CITE: returns-policy.pdf
"""
    answer, steps = parse_cot_response(raw)
    assert "30 days" in answer
    assert len(steps) > 0


def test_parse_cot_fallback_on_plain_text():
    raw = "The answer is 42."
    answer, steps = parse_cot_response(raw)
    assert answer == "The answer is 42."


def test_parse_cot_strips_whitespace():
    raw = "\n\n4. ANSWER:   Clean answer here.  \n"
    answer, _ = parse_cot_response(raw)
    assert "Clean answer here." in answer
