# -*- coding: utf-8 -*-
"""
LLM module initialization
"""
from app.llm.base import LLMClient, LLMResponse
from app.llm.openai_compatible import OpenAICompatibleClient
from app.llm.anthropic import AnthropicClient


def create_llm_client(provider_config: dict) -> LLMClient:
    """
    Factory function to create LLM client

    Args:
        provider_config: Provider configuration dict with keys:
            - api_type: 'openai' or 'anthropic'
            - api_key: API key
            - base_url: Base URL (optional)
            - default_model: Model name (user input, required)

    Returns:
        LLMClient instance
    """
    api_type = provider_config.get('api_type', 'openai')
    api_key = provider_config.get('api_key', '')
    base_url = provider_config.get('base_url')
    model = provider_config.get('default_model', '')

    if api_type == 'anthropic':
        return AnthropicClient(
            api_key=api_key,
            base_url=base_url,
            model=model
        )
    else:
        return OpenAICompatibleClient(
            api_key=api_key,
            base_url=base_url,
            model=model
        )


def get_llm_client(api_type: str, api_key: str, base_url: str = None, model: str = None) -> LLMClient:
    """
    Get LLM client by parameters

    Args:
        api_type: API type ('openai' or 'anthropic')
        api_key: API key
        base_url: Base URL (optional)
        model: Model name (user input)

    Returns:
        LLMClient instance
    """
    return create_llm_client({
        'api_type': api_type,
        'api_key': api_key,
        'base_url': base_url,
        'default_model': model
    })


__all__ = [
    'LLMClient', 'LLMResponse',
    'OpenAICompatibleClient', 'AnthropicClient',
    'create_llm_client', 'get_llm_client'
]