# In a file like app/providers/openai_provider.py

import logging
from pathlib import Path

import openai

from .base import BaseEmbedder

logger = logging.getLogger(__name__)

# This provider is now specialized for models that support the 'dimensions' parameter.
SUPPORTED_MODELS = {
    "text-embedding-3-small",
    "text-embedding-3-large"
}

# The dimension is now a fixed constant for this provider implementation.
FIXED_EMBEDDING_DIMENSION = 1024


class OpenAIEmbedder(BaseEmbedder):
    """
    Concrete implementation for generating embeddings using OpenAI's API.
    This provider is configured to ALWAYS return embeddings with a fixed
    dimension of 1024.
    """

    def __init__(self, model_name: str):
        super().__init__(model_name)
        if model_name not in SUPPORTED_MODELS:
            raise ValueError(
                f"Model '{model_name}' does not support custom dimensions and cannot be used with this provider. "
                f"Please use one of the following models: {list(SUPPORTED_MODELS)}"
            )

        try:
            self.client = openai.OpenAI()
            if not self.client.api_key:
                raise ValueError("OPENAI_API_KEY not found.")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise RuntimeError(
                "OpenAI API key is not configured. Please set the OPENAI_API_KEY environment variable."
            ) from e

        # The dimension is now hardcoded.
        self._dimension = FIXED_EMBEDDING_DIMENSION
        logger.info(
            f"OpenAIEmbeddingProvider configured for model '{self.model_name}' with a FIXED dimension of: {self._dimension}"
        )

    @property
    def embedding_dimension(self) -> int:
        """Returns the fixed dimensionality (1024) for the embeddings."""
        return self._dimension

    def embed_text(self, text: str) -> list[float]:
        """Generates an embedding for a single piece of text."""
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generates embeddings for a batch of texts."""
        if not texts:
            return []

        processed_texts = [text.replace("\n", " ") for text in texts]

        try:
            # The 'dimensions' parameter is now always passed with the fixed value.
            response = self.client.embeddings.create(
                model=self.model_name,
                input=processed_texts,
                dimensions=self._dimension
            )
            embeddings = [item.embedding for item in response.data]
            logger.debug(f"Successfully generated {len(embeddings)} text embeddings using {self.model_name}.")
            return embeddings
        except openai.APIError as e:
            logger.error(f"OpenAI API error during text embedding: {e}")
            raise Exception("Failed to generate text embeddings due to an API error.") from e

    def embed_image(self, image_path: str) -> list[float]:
        """This functionality is not supported by standard OpenAI text embedding models."""
        raise NotImplementedError(
            "The OpenAI '/embeddings' API endpoint does not support image files."
        )

    def embed_images(self, image_paths: list[str]) -> list[list[float]]:
        """This functionality is not supported by standard OpenAI text embedding models."""
        for path in image_paths:
            if not Path(path).is_file():
                raise FileNotFoundError(f"Image file not found at path: {path}")
        raise NotImplementedError(
            "The OpenAI '/embeddings' API endpoint does not support image files."
        )
