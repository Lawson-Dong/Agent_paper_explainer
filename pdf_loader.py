from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Optional
from langchain_core.documents import Document
import logging

logger = logging.getLogger(__name__)

def load_and_split_pdf(file_path: str, use_grobid: bool = False) -> List[Document]:
    """
    Load a PDF file and split it into chunks optimized for physics papers.

    Args:
        file_path: Path to PDF file
        use_grobid: Whether to use GROBID for structured extraction
    """
    if use_grobid:
        return load_and_split_pdf_with_grobid(file_path)
    else:
        return load_and_split_pdf_basic(file_path)

def load_and_split_pdf_basic(file_path: str) -> List[Document]:
    """
    Basic PDF loading without GROBID.
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

def load_and_split_pdf_with_grobid(file_path: str) -> List[Document]:
    """
    Load PDF using GROBID for structured extraction and better chunking.
    """
    from grobid_manager import grobid_manager  # Import here to avoid circular imports

    documents = []

    try:
        # Ensure GROBID server is running
        if not grobid_manager.is_server_running():
            logger.info("Starting GROBID server...")
            if not grobid_manager.start_server():
                logger.warning("Failed to start GROBID server, falling back to basic loading")
                return load_and_split_pdf_basic(file_path)

        # Extract metadata
        metadata = grobid_manager.extract_metadata(file_path)
        if metadata:
            logger.info(f"Extracted metadata: {metadata.get('title', 'Unknown title')}")

        # Get structured TEI content
        tei_content = grobid_manager.process_pdf(file_path, "tei")
        if not tei_content:
            logger.warning("GROBID processing failed, falling back to basic loading")
            return load_and_split_pdf_basic(file_path)

        # Parse TEI and create structured documents
        documents = parse_tei_to_documents(tei_content, metadata or {}, file_path)

        if not documents:
            logger.warning("TEI parsing failed, falling back to basic loading")
            return load_and_split_pdf_basic(file_path)

        logger.info(f"Successfully processed PDF with GROBID: {len(documents)} sections")

    except Exception as e:
        logger.error(f"Error in GROBID processing: {e}")
        return load_and_split_pdf_basic(file_path)

    return documents

def parse_tei_to_documents(tei_content: str, metadata: dict, source_path: str) -> List[Document]:
    """
    Parse TEI XML content into structured Document objects.
    """
    try:
        from lxml import etree

        documents = []
        root = etree.fromstring(tei_content.encode('utf-8'))

        # Extract title
        title = metadata.get("title", "Unknown Title")

        # Extract abstract
        abstract_elem = root.find(".//abstract")
        if abstract_elem is not None:
            abstract_text = etree.tostring(abstract_elem, method="text", encoding="unicode").strip()
            if abstract_text:
                doc = Document(
                    page_content=f"Abstract: {abstract_text}",
                    metadata={
                        "source": source_path,
                        "section": "abstract",
                        "title": title,
                        "type": "abstract"
                    }
                )
                documents.append(doc)

        # Extract body sections
        body = root.find(".//body")
        if body is not None:
            # Find all divisions (sections)
            for div in body.findall(".//div"):
                section_content = extract_section_content(div)
                if section_content.strip():
                    # Try to get section title
                    head = div.find(".//head")
                    section_title = head.text if head is not None else "Section"

                    doc = Document(
                        page_content=f"{section_title}: {section_content}",
                        metadata={
                            "source": source_path,
                            "section": section_title,
                            "title": title,
                            "type": "section"
                        }
                    )
                    documents.append(doc)

        # Extract references if available
        biblio = root.find(".//listBibl")
        if biblio is not None:
            references = []
            for ref in biblio.findall(".//biblStruct"):
                ref_text = etree.tostring(ref, method="text", encoding="unicode").strip()
                if ref_text:
                    references.append(ref_text)

            if references:
                ref_content = "\n".join(references)
                doc = Document(
                    page_content=f"References: {ref_content}",
                    metadata={
                        "source": source_path,
                        "section": "references",
                        "title": title,
                        "type": "references"
                    }
                )
                documents.append(doc)

        # If no structured content found, create a single document with all text
        if not documents:
            all_text = etree.tostring(root, method="text", encoding="unicode")
            doc = Document(
                page_content=all_text,
                metadata={
                    "source": source_path,
                    "title": title,
                    "type": "full_text"
                }
            )
            documents.append(doc)

        return documents

    except Exception as e:
        logger.error(f"Error parsing TEI content: {e}")
        return []

def extract_section_content(div_element) -> str:
    """
    Extract text content from a TEI div element.
    """
    try:
        from lxml import etree

        # Remove head elements to avoid duplicating section titles
        for head in div_element.findall(".//head"):
            head.getparent().remove(head)

        # Extract text content
        content = etree.tostring(div_element, method="text", encoding="unicode").strip()

        # Clean up extra whitespace
        import re
        content = re.sub(r'\n\s*\n', '\n\n', content)
        content = re.sub(r'\s+', ' ', content)

        return content

    except Exception as e:
        logger.error(f"Error extracting section content: {e}")
        return ""

def load_multiple_pdfs(file_paths: List[str], use_grobid: bool = False) -> List[Document]:
    """
    Load multiple PDF files and combine their chunks.

    Args:
        file_paths: List of PDF file paths
        use_grobid: Whether to use GROBID for structured extraction
    """
    all_chunks = []
    for path in file_paths:
        chunks = load_and_split_pdf(path, use_grobid=use_grobid)
        all_chunks.extend(chunks)
    return all_chunks