import requests
import feedparser
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ArxivManager:
    """
    Integration with arXiv API for physics paper discovery and metadata retrieval.
    """
    
    BASE_URL = "http://export.arxiv.org/api/query?"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Physics-Paper-Agent'})
    
    def search_papers(
        self, 
        query: str, 
        category: str = "physics.gen-ph",
        max_results: int = 10,
        sort_by: str = "submittedDate"
    ) -> List[Dict]:
        """
        Search arXiv for papers matching query.
        
        Args:
            query: Search keywords
            category: arXiv category (e.g., physics.gen-ph, physics.app-ph)
            max_results: Maximum number of results
            sort_by: Sort by ('relevance' or 'submittedDate')
        
        Returns:
            List of paper metadata
        """
        try:
            # Build arXiv API query
            search_query = f"cat:{category} AND all:{query}"
            params = {
                'search_query': search_query,
                'start': 0,
                'max_results': max_results,
                'sortBy': sort_by,
                'sortOrder': 'descending'
            }
            
            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            papers = []
            feed = feedparser.parse(response.text)
            
            for entry in feed.entries:
                paper = {
                    'title': entry.title,
                    'arxiv_id': entry.id.split('/abs/')[-1],
                    'authors': [author.name for author in entry.authors],
                    'summary': entry.summary.replace('\n', ' '),
                    'published': entry.published,
                    'url': entry.id,
                    'pdf_url': entry.id.replace('abs', 'pdf') + '.pdf',
                    'categories': entry.arxiv_primary_category['term']
                }
                papers.append(paper)
            
            return papers
        
        except Exception as e:
            logger.error(f"Error searching arXiv: {e}")
            return []
    
    def get_latest_papers(
        self, 
        category: str = "physics.gen-ph",
        days: int = 7,
        max_results: int = 20
    ) -> List[Dict]:
        """
        Get latest papers from past N days.
        """
        from_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
        query = f"submittedDate:[{from_date}000000 TO 9999999999]"
        
        search_query = f"cat:{category} AND {query}"
        params = {
            'search_query': search_query,
            'start': 0,
            'max_results': max_results,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        
        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            papers = []
            feed = feedparser.parse(response.text)
            
            for entry in feed.entries:
                paper = {
                    'title': entry.title,
                    'arxiv_id': entry.id.split('/abs/')[-1],
                    'authors': [author.name for author in entry.authors],
                    'summary': entry.summary.replace('\n', ' '),
                    'published': entry.published,
                    'url': entry.id,
                    'pdf_url': entry.id.replace('abs', 'pdf') + '.pdf'
                }
                papers.append(paper)
            
            return papers
        
        except Exception as e:
            logger.error(f"Error fetching latest papers: {e}")
            return []
    
    def get_paper_by_arxiv_id(self, arxiv_id: str) -> Optional[Dict]:
        """Get paper metadata by arXiv ID."""
        params = {
            'search_query': f'arxiv:{arxiv_id}',
            'max_results': 1
        }
        
        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            feed = feedparser.parse(response.text)
            if feed.entries:
                entry = feed.entries[0]
                return {
                    'title': entry.title,
                    'arxiv_id': arxiv_id,
                    'authors': [author.name for author in entry.authors],
                    'summary': entry.summary.replace('\n', ' '),
                    'published': entry.published,
                    'url': entry.id,
                    'pdf_url': entry.id.replace('abs', 'pdf') + '.pdf'
                }
        except Exception as e:
            logger.error(f"Error fetching paper {arxiv_id}: {e}")
        
        return None
