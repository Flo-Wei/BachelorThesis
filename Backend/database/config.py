"""
Database configuration management for the competency assessment system.

This module provides configuration classes and utilities for managing
database connections across different environments and database types.
The configuration is designed to be flexible and support easy migration
between database systems.

Classes:
    DatabaseType: Enumeration of supported database types
    DatabaseConfig: Configuration container for database settings
"""

import os
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any
from urllib.parse import urlparse


class DatabaseType(Enum):
    """
    Enumeration of supported database types.
    
    This enum defines the database systems that the application can work with.
    The implementation uses SQLAlchemy, so any SQLAlchemy-supported database
    can be added here.
    """
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    ORACLE = "oracle"
    MSSQL = "mssql"
    
    @classmethod
    def from_url(cls, url: str) -> 'DatabaseType':
        """
        Determine database type from connection URL.
        
        Args:
            url: Database connection URL
            
        Returns:
            DatabaseType: Detected database type
            
        Raises:
            ValueError: If database type cannot be determined
        """
        parsed = urlparse(url)
        scheme = parsed.scheme.split('+')[0]  # Handle cases like postgresql+psycopg2
        
        type_mapping = {
            'sqlite': cls.SQLITE,
            'postgresql': cls.POSTGRESQL,
            'postgres': cls.POSTGRESQL,
            'mysql': cls.MYSQL,
            'oracle': cls.ORACLE,
            'mssql': cls.MSSQL,
            'sqlserver': cls.MSSQL
        }
        
        db_type = type_mapping.get(scheme)
        if not db_type:
            raise ValueError(f"Unsupported database type: {scheme}")
        
        return db_type


@dataclass
class DatabaseConfig:
    """
    Configuration container for database connection settings.
    
    This class encapsulates all database configuration parameters and provides
    methods for creating connection URLs and validating settings. It supports
    both URL-based configuration and individual parameter configuration.
    
    Attributes:
        database_type: Type of database system
        host: Database server hostname
        port: Database server port
        database: Database name
        username: Database username
        password: Database password
        driver: SQLAlchemy driver name (optional)
        options: Additional connection options
        connection_url: Full connection URL (if provided directly)
        pool_size: Connection pool size
        pool_timeout: Connection pool timeout in seconds
        pool_recycle: Connection pool recycle time in seconds
        echo: Whether to echo SQL statements (for debugging)
    """
    
    database_type: DatabaseType = DatabaseType.SQLITE
    host: str = ""
    port: Optional[int] = None
    database: str = "competency_assessment.db"
    username: str = ""
    password: str = ""
    driver: Optional[str] = None
    options: Dict[str, Any] = None
    connection_url: Optional[str] = None
    pool_size: int = 5
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False
    
    def __post_init__(self):
        """Initialize default values and validate configuration."""
        if self.options is None:
            self.options = {}
        
        # Set default ports for database types
        if self.port is None:
            default_ports = {
                DatabaseType.POSTGRESQL: 5432,
                DatabaseType.MYSQL: 3306,
                DatabaseType.ORACLE: 1521,
                DatabaseType.MSSQL: 1433
            }
            self.port = default_ports.get(self.database_type)
        
        # Set default drivers
        if self.driver is None:
            default_drivers = {
                DatabaseType.SQLITE: None,  # No driver needed for SQLite
                DatabaseType.POSTGRESQL: "psycopg2",
                DatabaseType.MYSQL: "pymysql",
                DatabaseType.ORACLE: "cx_oracle",
                DatabaseType.MSSQL: "pyodbc"
            }
            self.driver = default_drivers.get(self.database_type)
    
    @classmethod
    def from_url(cls, url: str, **kwargs) -> 'DatabaseConfig':
        """
        Create configuration from database URL.
        
        Args:
            url: Database connection URL
            **kwargs: Additional configuration parameters
            
        Returns:
            DatabaseConfig: Configuration instance
        """
        return cls(
            database_type=DatabaseType.from_url(url),
            connection_url=url,
            **kwargs
        )
    
    @classmethod
    def from_environment(cls, prefix: str = "DB_") -> 'DatabaseConfig':
        """
        Create configuration from environment variables.
        
        Args:
            prefix: Prefix for environment variable names
            
        Returns:
            DatabaseConfig: Configuration instance
        """
        return cls(
            database_type=DatabaseType(os.getenv(f"{prefix}TYPE", "sqlite")),
            host=os.getenv(f"{prefix}HOST", ""),
            port=int(os.getenv(f"{prefix}PORT", "0")) or None,
            database=os.getenv(f"{prefix}DATABASE", "competency_assessment.db"),
            username=os.getenv(f"{prefix}USERNAME", ""),
            password=os.getenv(f"{prefix}PASSWORD", ""),
            driver=os.getenv(f"{prefix}DRIVER"),
            pool_size=int(os.getenv(f"{prefix}POOL_SIZE", "5")),
            pool_timeout=int(os.getenv(f"{prefix}POOL_TIMEOUT", "30")),
            pool_recycle=int(os.getenv(f"{prefix}POOL_RECYCLE", "3600")),
            echo=os.getenv(f"{prefix}ECHO", "false").lower() == "true"
        )
    
    @classmethod
    def sqlite(cls, database_path: str = "competency_assessment.db", **kwargs) -> 'DatabaseConfig':
        """
        Create SQLite configuration.
        
        Args:
            database_path: Path to SQLite database file
            **kwargs: Additional configuration parameters
            
        Returns:
            DatabaseConfig: SQLite configuration
        """
        return cls(
            database_type=DatabaseType.SQLITE,
            database=database_path,
            **kwargs
        )
    
    @classmethod
    def postgresql(cls, host: str = "localhost", database: str = "competency_assessment",
                   username: str = "", password: str = "", port: int = 5432,
                   **kwargs) -> 'DatabaseConfig':
        """
        Create PostgreSQL configuration.
        
        Args:
            host: PostgreSQL server host
            database: Database name
            username: Database username
            password: Database password
            port: PostgreSQL server port
            **kwargs: Additional configuration parameters
            
        Returns:
            DatabaseConfig: PostgreSQL configuration
        """
        return cls(
            database_type=DatabaseType.POSTGRESQL,
            host=host,
            port=port,
            database=database,
            username=username,
            password=password,
            **kwargs
        )
    
    def get_connection_url(self) -> str:
        """
        Generate SQLAlchemy connection URL.
        
        Returns:
            str: Database connection URL
        """
        if self.connection_url:
            return self.connection_url
        
        if self.database_type == DatabaseType.SQLITE:
            return f"sqlite:///{self.database}"
        
        # Build URL for other database types
        scheme = self.database_type.value
        if self.driver:
            scheme += f"+{self.driver}"
        
        url_parts = [f"{scheme}://"]
        
        if self.username:
            url_parts.append(self.username)
            if self.password:
                url_parts.append(f":{self.password}")
            url_parts.append("@")
        
        if self.host:
            url_parts.append(self.host)
            if self.port:
                url_parts.append(f":{self.port}")
        
        if self.database:
            url_parts.append(f"/{self.database}")
        
        # Add options as query parameters
        if self.options:
            query_params = "&".join(f"{k}={v}" for k, v in self.options.items())
            url_parts.append(f"?{query_params}")
        
        return "".join(url_parts)
    
    def get_engine_options(self) -> Dict[str, Any]:
        """
        Get SQLAlchemy engine options.
        
        Returns:
            Dict[str, Any]: Engine configuration options
        """
        options = {
            "echo": self.echo,
            "pool_pre_ping": True,  # Validate connections before use
        }
        
        # Add pooling options for non-SQLite databases
        if self.database_type != DatabaseType.SQLITE:
            options.update({
                "pool_size": self.pool_size,
                "pool_timeout": self.pool_timeout,
                "pool_recycle": self.pool_recycle,
                "max_overflow": 10  # Allow up to 10 additional connections
            })
        
        return options
    
    def validate(self) -> bool:
        """
        Validate the configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        try:
            # Check if connection URL can be generated
            url = self.get_connection_url()
            
            # Basic validation for required fields
            if self.database_type != DatabaseType.SQLITE:
                if not self.host or not self.database:
                    return False
            else:
                if not self.database:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dict[str, Any]: Configuration as dictionary
        """
        return {
            "database_type": self.database_type.value,
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "username": self.username,
            "password": "***" if self.password else "",  # Mask password
            "driver": self.driver,
            "options": self.options,
            "pool_size": self.pool_size,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "echo": self.echo
        }
    
    def __repr__(self) -> str:
        """Return string representation of the configuration."""
        return f"DatabaseConfig(type={self.database_type.value}, database={self.database})"


# Predefined configurations for different environments
class ConfigPresets:
    """Predefined database configurations for common scenarios."""
    
    @staticmethod
    def development() -> DatabaseConfig:
        """Development configuration using SQLite."""
        return DatabaseConfig.sqlite(
            database_path="development.db",
            echo=True  # Enable SQL logging for development
        )
    
    @staticmethod
    def testing() -> DatabaseConfig:
        """Testing configuration using in-memory SQLite."""
        return DatabaseConfig.sqlite(
            database_path=":memory:",
            echo=False
        )
    
    @staticmethod
    def production_postgres() -> DatabaseConfig:
        """Production configuration template for PostgreSQL."""
        return DatabaseConfig.postgresql(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            database=os.getenv("POSTGRES_DB", "competency_assessment"),
            username=os.getenv("POSTGRES_USER", ""),
            password=os.getenv("POSTGRES_PASSWORD", ""),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            pool_size=20,
            pool_timeout=60,
            echo=False
        ) 