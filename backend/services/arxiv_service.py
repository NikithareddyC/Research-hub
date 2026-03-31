"""ArXiv API Service - Search pre-print papers in physics, math, CS, AI/ML"""

import requests
import logging
import xml.etree.ElementTree as ET
from typing import List, Dict
from urllib.parse import quote

logger = logging.getLogger(__name__)

ARXIV_API_URL = "http://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


class ArxivService:
    """Searches arXiv.org for academic papers. Free, no API key needed."""

    def __init__(self):
        self.source_name = "arxiv"

    async def search(self, query: str, limit: int = 20) -> List[Dict]:
        try:
            logger.info(f"[ArXiv] Searching for: {query} (limit: {limit})")

            params = {
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": min(limit, 20),
                "sortBy": "relevance",
                "sortOrder": "descending",
            }

            response = requests.get(ARXIV_API_URL, params=params, timeout=(2, 3))
            response.raise_for_status()

            root = ET.fromstring(response.text)
            papers = []

            for entry in root.findall("atom:entry", NS):
                entry_id = entry.findtext("atom:id", "", NS)
                title = entry.findtext("atom:title", "Untitled", NS).strip().replace("\n", " ")
                summary = entry.findtext("atom:summary", "", NS).strip().replace("\n", " ")
                published = entry.findtext("atom:published", "", NS)

                authors = []
                for author in entry.findall("atom:author", NS):
                    name = author.findtext("atom:name", "", NS)
                    if name:
                        authors.append(name)

                categories = []
                for cat in entry.findall("arxiv:primary_category", NS):
                    term = cat.get("term", "")
                    if term:
                        categories.append(term)

                doi_elem = entry.find("arxiv:doi", NS)
                doi = doi_elem.text if doi_elem is not None else ""

                paper = {
                    "id": f"arxiv:{entry_id.split('/')[-1]}",
                    "title": title,
                    "authors": authors,
                    "published_date": published if published else None,
                    "abstract": summary,
                    "source": self.source_name,
                    "url": entry_id,
                    "doi": doi,
                    "citations_count": 0,
                    "categories": categories,
                }
                papers.append(paper)

            logger.info(f"[ArXiv] Found {len(papers)} papers")
            return papers

        except Exception as e:
            logger.error(f"[ArXiv] Search error: {str(e)}")
            return []
