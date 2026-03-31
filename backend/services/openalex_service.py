"""OpenAlex API Service - Search 250M+ works, free and open"""

import requests
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

OPENALEX_API_URL = "https://api.openalex.org"


class OpenAlexService:
    """Searches OpenAlex for academic works. Completely free, no key needed."""

    def __init__(self, email: str = ""):
        self.source_name = "openalex"
        self.email = email  # For polite pool (faster responses)

    async def search(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Search OpenAlex for papers matching the query.
        
        Args:
            query: Search keywords
            limit: Max papers to return
            
        Returns:
            List of paper dicts with standardized format
        """
        try:
            logger.info(f"[OpenAlex] Searching for: {query} (limit: {limit})")

            params = {
                "search": query,
                "per_page": min(limit, 100),
                "sort": "relevance_score:desc",
            }

            if self.email:
                params["mailto"] = self.email

            response = requests.get(
                f"{OPENALEX_API_URL}/works",
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            papers = []
            results = data.get("results", [])

            for item in results:
                # Extract authors
                authors = []
                for authorship in item.get("authorships", []):
                    author_info = authorship.get("author", {})
                    name = author_info.get("display_name", "")
                    if name:
                        authors.append(name)

                # Get published date
                pub_date = item.get("publication_date")
                if pub_date:
                    pub_date = f"{pub_date}T00:00:00"

                # Get abstract from inverted index
                abstract = ""
                abstract_index = item.get("abstract_inverted_index")
                if abstract_index:
                    abstract = self._reconstruct_abstract(abstract_index)

                # Get DOI
                doi = item.get("doi", "") or ""
                if doi.startswith("https://doi.org/"):
                    doi = doi.replace("https://doi.org/", "")

                # Get URL
                url = item.get("doi", "") or item.get("id", "")
                if not url.startswith("http"):
                    url = f"https://openalex.org/works/{item.get('id', '').split('/')[-1]}"

                # Get concepts/topics as categories
                categories = []
                for concept in item.get("concepts", [])[:5]:
                    if concept.get("display_name"):
                        categories.append(concept["display_name"])

                paper = {
                    "id": f"openalex:{item.get('id', '').split('/')[-1]}",
                    "title": (item.get("title", "") or "Untitled").strip(),
                    "authors": authors,
                    "published_date": pub_date,
                    "abstract": abstract,
                    "source": self.source_name,
                    "url": url,
                    "doi": doi,
                    "citations_count": item.get("cited_by_count", 0) or 0,
                    "categories": categories,
                }
                papers.append(paper)

            logger.info(f"[OpenAlex] Found {len(papers)} papers")
            return papers

        except Exception as e:
            logger.error(f"[OpenAlex] Search error: {str(e)}")
            return []

    def _reconstruct_abstract(self, inverted_index: Dict) -> str:
        """Reconstruct abstract from OpenAlex inverted index format."""
        try:
            word_positions = []
            for word, positions in inverted_index.items():
                for pos in positions:
                    word_positions.append((pos, word))
            word_positions.sort(key=lambda x: x[0])
            return " ".join(word for _, word in word_positions)
        except Exception:
            return ""
