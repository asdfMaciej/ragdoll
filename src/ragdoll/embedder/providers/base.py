import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseEmbedder(ABC):
    """Abstract base class for text and image embedding providers."""

    def __init__(self, model_name: str):
        """
        Initializes the embedding provider.

        Args:
            model_name: The name of the embedding model to use (e.g., 'text-embedding-3-small').
        """
        self.model_name = model_name
        logger.info(
            f"Initialized Embedding provider: {self.__class__.__name__} with model: {self.model_name}"
        )

    @property
    @abstractmethod
    def embedding_dimension(self) -> int:
        """
        Returns the dimensionality (the length of the vector) of the embeddings
        produced by the model.
        """
        pass

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """
        Generates an embedding for a single piece of text.

        Note: For embedding multiple texts, `embed_texts` is strongly preferred
        for performance and efficiency.

        Args:
            text: The input text to embed.

        Returns:
            A list of floats representing the embedding vector.

        Raises:
            Exception: For underlying API or processing errors.
        """
        pass

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Generates embeddings for a batch of texts.

        Args:
            texts: A list of texts to embed.

        Returns:
            A list of embedding vectors, where each vector is a list of floats.

        Raises:
            Exception: For underlying API or processing errors.
        """
        pass

    @abstractmethod
    def embed_image(self, image_path: str) -> list[float]:
        """
        Generates an embedding for a single image from its file path.

        Note: For embedding multiple images, `embed_images` is strongly preferred
        for performance and efficiency.

        Args:
            image_path: The local path to the image file.

        Returns:
            A list of floats representing the embedding vector.

        Raises:
            FileNotFoundError: If the image path does not exist.
            Exception: For underlying API or processing errors.
        """
        pass

    @abstractmethod
    def embed_images(self, image_paths: list[str]) -> list[list[float]]:
        """
        Generates embeddings for a batch of images from their file paths.

        Args:
            image_paths: A list of local paths to the image files.

        Returns:
            A list of embedding vectors, where each vector is a list of floats.

        Raises:
            FileNotFoundError: If any image path does not exist.
            Exception: For underlying API or processing errors.
        """
        pass
