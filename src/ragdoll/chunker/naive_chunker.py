class NaiveChunker:
    def __init__(self, chunk_size: int = 8192, overlap: int = 2000):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        """Splits the text into chunks of a specified size with overlap."""
        chunks = []
        for i in range(0, len(text), self.chunk_size - self.overlap):
            chunks.append(text[i:i + self.chunk_size])
        return chunks
