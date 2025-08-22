from .providers import BaseEmbedder
import logging


logger = logging.getLogger(__name__)


def get_embedder(config_string: str) -> BaseEmbedder:
    logger.info(
        f"Attempting to create Embedding provider for config: '{config_string}'"
    )
    try:
        provider_prefix, model_name = config_string.strip().lower().split("/", 1)
    except ValueError:
        raise ValueError(
            f"Invalid Embedding configuration format: '{config_string}'. "
            "Expected format: 'provider/model_name' (e.g., 'openai/text-embedding-3-small')."
        )

    if provider_prefix == "openai":
        # Assuming the concrete provider is in a file named openai_provider.py
        from .providers import OpenAIEmbedder

        return OpenAIEmbedder(model_name=model_name)
    elif provider_prefix == "mock":
        from .providers import MockEmbedder

        return MockEmbedder(model_name=model_name)
    else:
        raise ValueError(
            f"Unsupported Embedding provider prefix: '{provider_prefix}'. Supported prefixes: 'openai'."
        )
