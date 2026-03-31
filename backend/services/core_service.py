"""CORE API Service - Search open access research globally"""

import requests
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

CORE_API_URL = "https://api.core.ac.uk/v3"


class CoreService:
    """Searches CORE for open access research papers. Requires API key."""

    def __init__(self, api_key: str = ""):
        self.source_name = "core"
        self.api_key = api_key

    async def search(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Search CORE for papers matching the query.
        
        Args:
            query: Search keywords
            limit: Max papers to return
            
        Returns:
            List of paper dicts with standardized format
        """
        if not self.api_key:
            logger.warning("[CORE] No API key configured, skipping")
            return []

        try:
            logger.info(f"[CORE] Searching for: {query} (limit: {limit})")

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            params = {
                "q": query,
                "limit": min(limit, 100),
                "scroll": "false",
            }

            response = requests.get(
                f"{CORE_API_URL}/search/works",
                params=params,
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            papers = []
            results = data.get("results", [])

            for item in results:
                authors = []
                for author in item.get("authors", []):
                    if isinstance(author, dict):
                        authors.append(author.get("name", ""))
                    elif isinstance(author, str):
                        authors.append(author)

                pub_date = None
                if item.get("publishedDate"):
                    pub_date = item["publishedDate"]
                elif item.get("yearPublished"):
                    pub_date = f"{item['yearPublished']}-01-01T00:00:00"

                abstract = item.get("abstract", "") or ""

                doi = ""
                for identifier in item.get("identifiers", []):
                    if isinstance(identifier, str) and "doi.org" in identifier:
                        doi = identifier.split("doi.org/")[-1]
                        break

                download_url = item.get("downloadUrl", "") or item.get("sourceFulltextUrls", [""])[0] if item.get("sourceFulltextUrls") else ""
                url = download_url or f"https://core.ac.uk/works/{item.get('id', '')}"

                paper = {
                    "id": f"core:{item.get('id', '')}",
                    "title": (item.get("title", "") or "Untitled").strip(),
                    "authors": [a for a in authors if a],
                    "published_date": pub_date,
                    "abstract": abstract.strip(),
                    "source": self.source_name,
                    "url": url,
                    "doi": doi,
                    "citations_count": item.get("citationCount", 0) or 0,
                    "categories": [],
                }
                papers.append(paper)

            logger.info(f"[CORE] Found {len(papers)} papers")
            return papers

        except Exception as e:
            logger.error(f"[CORE] Search error: {str(e)}")
            return []
