"""CrossRef API Service - Search 150M+ scholarly articles"""

import requests
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

CROSSREF_API_URL = "https://api.crossref.org/works"


class CrossrefService:
    """Searches CrossRef for scholarly articles. Free public API."""

    def __init__(self, api_key: str = ""):
        self.source_name = "crossref"
        self.api_key = api_key

    async def search(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Search CrossRef for papers matching the query.
        
        Args:
            query: Search keywords
            limit: Max papers to return
            
        Returns:
            List of paper dicts with standardized format
        """
        try:
            logger.info(f"[CrossRef] Searching for: {query} (limit: {limit})")

            params = {
                "query": query,
                "rows": min(limit, 100),
                "sort": "relevance",
                "order": "desc",
                "select": "DOI,title,author,published-print,published-online,abstract,is-referenced-by-count,URL,subject",
            }

            headers = {"User-Agent": "ResearchPaperHub/1.0 (mailto:research@hub.com)"}

            response = requests.get(
                CROSSREF_API_URL, params=params, headers=headers, timeout=10
            )
            response.raise_for_status()
            data = response.json()

            papers = []
            items = data.get("message", {}).get("items", [])

            for item in items:
                title_list = item.get("title", [])
                title = title_list[0] if title_list else "Untitled"

                authors = []
                for author in item.get("author", []):
                    name_parts = []
                    if author.get("given"):
                        name_parts.append(author["given"])
                    if author.get("family"):
                        name_parts.append(author["family"])
                    if name_parts:
                        authors.append(" ".join(name_parts))

                # Get published date
                pub_date = None
                for date_field in ["published-print", "published-online"]:
                    date_parts = item.get(date_field, {}).get("date-parts", [[]])
                    if date_parts and date_parts[0]:
                        parts = date_parts[0]
                        year = parts[0] if len(parts) > 0 else 2000
                        month = parts[1] if len(parts) > 1 else 1
                        day = parts[2] if len(parts) > 2 else 1
                        try:
                            from datetime import datetime
                            pub_date = datetime(year, month, day).isoformat()
                        except (ValueError, TypeError):
                            pass
                    if pub_date:
                        break

                abstract = item.get("abstract", "")
                # Clean HTML tags from CrossRef abstracts
                if abstract:
                    import re
                    abstract = re.sub(r"<[^>]+>", "", abstract).strip()

                paper = {
                    "id": f"crossref:{item.get('DOI', '')}",
                    "title": title.strip(),
                    "authors": authors,
                    "published_date": pub_date,
                    "abstract": abstract,
                    "source": self.source_name,
                    "url": item.get("URL", f"https://doi.org/{item.get('DOI', '')}"),
                    "doi": item.get("DOI", ""),
                    "citations_count": item.get("is-referenced-by-count", 0),
                    "categories": item.get("subject", []),
                }
                papers.append(paper)

            logger.info(f"[CrossRef] Found {len(papers)} papers")
            return papers

        except Exception as e:
            logger.error(f"[CrossRef] Search error: {str(e)}")
            return []
