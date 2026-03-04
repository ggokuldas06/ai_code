"""LangChain OpenAI LLM integration."""

from langchain_openai import ChatOpenAI

from aicode.config import AICodeConfig


def create_llm(config: AICodeConfig) -> ChatOpenAI:
    """Create a configured OpenAI LLM instance."""
    return ChatOpenAI(
        model=config.model_name,
        openai_api_key=config.openai_api_key,
        temperature=0.2,
    )
