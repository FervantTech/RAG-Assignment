"""Search the saved PDF index without reprocessing the document."""

import argparse

from read_pdf import EMBEDDING_MODEL, embed_texts
from vector_store import get_collection, search_chunks


def main():
    """Read a question supplied in the terminal and search the saved PDF index.
    Print matching passages and page numbers, without asking Gemini for an answer."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", help="The question or phrase to search for.")
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()
    if not args.question.strip():
        parser.error("The question cannot be blank.")
    if args.top_k <= 0:
        parser.error("--top-k must be greater than zero.")

    collection = get_collection()
    if collection.count() == 0:
        parser.error("The index is empty. Run src/read_pdf.py first.")
    if (collection.metadata or {}).get("embedding_model") != EMBEDDING_MODEL:
        parser.error("The stored model does not match. Rebuild the PDF index.")

    question_embedding = embed_texts([args.question])[0]
    matches = search_chunks(collection, question_embedding, args.top_k)
    for rank, match in enumerate(matches, start=1):
        print(f"\nMatch {rank} | PDF page {match['page_number']} "
              f"| cosine distance {match['distance']:.3f}")
        print(f"Source: {match['source']}")
        print(match["text"])
    print("\nThese are retrieved passages, not an LLM-generated answer.")


if __name__ == "__main__":
    main()
