"""Relevance Scorer - Ranks papers by relevance to the search query"""

import re
import logging
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class RelevanceScorer:
    """Calculates relevance scores for papers based on query matching."""

    def __init__(self):
        # Weight distribution for relevance scoring
        self.weights = {
            "title_match": 0.40,      # 40% - Title keyword match
            "abstract_match": 0.30,   # 30% - Abstract keyword match
            "citations": 0.15,        # 15% - Citation count
            "recency": 0.15,          # 15% - How recent the paper is
        }

    def score_papers(self, papers: List[Dict], query: str) -> List[Dict]:
        """
        Score and rank papers by relevance to the query.
        
        Args:
            papers: List of paper dicts
            query: Original search query
            
        Returns:
            Papers with relevance_score field, sorted by score descending
        """
        if not papers:
            return []

        query_terms = self._extract_terms(query)
        logger.info(f"[Scorer] Scoring {len(papers)} papers for query terms: {query_terms}")

        # Calculate max citations for normalization
        max_citations = max((p.get("citations_count", 0) or 0) for p in papers) or 1

        for paper in papers:
            title_score = self._keyword_match_score(
                paper.get("title", ""), query_terms
            )
            abstract_score = self._keyword_match_score(
                paper.get("abstract", ""), query_terms
            )
            citation_score = self._citation_score(
                paper.get("citations_count", 0) or 0, max_citations
            )
            recency_score = self._recency_score(paper.get("published_date"))

            # Weighted combined score (0-1)
            combined = (
                self.weights["title_match"] * title_score
                + self.weights["abstract_match"] * abstract_score
                + self.weights["citations"] * citation_score
                + self.weights["recency"] * recency_score
            )

            paper["relevance_score"] = round(combined, 4)

        # Sort by relevance score descending
        papers.sort(key=lambda p: p.get("relevance_score", 0), reverse=True)
        return papers

    def sort_papers(self, papers: List[Dict], sort_by: str) -> List[Dict]:
        """Sort papers by different criteria."""
        if sort_by == "date":
            papers.sort(
                key=lambda p: p.get("published_date") or "0000",
                reverse=True,
            )
        elif sort_by == "citations":
            papers.sort(
                key=lambda p: p.get("citations_count", 0) or 0,
                reverse=True,
            )
        # Default: already sorted by relevance
        return papers

    def _extract_terms(self, query: str) -> List[str]:
        """Extract meaningful search terms from query."""
        # Remove common stop words
        stop_words = {
            "a", "an", "the", "in", "on", "at", "to", "for", "of", "and",
            "or", "is", "it", "by", "with", "from", "as", "are", "was",
            "were", "been", "be", "have", "has", "had", "do", "does",
            "did", "will", "would", "could", "should", "may", "might",
            "this", "that", "these", "those", "using", "based",
        }
        terms = re.findall(r'\b\w+\b', query.lower())
        return [t for t in terms if t not in stop_words and len(t) > 1]

    def _keyword_match_score(self, text: str, query_terms: List[str]) -> float:
        """Calculate what fraction of query terms appear in the text."""
        if not text or not query_terms:
            return 0.0

        text_lower = text.lower()
        matches = sum(1 for term in query_terms if term in text_lower)
        return matches / len(query_terms)

    def _citation_score(self, citations: int, max_citations: int) -> float:
        """Normalize citation count to 0-1 range using log scale."""
        if citations <= 0 or max_citations <= 0:
            return 0.0

        import math
        # Log scale normalization so a few highly-cited papers don't dominate
        return math.log1p(citations) / math.log1p(max_citations)

    def _recency_score(self, published_date: str) -> float:
        """Score paper recency. Newer = higher score."""
        if not published_date:
            return 0.3  # Default score for unknown dates

        try:
            # Parse date string
            date_str = published_date.split("T")[0]
            pub_date = datetime.strptime(date_str, "%Y-%m-%d")
            now = datetime.now()

            # Years since publication
            years_old = (now - pub_date).days / 365.25

            if years_old <= 1:
                return 1.0
            elif years_old <= 3:
                return 0.8
            elif years_old <= 5:
                return 0.6
            elif years_old <= 10:
                return 0.4
            else:
                return 0.2

        except (ValueError, TypeError):
            return 0.3
