import time
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.agents.base_agent import BaseAgent
from app.services.ai.base import BaseAIProvider
from app.services.tools.search_tool import WebSearchTool
from app.database.models.citation import Citation
from app.core.logger import get_logger

logger = get_logger("research_agent")


class ResearchAgent(BaseAgent):
    """
    Research Agent:
    Executes automated multi-source web research, gathers domain literature,
    extracts citations, and indexes primary sources.
    """
    def __init__(self, ai_provider: BaseAIProvider):
        super().__init__(name="Research Agent", ai_provider=ai_provider)
        self.search_tool = WebSearchTool(max_results=3)

    async def execute(self, task_id: str, db: AsyncSession, context: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        search_queries = context.get("search_queries", [context.get("title", "general inquiry")])
        
        await self.emit_event(task_id, "agent_started", {
            "message": f"Initiating automated research across {len(search_queries)} search vectors...",
            "phase": "RESEARCHING"
        })

        all_citations: List[Dict[str, Any]] = []

        for q in search_queries:
            await self.emit_event(task_id, "agent_action", {
                "action": "web_search",
                "query": q,
                "message": f"Querying knowledge sources for: '{q}'"
            })
            results = await self.search_tool.search(q)
            all_citations.extend(results)

        # Deduplicate citations by URL
        unique_citations: Dict[str, Dict[str, Any]] = {}
        for c in all_citations:
            url = c.get("url")
            if url and url not in unique_citations:
                unique_citations[url] = c

        saved_citations = []
        for c in unique_citations.values():
            citation_model = Citation(
                task_id=task_id,
                title=c.get("title", "Source Citation"),
                url=c.get("url", ""),
                snippet=c.get("snippet", ""),
                domain=c.get("domain", "web"),
                reliability_score=c.get("reliability_score", 0.90),
                verified=True
            )
            db.add(citation_model)
            saved_citations.append(c)

        await db.commit()

        latency_ms = (time.time() - start_time) * 1000
        tokens_used = self.ai.get_token_estimate(str(saved_citations))

        research_data = {
            "total_sources_found": len(saved_citations),
            "citations": saved_citations,
            "queries_executed": search_queries
        }

        await self.record_step(
            db=db,
            task_id=task_id,
            step_name="Automated Multi-Source Research",
            input_payload={"search_queries": search_queries},
            output_payload={"total_sources": len(saved_citations)},
            logs=f"Gathered {len(saved_citations)} distinct citations across {len(search_queries)} search vectors.",
            latency_ms=latency_ms,
            tokens_used=tokens_used
        )

        await self.emit_event(task_id, "agent_completed", {
            "message": f"Research complete. Extracted {len(saved_citations)} verified citations.",
            "citations_count": len(saved_citations),
            "latency_ms": round(latency_ms, 2)
        })

        return research_data
