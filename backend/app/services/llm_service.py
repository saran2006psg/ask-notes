import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.client = None
        self.enabled = False
        
        try:
            api_key = os.environ.get("GROQ_API_KEY")
            if not api_key:
                logger.warning("Groq: GROQ_API_KEY environment variable is not set. Service offline.")
                return
                
            from groq import Groq
            self.client = Groq(api_key=api_key)
            self.enabled = True
            logger.info("Groq: Client successfully initialized.")
        except Exception as e:
            logger.error(f"Groq: Initialization failed: {e}")
            
    def generate_answer(self, prompt: str, model_name: str = "llama-3.1-8b-instant") -> str:
        """
        Calls Groq completions endpoint with a prompt to generate an answer.
        
        Args:
            prompt (str): Assembled RAG prompt.
            model_name (str): Groq chat model (default: llama-3.1-8b-instant).
            
        Returns:
            str: Generated answer.
        """
        if not self.enabled or self.client is None:
            logger.error("Groq: Client is offline.")
            return "Error: LLM service is offline. Please verify GROQ_API_KEY in your environment."
            
        try:
            logger.info(f"Groq: Requesting completion using model '{model_name}'...")
            
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=model_name,
                temperature=0.2, # Low temperature to prevent hallucinations
                max_tokens=1024
            )
            
            answer = chat_completion.choices[0].message.content
            logger.info("Groq: Successfully received response completion.")
            return answer
            
        except Exception as e:
            logger.error(f"Groq: Answer generation failed: {e}")
            return f"Error: Failed to generate response from Groq. (Details: {e})"
