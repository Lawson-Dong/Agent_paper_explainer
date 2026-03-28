import os
import time
import requests
import subprocess
import tempfile
import zipfile
from pathlib import Path
import docker
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class GrobidManager:
    """
    Manages local GROBID server deployment using Docker.
    """

    def __init__(self, port: int = 8070):
        self.port = port
        self.container_name = "grobid-local"
        self._docker_client = None  # Lazy initialization
        self.server_url = f"http://localhost:{port}"

    @property
    def docker_client(self):
        """Lazy initialization of Docker client."""
        if self._docker_client is None:
            try:
                self._docker_client = docker.from_env()
            except Exception as e:
                logger.error(f"Failed to initialize Docker client: {e}")
                raise
        return self._docker_client

    def is_server_running(self) -> bool:
        """Check if GROBID server is running and responsive."""
        try:
            response = requests.get(f"{self.server_url}/api/isalive", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def start_server(self) -> bool:
        """Start GROBID server using Docker."""
        try:
            # Check if container already exists
            try:
                container = self.docker_client.containers.get(self.container_name)
                if container.status == "running":
                    logger.info("GROBID server already running")
                    return True
                elif container.status == "exited":
                    container.start()
                    logger.info("Restarted existing GROBID container")
                    return self._wait_for_server()
            except docker.errors.NotFound:
                pass

            # Start new container
            logger.info("Starting new GROBID container...")
            container = self.docker_client.containers.run(
                "grobid/grobid:0.8.0",
                name=self.container_name,
                ports={"8070/tcp": self.port},
                detach=True,
                mem_limit="2g",
                environment={
                    "JAVA_OPTS": "-Xmx2048m"
                }
            )

            return self._wait_for_server()

        except Exception as e:
            logger.error(f"Failed to start GROBID server: {e}")
            return False

    def stop_server(self) -> bool:
        """Stop GROBID server."""
        try:
            container = self.docker_client.containers.get(self.container_name)
            container.stop()
            container.remove()
            logger.info("GROBID server stopped")
            return True
        except docker.errors.NotFound:
            logger.info("GROBID container not found")
            return True
        except Exception as e:
            logger.error(f"Failed to stop GROBID server: {e}")
            return False

    def _wait_for_server(self, timeout: int = 120) -> bool:
        """Wait for GROBID server to be ready."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_server_running():
                logger.info("GROBID server is ready")
                return True
            time.sleep(2)
        logger.error("GROBID server failed to start within timeout")
        return False

    def process_pdf(self, pdf_path: str, output_format: str = "tei") -> Optional[str]:
        """
        Process PDF with GROBID and return structured XML/TEI.

        Args:
            pdf_path: Path to PDF file
            output_format: 'tei' or 'xml'

        Returns:
            Structured XML/TEI content or None if failed
        """
        if not self.is_server_running():
            logger.error("GROBID server not running")
            return None

        try:
            with open(pdf_path, "rb") as f:
                files = {"input": f}
                params = {"consolidateHeader": "1", "consolidateCitations": "1"}

                if output_format == "tei":
                    endpoint = f"{self.server_url}/api/processFulltextDocument"
                else:
                    endpoint = f"{self.server_url}/api/processHeaderDocument"

                response = requests.post(
                    endpoint,
                    files=files,
                    data=params,
                    timeout=300  # 5 minutes timeout
                )

                if response.status_code == 200:
                    return response.text
                else:
                    logger.error(f"GROBID processing failed: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Error processing PDF with GROBID: {e}")
            return None

    def extract_metadata(self, pdf_path: str) -> Optional[Dict[str, Any]]:
        """
        Extract metadata from PDF using GROBID.

        Returns:
            Dict with title, authors, abstract, etc.
        """
        xml_content = self.process_pdf(pdf_path, "tei")
        if not xml_content:
            return None

        try:
            from lxml import etree

            # Parse TEI XML
            root = etree.fromstring(xml_content.encode('utf-8'))

            # Extract basic metadata
            metadata = {}

            # Title
            title_elem = root.find(".//titleStmt/title")
            if title_elem is not None:
                metadata["title"] = title_elem.text

            # Authors
            authors = []
            for author in root.findall(".//titleStmt/author"):
                author_info = {}
                pers_name = author.find("persName")
                if pers_name is not None:
                    forename = pers_name.find("forename")
                    surname = pers_name.find("surname")
                    if forename is not None and surname is not None:
                        author_info["name"] = f"{forename.text} {surname.text}"
                    elif surname is not None:
                        author_info["name"] = surname.text

                # Affiliation
                affiliation = author.find("affiliation")
                if affiliation is not None:
                    org = affiliation.find("orgName")
                    if org is not None:
                        author_info["affiliation"] = org.text

                if author_info:
                    authors.append(author_info)

            if authors:
                metadata["authors"] = authors

            # Abstract
            abstract_elem = root.find(".//abstract")
            if abstract_elem is not None:
                metadata["abstract"] = etree.tostring(abstract_elem, method="text", encoding="unicode").strip()

            # Keywords
            keywords = []
            for keyword in root.findall(".//keywords/term"):
                if keyword.text:
                    keywords.append(keyword.text.strip())
            if keywords:
                metadata["keywords"] = keywords

            return metadata

        except Exception as e:
            logger.error(f"Error parsing GROBID XML: {e}")
            return None

# Global instance
grobid_manager = GrobidManager()