"""Command-line interface for the assistant — handy for quick manual testing.

Usage:
    python -m app.cli "Is the GRE required for Heinz College programs?"
    python -m app.cli          # interactive prompt loop
"""

import sys

from . import pipeline
from .retrieval import get_retriever


def _print(response) -> None:
    print(f"\n{response.answer}")
    if response.sources:
        print("\nSources:")
        for s in response.sources:
            print(f"  - {s.title}: {s.url}")
    if response.escalation:
        print(f"\n{response.escalation}")
    print(f"\n[support: {response.support_status.value} | backend: {response.model}]")


def main(argv: list[str] | None = None) -> None:
    argv = argv if argv is not None else sys.argv[1:]
    retriever = get_retriever()

    if argv:
        _print(pipeline.answer(" ".join(argv), retriever))
        return

    print("Heinz Admissions Assistant (Ctrl-C to exit)")
    try:
        while True:
            question = input("\nQuestion: ").strip()
            if question:
                _print(pipeline.answer(question, retriever))
    except (KeyboardInterrupt, EOFError):
        print()


if __name__ == "__main__":
    main()
