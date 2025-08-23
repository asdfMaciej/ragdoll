import sqlite3
from pathlib import Path

# Import the sqlite-vec extension
import sqlite_vec


class Database:
    """
    Manages the SQLite database connection and schema for the Ragdoll application.

    This class handles:
    - Connecting to the database file.
    - Loading the sqlite-vec extension.
    - Creating the necessary tables and indexes if they don't exist.
    - Providing a connection object for database operations.

    It is recommended to use this class as a context manager.
    """

    def __init__(
        self, db_path: Path = Path("ragdoll.sqlite3"), embedding_dim: int = 1024
    ):
        """
        Initializes the Database object and sets up the connection.

        Args:
            db_path: The path to the SQLite database file.
            embedding_dim: The dimension of the vectors to be stored.
                           This must match the output of your embedding model.
        """
        self.db_path = db_path
        self.embedding_dim = embedding_dim
        self.conn = None

        # Ensure the parent directory for the database file exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Access columns by name

            # Load the sqlite-vec extension
            self.conn.enable_load_extension(True)
            sqlite_vec.load(self.conn)
            self.conn.enable_load_extension(False)

            # Enable foreign key support
            self.conn.execute("PRAGMA foreign_keys = ON;")

            # Create the schema
            self._create_schema()

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            if self.conn:
                self.conn.close()
            raise

    def _create_schema(self):
        """
        Creates the database schema (tables, indexes, and triggers) if they don't exist.
        This method is idempotent.
        """
        with self.conn:
            # Table: files
            # Stores metadata for each source file.
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id           TEXT PRIMARY KEY, -- UUIDv7
                    path         TEXT NOT NULL UNIQUE,
                    content_hash TEXT NOT NULL,
                    is_dirty     INTEGER NOT NULL DEFAULT 1, -- Boolean (1=true, 0=false)
                    indexed_at   TEXT,             -- ISO 8601 datetime string
                    metadata     TEXT,             -- JSON string
                    created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Trigger to automatically update the 'updated_at' timestamp on files table
            self.conn.execute("""
                CREATE TRIGGER IF NOT EXISTS trigger_files_updated_at
                AFTER UPDATE ON files
                FOR EACH ROW
                BEGIN
                    UPDATE files SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
                END;
            """)

            # Index on file paths for fast lookups
            self.conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_files_path ON files(path);
            """)

            # Virtual Table: chunks
            # ... (rest of the method is unchanged) ...
            self.conn.execute(f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING vec0(
                    embedding   FLOAT[{self.embedding_dim}], -- The vector embedding
                    file_id     TEXT,                      -- Foreign key to files.id
                    chunk_index INTEGER,                   -- Order of the chunk in the file
                    content     TEXT                       -- The optional text content of the chunk
                );
            """)

    def close(self):
        """Closes the database connection if it is open."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Enter the runtime context related to this object."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the runtime context and close the connection."""
        self.close()
