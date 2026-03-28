from langchain_community.embeddings import FakeEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from typing import List
import os
import shutil

class VectorStoreManager:
    def __init__(self, persist_directory: str = "./chroma_db_hf"):
        self.persist_directory = persist_directory
        # Use fake embeddings for testing (no download needed)
        self.embeddings = FakeEmbeddings(size=384)  # Standard embedding size
        self.vectorstore = None

    def reset_vectorstore(self):
        """Clear and remove existing persistent vectorstore."""
        # Gracefully close any existing vectorstore connection.
        if self.vectorstore is not None:
            try:
                if hasattr(self.vectorstore, "persist"):
                    self.vectorstore.persist()
                # Try to close client connection if available.
                if hasattr(self.vectorstore, "client"):
                    try:
                        self.vectorstore.client.close()
                    except Exception:
                        pass
            except Exception:
                pass
            self.vectorstore = None

        # Retry deletion to handle Windows file-lock/WIN32 sharing issues
        if os.path.exists(self.persist_directory):
            for attempt in range(10):
                try:
                    shutil.rmtree(self.persist_directory)
                    break
                except PermissionError:
                    import time
                    time.sleep(0.2)
                except OSError:
                    import time
                    time.sleep(0.2)
            else:
                # if still failing, keep vectorstore None and continue; user can retry in next run
                print(f"Warning: Failed to remove vectorstore folder after retries: {self.persist_directory}")

    def create_or_load_vectorstore(self, documents: List[Document], reset: bool = False):
        """
        Create a new vectorstore or load existing one.

        set reset=True when source documents changed (add/remove) and you need full rebuild.
        """
        if reset:
            self.reset_vectorstore()

        if os.path.exists(self.persist_directory):
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            # Replace content if explicitly rebuilding with docs
            if documents:
                # Add documents in batches; if the vectorstore is stale, we do a full rebuild
                self.vectorstore.add_documents(documents)
        else:
            if not documents:
                raise ValueError("No documents provided and no existing vectorstore found.")
            self.vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )

    def persist(self):
        """
        Persist the vectorstore to disk.
        """
        if self.vectorstore:
            self.vectorstore.persist()

    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """
        Perform similarity search.
        """
        if not self.vectorstore:
            raise ValueError("Vectorstore not initialized.")
        return self.vectorstore.similarity_search(query, k=k)

    def persist(self):
        """
        Persist the vectorstore to disk.
        """
        if self.vectorstore:
            self.vectorstore.persist()