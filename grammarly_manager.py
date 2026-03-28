import requests
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class GrammarlyManager:
    """
    Integration with Grammarly API for text quality checking.
    Requires GRAMMARLY_CLIENT_ID and GRAMMARLY_CLIENT_SECRET from .env
    """
    
    BASE_URL = "https://api.grammarly.com/v1"
    
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.is_authenticated = False
        
        if client_id and client_secret:
            self.is_authenticated = self.authenticate()
    
    def authenticate(self) -> bool:
        """Authenticate with Grammarly API."""
        try:
            auth_url = f"{self.BASE_URL}/oauth/token"
            payload = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': 'writing-score'
            }
            
            response = requests.post(auth_url, json=payload, timeout=10)
            response.raise_for_status()
            
            self.access_token = response.json().get('access_token')
            return bool(self.access_token)
        
        except Exception as e:
            logger.error(f"Grammarly authentication failed: {e}")
            return False
    
    def get_writing_score(self, text: str) -> Optional[Dict]:
        """
        Get writing quality score for text using Grammarly's Writing Score API.
        
        Returns:
            Dict with overall score and detailed metrics
        """
        if not self.is_authenticated:
            logger.warning("Grammarly not authenticated")
            return None
        
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'text': text,
                'goals': {
                    'audience': 'academic',
                    'style': 'academic',
                    'tone': 'formal',
                    'intent': 'inform'
                }
            }
            
            response = requests.post(
                f"{self.BASE_URL}/writing-score",
                json=payload,
                headers=headers,
                timeout=15
            )
            response.raise_for_status()
            
            result = response.json()
            return {
                'overall_score': result.get('score', 0),
                'scores': result.get('scores', {}),
                'feedback': result.get('feedback', [])
            }
        
        except Exception as e:
            logger.error(f"Error getting writing score: {e}")
            return None
    
    def check_plagiarism(self, text: str) -> Optional[Dict]:
        """
        Check for plagiarism in text (requires Plagiarism Detection API).
        
        Returns:
            Dict with plagiarism detection results
        """
        if not self.is_authenticated:
            logger.warning("Grammarly not authenticated")
            return None
        
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {'text': text}
            
            response = requests.post(
                f"{self.BASE_URL}/plagiarism",
                json=payload,
                headers=headers,
                timeout=15
            )
            response.raise_for_status()
            
            result = response.json()
            return {
                'plagiarism_score': result.get('plagiarism_score', 0),
                'matches': result.get('matches', [])
            }
        
        except Exception as e:
            logger.error(f"Error checking plagiarism: {e}")
            return None
