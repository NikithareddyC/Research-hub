"""Deduplicator - Removes duplicate papers found across multiple sources"""

import logging
from typing import List, Dict
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class Deduplicator:
    """Identifies and removes duplicate papers from multi-source results."""

    def __init__(self, title_similarity_threshold: float = 0.85):
        self.title_threshold = title_similarity_threshold

    def deduplicate(self, papers: List[Dict]) -> List[Dict]:
        """
        Remove duplicate papers, keeping the one with more metadata.
        
        Matches by:
        1. DOI (exact match - most reliable)
        2. Title similarity (fuzzy match)
        
        Args:
            papers: List of paper dicts from multiple sources
            
        Returns:
            Deduplicated list of papers
        """
        if not papers:
            return []

        logger.info(f"[Dedup] Starting with {len(papers)} papers")

        unique_papers = []
        seen_dois = set()
        seen_titles = []

        for paper in papers:
            doi = paper.get("doi", "").strip().lower()
            title = paper.get("title", "").strip().lower()

            if not title or title == "untitled":
                continue

            # Check DOI match
            if doi and doi in seen_dois:
                # Merge: update existing paper if new one has more data
                self._merge_into_existing(unique_papers, paper, match_type="doi")
                continue

            # Check title similarity
            is_duplicate = False
            for seen_title in seen_titles:
                similarity = self._title_similarity(title, seen_title)
                if similarity >= self.title_threshold:
                    self._merge_into_existing(unique_papers, paper, match_type="title")
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_papers.append(paper)
                if doi:
                    seen_dois.add(doi)
                seen_titles.append(title)

        logger.info(f"[Dedup] Reduced to {len(unique_papers)} unique papers (removed {len(papers) - len(unique_papers)} duplicates)")
        return unique_papers

    def _title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles using SequenceMatcher."""
        return SequenceMatcher(None, title1, title2).ratio()

    def _merge_into_existing(self, unique_papers: List[Dict], new_paper: Dict, match_type: str):
        """Merge data from new_paper into the existing matching paper."""
        for existing in unique_papers:
            match = False
            if match_type == "doi":
                match = (
                    existing.get("doi", "").strip().lower()
                    == new_paper.get("doi", "").strip().lower()
                )
            elif match_type == "title":
                match = self._title_similarity(
                    existing.get("title", "").lower(),
                    new_paper.get("title", "").lower(),
                ) >= self.title_threshold

            if match:
                # Keep the one with more citations
                if (new_paper.get("citations_count", 0) or 0) > (existing.get("citations_count", 0) or 0):
                    existing["citations_count"] = new_paper["citations_count"]

                # Keep the longer abstract
                if len(new_paper.get("abstract", "")) > len(existing.get("abstract", "")):
                    existing["abstract"] = new_paper["abstract"]

                # Add source info
                existing["source"] = f"{existing['source']}+{new_paper['source']}"
                break
