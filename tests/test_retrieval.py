"""Retrieval tests over the live corpus (Member 2's chunked dataset).

Assertions check the *kind* of source returned (its content / URL) rather than a
brittle fixed document id, so they stay valid as the corpus is refreshed.
"""

from app.retrieval import get_retriever


def test_gre_question_returns_a_testing_source():
    retriever = get_retriever()
    results = retriever.search("Is the GRE required for Heinz College programs?")
    assert results, "expected at least one relevant passage"
    assert "gre" in results[0].document.text.lower()


def test_english_question_returns_an_english_proficiency_source():
    retriever = get_retriever()
    results = retriever.search("What TOEFL or IELTS score do I need?")
    assert results, "expected at least one relevant passage"
    top = results[0].document.text.lower()
    assert any(term in top for term in ("toefl", "ielts", "english"))


def test_tuition_question_returns_a_cost_source():
    retriever = get_retriever()
    results = retriever.search("How much is tuition?")
    assert results, "expected at least one relevant passage"
    assert "tuition" in results[0].document.text.lower()


def test_unrelated_question_returns_no_passages():
    retriever = get_retriever()
    results = retriever.search("What is the capital of France?")
    assert results == []
