class NaiveChunker:
    def __init__(self, chunk_size: int = 8192, overlap: int = 2000):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be a positive integer.")

        if overlap >= chunk_size:
            raise ValueError("overlap must be less than chunk_size.")

        if overlap < 0:
            raise ValueError("overlap must be a non-negative integer.")

        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        """Splits the text into chunks of a specified size with overlap."""
        # Handle the edge case of empty input text.
        if not text:
            return []

        chunks = []
        start = 0
        step = self.chunk_size - self.overlap
        
        # The loop continues creating chunks until the entire text is covered.
        while True:
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)

            if end >= len(text):
                break
            
            start += step
            
        return chunks

