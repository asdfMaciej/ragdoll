import os
import random
from .base import BaseEmbedder
import logging

logger = logging.getLogger(__name__)


class MockEmbedder(BaseEmbedder):
    """A mock implementation of EmbeddingProvider for testing purposes."""

    def __init__(self, model_name: str):
        super().__init__(model_name)
        self._dimension = 1024
        logger.info(f"MockEmbedder configured with dimension: {self._dimension}")

    @property
    def embedding_dimension(self) -> int:
        """Returns the pre-configured dimensionality."""
        return self._dimension

    def embed_text(self, text: str) -> list[float]:
        """Generates a mock embedding for a single text."""
        # For simplicity, delegate to the batch method.
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generates a batch of mock text embeddings."""
        logger.debug(f"Generating mock text embeddings for {len(texts)} texts.")
        embeddings = []
        for text in texts:
            # Create a deterministic-ish but unique vector for testing
            random.seed(hash(text))
            embeddings.append([random.random() for _ in range(self._dimension)])
        return embeddings

    def embed_image(self, image_path: str) -> list[float]:
        """Generates a mock embedding for a single image."""
        return self.embed_images([image_path])[0]

    def embed_images(self, image_paths: list[str]) -> list[list[float]]:
        """Generates a batch of mock image embeddings."""
        logger.debug(f"Generating mock image embeddings for {len(image_paths)} images.")
        embeddings = []
        for path in image_paths:
            if not os.path.exists(path):
                raise FileNotFoundError(
                    f"Mock provider error: Image not found at {path}"
                )
            # Create a vector based on the file path hash
            random.seed(hash(path))
            embeddings.append([random.random() for _ in range(self._dimension)])
        return embeddings
