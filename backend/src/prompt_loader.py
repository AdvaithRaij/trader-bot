"""
Prompt Loader Module
Centralized prompt management for AI interactions.
"""

import os
from pathlib import Path
from typing import Dict
from loguru import logger

# Get the prompts directory path
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class PromptLoader:
    """Loads and manages AI prompts from files."""
    
    def __init__(self):
        self.prompts_cache = {}
        self._load_all_prompts()
    
    def _load_all_prompts(self):
        """Load all prompt files into cache."""
        if not PROMPTS_DIR.exists():
            logger.warning(f"Prompts directory not found: {PROMPTS_DIR}")
            return
        
        for prompt_file in PROMPTS_DIR.glob("*.txt"):
            prompt_name = prompt_file.stem
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    self.prompts_cache[prompt_name] = f.read()
                logger.debug(f"✅ Loaded prompt: {prompt_name}")
            except Exception as e:
                logger.error(f"Error loading prompt {prompt_name}: {e}")
    
    def get_prompt(self, prompt_name: str, **kwargs) -> str:
        """
        Get a prompt by name and format it with provided variables.
        
        Args:
            prompt_name: Name of the prompt file (without .txt extension)
            **kwargs: Variables to format the prompt with
            
        Returns:
            Formatted prompt string
        """
        if prompt_name not in self.prompts_cache:
            logger.error(f"Prompt not found: {prompt_name}")
            return ""
        
        prompt_template = self.prompts_cache[prompt_name]
        
        try:
            # Format the prompt with provided variables
            formatted_prompt = prompt_template.format(**kwargs)
            return formatted_prompt
        except KeyError as e:
            logger.error(f"Missing variable in prompt {prompt_name}: {e}")
            return prompt_template
        except Exception as e:
            logger.error(f"Error formatting prompt {prompt_name}: {e}")
            return prompt_template
    
    def reload_prompts(self):
        """Reload all prompts from files (useful for development)."""
        self.prompts_cache.clear()
        self._load_all_prompts()
        logger.info("🔄 Prompts reloaded")
    
    def list_prompts(self) -> list:
        """List all available prompts."""
        return list(self.prompts_cache.keys())


# Singleton instance
prompt_loader = PromptLoader()


# Convenience functions
def get_trading_decision_prompt(**kwargs) -> str:
    """Get the trading decision prompt."""
    return prompt_loader.get_prompt("trading_decision", **kwargs)


def get_news_analysis_prompt(**kwargs) -> str:
    """Get the news analysis prompt."""
    return prompt_loader.get_prompt("news_analysis", **kwargs)


def get_sentiment_analysis_prompt(**kwargs) -> str:
    """Get the sentiment analysis prompt."""
    return prompt_loader.get_prompt("sentiment_analysis", **kwargs)


def get_trade_levels_prompt(**kwargs) -> str:
    """Get the trade levels prompt."""
    return prompt_loader.get_prompt("trade_levels", **kwargs)

