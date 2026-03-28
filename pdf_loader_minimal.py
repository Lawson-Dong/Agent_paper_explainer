#!/usr/bin/env python3
"""
Minimal PDF loader test
"""

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List
from langchain_core.documents import Document

print("DEBUG: Basic imports completed")

def load_and_split_pdf_basic(file_path: str) -> List[Document]:
    """
    Basic PDF loading without GROBID.
    """
    print(f"DEBUG: Loading PDF from {file_path}")
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    print(f"DEBUG: Loaded {len(documents)} pages")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=200,
    )

    chunks = text_splitter.split_documents(documents)
    print(f"DEBUG: Split into {len(chunks)} chunks")
    return chunks

def load_multiple_pdfs(file_paths: List[str]) -> List[Document]:
    """
    Load multiple PDF files and combine their chunks.
    """
    all_chunks = []
    for path in file_paths:
        chunks = load_and_split_pdf_basic(path)
        all_chunks.extend(chunks)
    return all_chunks

print("DEBUG: Functions defined")