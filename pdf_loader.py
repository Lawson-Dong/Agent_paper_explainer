from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List
from langchain_core.documents import Document

def load_and_split_pdf(file_path: str) -> List[Document]:
    """
    Load a PDF file and split it into chunks optimized for physics papers.
    """
    loader = PyPDFLoader(file_path)
    documents = loader.load()

    # For physics papers, try to keep sections, formulas, and methods intact
    # Use separators that prioritize paragraphs and sections over sentences
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=200,
        separators=[
            "\n\n",  # Double newlines (paragraphs)
            "\n",    # Single newlines
            ". ",    # Sentences
            " ",     # Words
            "",      # Characters
        ],
        keep_separator=True
    )

    chunks = text_splitter.split_documents(documents)
    return chunks

def load_multiple_pdfs(file_paths: List[str]) -> List[Document]:
    """
    Load multiple PDF files and combine their chunks.
    """
    all_chunks = []
    for path in file_paths:
        chunks = load_and_split_pdf(path)
        all_chunks.extend(chunks)
    return all_chunks