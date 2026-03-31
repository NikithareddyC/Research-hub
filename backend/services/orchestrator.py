"""Search Orchestrator - Coordinates parallel search across all sources"""

import asyncio
import time
import logging
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor

from services.arxiv_service import ArxivService
from services.crossref_service import CrossrefService
from services.core_service import CoreService
from services.openalex_service import OpenAlexService
from services.pubmed_service import PubMedService
from services.deduplicator import Deduplicator
from services.relevance_scorer import RelevanceScorer

logger = logging.getLogger(__name__)


class SearchOrchestrator:
    """
    Coordinates search across multiple academic databases.
    
    Flow:
    1. Search all selected sources in parallel
    2. Merge results
    3. Deduplicate
    4. Score relevance
    5. Generate summaries (from abstracts)
    6. Sort and return
    """

    def __init__(self, core_api_key: str = "", crossref_api_key: str = "", openalex_email: str = ""):
        self.services = {
            "arxiv": ArxivService(),
            "crossref": CrossrefService(api_key=crossref_api_key),
            "core": CoreService(api_key=core_api_key),
            "openalex": OpenAlexService(email=openalex_email),
            "pubmed": PubMedService(),
        }
        self.deduplicator = Deduplicator()
        self.scorer = RelevanceScorer()

    async def search(
        self,
        query: str,
        sources: List[str],
        limit: int = 100,
        sort_by: str = "relevance",
    ) -> Dict:
        """
        Execute search across selected sources and return processed results.
        
        Args:
            query: Search keywords
            sources: List of source names to search
            limit: Max total papers to return
            sort_by: Sort method (relevance, date, citations)
            
        Returns:
            Dict with papers list, total count, and search time
        """
        start_time = time.time()
        logger.info(f"[Orchestrator] Starting search: '{query}' across {sources}")

        # Per-source limit — keep small for speed (20 per source is plenty)
        per_source_limit = min(limit // max(len(sources), 1) + 5, 25)

        # Search all sources in parallel
        all_papers = await self._search_parallel(query, sources, per_source_limit)

        logger.info(f"[Orchestrator] Raw results: {len(all_papers)} papers from {len(sources)} sources")

        # Deduplicate
        unique_papers = self.deduplicator.deduplicate(all_papers)

        # Score relevance
        scored_papers = self.scorer.score_papers(unique_papers, query)

        # Generate summaries from abstracts
        for paper in scored_papers:
            if not paper.get("summary"):
                paper["summary"] = self._generate_summary(paper)

        # Sort
        sorted_papers = self.scorer.sort_papers(scored_papers, sort_by)

        # Limit results
        final_papers = sorted_papers[:limit]

        search_time = round(time.time() - start_time, 2)
        logger.info(f"[Orchestrator] Search complete: {len(final_papers)} papers in {search_time}s")

        return {
            "papers": final_papers,
            "total_papers": len(final_papers),
            "search_time": search_time,
        }

    async def _search_parallel(
        self, query: str, sources: List[str], limit: int
    ) -> List[Dict]:
        """Search multiple sources concurrently."""
        tasks = []
        for source in sources:
            service = self.services.get(source)
            if service:
                tasks.append(self._search_source(service, query, limit))
            else:
                logger.warning(f"[Orchestrator] Unknown source: {source}")

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_papers = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"[Orchestrator] Source {sources[i]} failed: {str(result)}")
            elif isinstance(result, list):
                all_papers.extend(result)

        return all_papers

    async def _search_source(self, service, query: str, limit: int) -> List[Dict]:
        """Search a single source with a 10-second timeout."""
        try:
            loop = asyncio.get_running_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: asyncio.run(service.search(query, limit))
                ),
                timeout=10.0
            )
            return result
        except asyncio.TimeoutError:
            logger.warning(f"[Orchestrator] {service.source_name} timed out after 10s")
            return []
        except Exception as e:
            logger.error(f"[Orchestrator] Error searching {service.source_name}: {str(e)}")
            return []

    def _generate_summary(self, paper: Dict) -> str:
        """
        Generate a summary from paper abstract.
        For MVP: Extract first 2-3 sentences from abstract.
        Future: Use transformers for abstractive summarization.
        """
        abstract = paper.get("abstract", "")
        if not abstract:
            return f"Research paper on {paper.get('title', 'unknown topic')}. Published by {', '.join(paper.get('authors', ['Unknown'])[:2])}."

        # Simple extractive summary: first 2-3 sentences
        sentences = []
        current = ""
        for char in abstract:
            current += char
            if char in ".!?" and len(current.strip()) > 20:
                sentences.append(current.strip())
                current = ""
                if len(sentences) >= 3:
                    break

        if sentences:
            summary = " ".join(sentences)
            # Cap at 300 chars
            if len(summary) > 300:
                summary = summary[:297] + "..."
            return summary

        # Fallback: truncate abstract
        if len(abstract) > 300:
            return abstract[:297] + "..."
        return abstract
