"""Save chunk vectors locally and retrieve the nearest matching passages."""

from pathlib import Path

import chromadb

DB_PATH = Path(__file__).resolve().parent.parent / "chroma_db"
COLLECTION_NAME = "pdf_chunks"


def get_collection(db_path=DB_PATH):
    """Open our saved group of PDF chunks in ChromaDB.
    Create the database and collection if this is the first run."""
    client = chromadb.PersistentClient(path=str(db_path))
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=None,
        configuration={"hnsw": {"space": "cosine"}},
    )
    return collection


def store_chunks(collection, chunks, embeddings, source, embedding_model):
    """Save each chunk's text, numbers, page number, and PDF filename together.
    Update existing records and remove leftovers from the previously indexed PDF."""
    if not chunks or len(chunks) != len(embeddings):
        raise ValueError("Provide one embedding for every nonempty chunk record.")

    # Every chunk needs a unique name in the database.
    ids = []
    for i in range(len(chunks)):
        ids.append(f"chunk-{i}")

    previous_records = collection.get(include=[])
    previous_ids = previous_records["ids"]

    # Save 100 records at a time to stay within the database's batch limits.
    for start in range(0, len(chunks), 100):
        stop = start + 100
        batch_chunks = chunks[start:stop]
        batch_embeddings = []
        documents = []
        metadata = []

        for vector in embeddings[start:stop]:
            numbers = []
            for number in vector:
                numbers.append(float(number))
            batch_embeddings.append(numbers)

        for chunk in batch_chunks:
            documents.append(chunk["text"])
            chunk_details = {
                "page_number": chunk["page_number"],
                "source": source,
            }
            metadata.append(chunk_details)

        collection.upsert(
            ids=ids[start:stop],
            embeddings=batch_embeddings,
            documents=documents,
            metadatas=metadata,
        )

    # If the new PDF is shorter, remove records left over from the old PDF.
    stale_ids = []
    for old_id in previous_ids:
        if old_id not in ids:
            stale_ids.append(old_id)

    stale_ids.sort()
    for start in range(0, len(stale_ids), 100):
        collection.delete(ids=stale_ids[start:start + 100])

    settings = {"embedding_model": embedding_model, "source": source}
    collection.modify(metadata=settings)


def search_chunks(collection, question_embedding, top_k=3):
    """Compare a question's numbers with the saved chunk numbers.
    Return up to top_k matching passages, including their text and source pages."""
    if top_k <= 0:
        raise ValueError("top_k must be greater than zero.")

    chunk_count = collection.count()
    if chunk_count == 0:
        return []

    question_numbers = []
    for number in question_embedding:
        question_numbers.append(float(number))

    results = collection.query(
        query_embeddings=[question_numbers],
        n_results=min(top_k, chunk_count),
        include=["documents", "metadatas", "distances"],
    )

    # Chroma returns a separate result list for each question. We asked one.
    documents = results["documents"][0]
    metadata = results["metadatas"][0]
    distances = results["distances"][0]
    matches = []

    for i in range(len(documents)):
        match = {
            "text": documents[i],
            "page_number": metadata[i]["page_number"],
            "source": metadata[i]["source"],
            "distance": float(distances[i]),
        }
        matches.append(match)

    return matches
