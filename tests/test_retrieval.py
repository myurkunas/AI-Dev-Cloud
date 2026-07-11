"""Retrieval tests: relevant questions rank the right doc; junk finds nothing."""

from app.retrieval import get_retriever


def test_gre_question_ranks_testing_document_first():
    retriever = get_retriever()
    results = retriever.search("Is the GRE required for Heinz programs?")
    assert results, "expected at least one relevant passage"
    assert results[0].document.id == "standardized-testing"


def test_english_question_ranks_english_document_first():
    retriever = get_retriever()
    results = retriever.search("What TOEFL or IELTS score do I need?")
    assert results[0].document.id == "english-language-proficiency"


def test_unrelated_question_returns_no_passages():
    retriever = get_retriever()
    results = retriever.search("What is the capital of France?")
    assert results == []
