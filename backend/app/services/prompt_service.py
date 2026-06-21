import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class PromptService:
    def __init__(self):
        # Base instructions for the LLM to maintain grounding and citations
        self.system_instructions = (
            "You are a helpful and precise academic assistant. Your goal is to answer the user's question "
            "based ONLY on the provided context notes below. Follow these strict rules:\n"
            "1. Grounding: Answer the question using ONLY the provided text segments. If the answer "
            "cannot be reasonably inferred from the context, respond with 'I don't know based on the provided notes.'\n"
            "2. No Hallucinations: Do not assume, extrapolate, or make up facts. Your answer must be fully backed "
            "by the text.\n"
            "3. Citations: Every fact or claim you make must cite the source note document and page number. "
            "Format citations inline, for example: (Source: DBMS Notes - Page 12) or at the end of statements.\n"
            "4. Formatting: Keep your answers clear, educational, and structured."
        )

    def build_prompt(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        """
        Formats retrieved segments and user query into a grounded RAG prompt.
        
        Args:
            query (str): User's search query or question.
            chunks (List[Dict[str, Any]]): Retrieved chunks with metadata.
            
        Returns:
            str: Grounded prompt template.
        """
        logger.info(f"Building prompt for query='{query}' with {len(chunks)} context chunk(s).")
        
        # 1. Format Context Segments
        context_str = ""
        if not chunks:
            context_str = "[No matching notes context available]"
        else:
            for idx, chunk in enumerate(chunks):
                meta = chunk.get("metadata", {})
                filename = meta.get("filename", "Unknown File")
                page = meta.get("page", "Unknown Page")
                source = meta.get("source", f"{filename} - Page {page}")
                text = chunk.get("text", "").strip()
                
                context_str += f"Segment [{idx + 1}]:\n"
                context_str += f"Source: {source}\n"
                context_str += f"Content:\n{text}\n"
                context_str += "-" * 50 + "\n"

        # 2. Assemble RAG Prompt
        prompt = (
            f"=== SYSTEM INSTRUCTIONS ===\n"
            f"{self.system_instructions}\n\n"
            f"=== NOTES CONTEXT ===\n"
            f"{context_str}\n"
            f"=== USER QUERY ===\n"
            f"Question: {query}\n\n"
            f"Answer:"
        )
        
        return prompt
