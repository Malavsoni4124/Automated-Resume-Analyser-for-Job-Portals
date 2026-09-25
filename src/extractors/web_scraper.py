import httpx
import re
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class GitHubScraper:
    async def extract_profile(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extracts public information from a candidate's GitHub profile.
        Returns a structured dictionary representing the candidate's skills and projects.
        """
        match = re.search(r'github\.com/([^/]+)', url)
        if not match:
            return None
            
        username = match.group(1)
        api_url = f"https://api.github.com/users/{username}"
        repos_url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=5"
        
        try:
            async with httpx.AsyncClient() as client:
                user_resp = await client.get(api_url, timeout=5.0)
                if user_resp.status_code != 200:
                    return None
                    
                user_data = user_resp.json()
                
                repos_resp = await client.get(repos_url, timeout=5.0)
                repos_data = repos_resp.json() if repos_resp.status_code == 200 else []
                
                # Extract languages to infer skills
                skills = set()
                projects = []
                for repo in repos_data:
                    if repo.get("language"):
                        skills.add(repo["language"])
                    projects.append({
                        "name": repo.get("name"),
                        "description": repo.get("description"),
                        "url": repo.get("html_url")
                    })
                    
                return {
                    "contact": {
                        "name": user_data.get("name") or username,
                        "email": user_data.get("email"),
                        "links": [url, user_data.get("blog")]
                    },
                    "summary": user_data.get("bio"),
                    "skills": list(skills),
                    "projects": projects
                }
        except Exception as e:
            logger.error(f"GitHub scraping failed for {url}: {e}")
            return None
