"""PubMed API Service - Search biomedical and life sciences papers"""

import requests
import logging
from typing import List, Dict
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

PUBMED_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


class PubMedService:
    """Searches PubMed for biomedical papers. Free public API."""

    def __init__(self, email: str = ""):
        self.source_name = "pubmed"
        self.email = email

    async def search(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Search PubMed for papers matching the query.
        
        Args:
            query: Search keywords
            limit: Max papers to return
            
        Returns:
            List of paper dicts with standardized format
        """
        try:
            logger.info(f"[PubMed] Searching for: {query} (limit: {limit})")

            # Step 1: Search for paper IDs
            search_params = {
                "db": "pubmed",
                "term": query,
                "retmax": min(limit, 100),
                "retmode": "json",
                "sort": "relevance",
            }
            if self.email:
                search_params["email"] = self.email

            search_response = requests.get(
                PUBMED_SEARCH_URL, params=search_params, timeout=10
            )
            search_response.raise_for_status()
            search_data = search_response.json()

            id_list = search_data.get("esearchresult", {}).get("idlist", [])
            if not id_list:
                logger.info("[PubMed] No papers found")
                return []

            # Step 2: Fetch paper details
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(id_list),
                "retmode": "xml",
                "rettype": "abstract",
            }

            fetch_response = requests.get(
                PUBMED_FETCH_URL, params=fetch_params, timeout=10
            )
            fetch_response.raise_for_status()

            papers = self._parse_xml_response(fetch_response.text)
            logger.info(f"[PubMed] Found {len(papers)} papers")
            return papers

        except Exception as e:
            logger.error(f"[PubMed] Search error: {str(e)}")
            return []

    def _parse_xml_response(self, xml_text: str) -> List[Dict]:
        """Parse PubMed XML response into standardized paper format."""
        papers = []
        try:
            root = ET.fromstring(xml_text)

            for article in root.findall(".//PubmedArticle"):
                medline = article.find(".//MedlineCitation")
                if medline is None:
                    continue

                pmid_elem = medline.find("PMID")
                pmid = pmid_elem.text if pmid_elem is not None else ""

                article_elem = medline.find("Article")
                if article_elem is None:
                    continue

                # Title
                title_elem = article_elem.find("ArticleTitle")
                title = title_elem.text if title_elem is not None else "Untitled"

                # Authors
                authors = []
                author_list = article_elem.find("AuthorList")
                if author_list is not None:
                    for author in author_list.findall("Author"):
                        last = author.find("LastName")
                        first = author.find("ForeName")
                        name_parts = []
                        if first is not None and first.text:
                            name_parts.append(first.text)
                        if last is not None and last.text:
                            name_parts.append(last.text)
                        if name_parts:
                            authors.append(" ".join(name_parts))

                # Abstract
                abstract = ""
                abstract_elem = article_elem.find("Abstract")
                if abstract_elem is not None:
                    abstract_texts = []
                    for text in abstract_elem.findall("AbstractText"):
                        if text.text:
                            abstract_texts.append(text.text)
                    abstract = " ".join(abstract_texts)

                # Published date
                pub_date = None
                journal = article_elem.find("Journal")
                if journal is not None:
                    pub_date_elem = journal.find(".//PubDate")
                    if pub_date_elem is not None:
                        year = pub_date_elem.find("Year")
                        month = pub_date_elem.find("Month")
                        if year is not None and year.text:
                            month_str = month.text if month is not None else "01"
                            # Convert month name to number
                            month_map = {
                                "Jan": "01", "Feb": "02", "Mar": "03",
                                "Apr": "04", "May": "05", "Jun": "06",
                                "Jul": "07", "Aug": "08", "Sep": "09",
                                "Oct": "10", "Nov": "11", "Dec": "12",
                            }
                            month_num = month_map.get(month_str, month_str if month_str.isdigit() else "01")
                            pub_date = f"{year.text}-{month_num}-01T00:00:00"

                # DOI
                doi = ""
                article_ids = article.find(".//ArticleIdList")
                if article_ids is not None:
                    for aid in article_ids.findall("ArticleId"):
                        if aid.get("IdType") == "doi":
                            doi = aid.text or ""
                            break

                paper = {
                    "id": f"pubmed:{pmid}",
                    "title": title.strip() if title else "Untitled",
                    "authors": authors,
                    "published_date": pub_date,
                    "abstract": abstract.strip(),
                    "source": self.source_name,
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    "doi": doi,
                    "citations_count": 0,
                    "categories": [],
                }
                papers.append(paper)

        except ET.ParseError as e:
            logger.error(f"[PubMed] XML parse error: {str(e)}")

        return papers
