import argparse
from functools import lru_cache
from pathlib import Path

from pypdf import PdfReader

REPO_ROOT = Path(__file__).resolve().parent.parent
PDF_PATH = REPO_ROOT / "data" / "Handbook.pdf"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def extract_pages(pdf_path, max_pages=None):
    """Read the PDF and return nonblank page text with its PDF page number.
    Use max_pages to inspect only the first few pages, or None to read all pages."""
    if max_pages is not None and max_pages <= 0:
        raise ValueError("max_pages must be greater than zero.")
    reader = PdfReader(pdf_path)
    page_count = len(reader.pages) 


    # print(f"{'There are':<20} | {page_count:>12,} pages\n")

    # print(
    #     f"{'='*100}\n",
    #     f"{' The extracted  ctext is: ':-^100}\n",
    #     f"{'='*100}\n",
    # )

    pages = [] 

    if max_pages is None:
        limit = page_count
    else:
        limit = min(max_pages, page_count)
    for i in range(limit):
        extracted_text = reader.pages[i].extract_text().strip()
        page_number = i+1
    
        if not extracted_text:
            continue
        
        
        page_details = {
            "page_number": page_number,
            "text": extracted_text,
        }
            
        pages.append(page_details)
        
        # page_number_output = f" Page {page_number} of {page_count} "
        # print(
        #     f"{'-'*100}\n",
        #     f"{page_number_output:-^100}\n",
        #     "\n\n",
        #     f"{extracted_text}\n{'-'*100}\n",
        # )
    return pages


def chunk_text(text, chunk_size, overlap=0):
    """Split a string into smaller pieces and return them in a list.
    chunk_size sets the number of characters per piece; overlap repeats some text."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be at least zero and less than chunk_size.")

    step = chunk_size - overlap
    chunks = []
    for i in range(0, len(text), step):
        chunks.append(text[i:i+chunk_size])
        
    return chunks


@lru_cache(maxsize=1)
def load_embedding_model():
    """Load the tool that turns text into numbers.
    The cache keeps it ready so later calls can reuse the same loaded model."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(
        EMBEDDING_MODEL, device="cpu", cache_folder=str(REPO_ROOT / ".cache/models")
    )


def embed_texts(texts):
    """Give a list of texts to the model and return their lists of numbers.
    The first result belongs to the first text, the second to the second, and so on."""
    if not texts:
        raise ValueError("At least one text is required to generate embeddings.")
    model = load_embedding_model()
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
    return embeddings


def embed_chunks(chunk_records):
    """Collect the text from each chunk dictionary, then convert it to numbers.
    The original dictionaries still keep their page numbers for source references."""

    # Give the model the text; keep the original records for page references.
    texts = []
    for chunk in chunk_records:
        texts.append(chunk["text"])

    return embed_texts(texts)


def main():
    # This import stays here so other scripts can reuse the PDF functions.
    """Run the PDF preparation steps: read pages, make chunks, and create embeddings.
    Save the chunks and embeddings in the local database so we can search them later."""
    from vector_store import get_collection, store_chunks

    parser = argparse.ArgumentParser(description="Build a local PDF search index.")
    parser.add_argument("--pdf", type=Path, default=PDF_PATH)
    parser.add_argument("--max-pages", type=int, default=None,
                        help="Inspect this many PDF pages; default: all pages.")
    args = parser.parse_args()
    pages = extract_pages(args.pdf, max_pages=args.max_pages)
    if not pages:
        print("No text found. No changes were made to the index.")
        return

    all_chunks = []
    for page in pages:
        # Keep more of each passage together now that we are searching it.
        chunks = chunk_text(page["text"], chunk_size=800, overlap=100)
        for chunk in chunks:
            if not chunk.strip():
                continue

            chunk_details = {
                "page_number": page["page_number"],
                "text": chunk,
            }
            all_chunks.append(chunk_details)

    print(f"Collected {len(all_chunks)} chunks from {len(pages)} nonblank pages.")
    embeddings = embed_chunks(all_chunks)
    collection = get_collection()
    store_chunks(collection, all_chunks, embeddings, str(args.pdf.resolve()),
                 EMBEDDING_MODEL)
    print(f"Saved {collection.count()} chunks to chroma_db.")
    print(f"Each embedding contains {embeddings.shape[1]} numbers.")
    print("The index contains only the most recently indexed PDF/page selection.")


if __name__ == "__main__":
    main()

    
    
