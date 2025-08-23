"""Database configuration management."""

import os
from typing import Optional
from pathlib import Path


class DatabaseConfig:
    """Database configuration class with environment variable support."""
    
    def __init__(self):
        self.database_url = self._get_database_url()
        self.echo_sql = self._get_bool_env("DB_ECHO", False)
        self.pool_size = self._get_int_env("DB_POOL_SIZE", 5)
        self.max_overflow = self._get_int_env("DB_MAX_OVERFLOW", 10)
        self.pool_timeout = self._get_int_env("DB_POOL_TIMEOUT", 30)
        
    def _get_database_url(self) -> str:
        """Get database URL from environment or use default."""
        # Check environment variable first
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            return db_url
            
        # Use default SQLite database
        db_dir = Path(__file__).parent.parent.parent / "Database"
        db_dir.mkdir(exist_ok=True)
        db_path = db_dir / "app_database.db"
        return f"sqlite:///{db_path}"
    
    def _get_bool_env(self, key: str, default: bool) -> bool:
        """Get boolean value from environment variable."""
        value = os.getenv(key, "").lower()
        if value in ("true", "1", "yes", "on"):
            return True
        elif value in ("false", "0", "no", "off"):
            return False
        return default
    
    def _get_int_env(self, key: str, default: int) -> int:
        """Get integer value from environment variable."""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default

    @property
    def is_sqlite(self) -> bool:
        """Check if the database is SQLite."""
        return self.database_url.startswith("sqlite")
    
    @property
    def connect_args(self) -> dict:
        """Get connection arguments based on database type."""
        if self.is_sqlite:
            return {"check_same_thread": False}
        return {}


# Global config instance
db_config = DatabaseConfig()
