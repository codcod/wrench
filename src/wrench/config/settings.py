"""
Centralized configuration management for Wrench.

This module provides a unified way to load and validate configuration
from environment variables, config files, and defaults.
"""

import os
import logging
import typing as tp
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class BackstageSettings:
    """Configuration for Backstage API client."""

    base_url: str = ''
    token: str = ''
    timeout: float = 30.0
    max_retries: int = 3
    page_size: int = 100

    def validate(self) -> tp.List[str]:
        """Validate settings and return list of errors."""
        errors = []
        if not self.base_url:
            errors.append('Backstage base_url is required')
        if not self.token:
            errors.append('Backstage token is required')
        if self.timeout <= 0:
            errors.append('Timeout must be positive')
        if self.max_retries < 0:
            errors.append('Max retries cannot be negative')
        if self.page_size <= 0:
            errors.append('Page size must be positive')
        return errors


@dataclass
class BambooHRSettings:
    """Configuration for BambooHR API client."""

    domain: str = ''
    token: str = ''
    timeout: float = 30.0
    max_retries: int = 3

    def validate(self) -> tp.List[str]:
        """Validate settings and return list of errors."""
        errors = []
        if not self.domain:
            errors.append('BambooHR domain is required')
        if not self.token:
            errors.append('BambooHR token is required')
        if self.timeout <= 0:
            errors.append('Timeout must be positive')
        if self.max_retries < 0:
            errors.append('Max retries cannot be negative')
        return errors


@dataclass
class LoggingSettings:
    """Configuration for logging."""

    level: str = 'INFO'
    format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format: str = '%Y-%m-%d %H:%M:%S'
    file_path: tp.Optional[str] = None
    max_bytes: int = 10_000_000  # 10MB
    backup_count: int = 5

    def validate(self) -> tp.List[str]:
        """Validate logging settings."""
        errors = []
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if self.level.upper() not in valid_levels:
            errors.append(
                f'Invalid log level: {self.level}. Must be one of {valid_levels}'
            )
        return errors

    def __post_init__(self):
        """Normalize log level to uppercase."""
        self.level = self.level.upper()


@dataclass
class Settings:
    """Main settings container."""

    backstage: BackstageSettings = field(default_factory=BackstageSettings)
    bamboohr: BambooHRSettings = field(default_factory=BambooHRSettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)
    config_file: tp.Optional[str] = None

    @classmethod
    def load_from_env(cls) -> 'Settings':
        """Load settings from environment variables."""
        backstage = BackstageSettings(
            base_url=os.getenv('BACKSTAGE_BASE_URL', ''),
            token=os.getenv('BACKSTAGE_TOKEN', ''),
            timeout=float(os.getenv('BACKSTAGE_TIMEOUT', '30.0')),
            max_retries=int(os.getenv('BACKSTAGE_MAX_RETRIES', '3')),
            page_size=int(os.getenv('BACKSTAGE_PAGE_SIZE', '100')),
        )

        bamboohr = BambooHRSettings(
            domain=os.getenv('BAMBOOHR_DOMAIN', ''),
            token=os.getenv('BAMBOOHR_TOKEN', ''),
            timeout=float(os.getenv('BAMBOOHR_TIMEOUT', '30.0')),
            max_retries=int(os.getenv('BAMBOOHR_MAX_RETRIES', '3')),
        )

        logging_settings = LoggingSettings(
            level=os.getenv('LOG_LEVEL', 'INFO'),
            format=os.getenv(
                'LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ),
            date_format=os.getenv('LOG_DATE_FORMAT', '%Y-%m-%d %H:%M:%S'),
            file_path=os.getenv('LOG_FILE_PATH'),
            max_bytes=int(os.getenv('LOG_MAX_BYTES', '10000000')),
            backup_count=int(os.getenv('LOG_BACKUP_COUNT', '5')),
        )

        return cls(
            backstage=backstage,
            bamboohr=bamboohr,
            logging=logging_settings,
            config_file=os.getenv('WRENCH_CONFIG_FILE'),
        )

    def configure_logging(self):
        """Configure logging based on current settings."""
        import logging.handlers

        # Set log level
        logging.getLogger().setLevel(getattr(logging, self.logging.level))

        # Create formatter
        formatter = logging.Formatter(
            fmt=self.logging.format, datefmt=self.logging.date_format
        )

        # Configure console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logging.getLogger().addHandler(console_handler)

        # Configure file handler if specified
        if self.logging.file_path:
            file_handler = logging.handlers.RotatingFileHandler(
                filename=self.logging.file_path,
                maxBytes=self.logging.max_bytes,
                backupCount=self.logging.backup_count,
            )
            file_handler.setFormatter(formatter)
            logging.getLogger().addHandler(file_handler)

    def validate(self) -> tp.List[str]:
        """
        Validate all settings and return list of errors.

        Returns:
            List of validation error messages. Empty if valid.
        """
        errors = []

        # Collect errors from all sub-settings
        errors.extend([f'Backstage: {e}' for e in self.backstage.validate()])
        errors.extend([f'BambooHR: {e}' for e in self.bamboohr.validate()])
        errors.extend([f'Logging: {e}' for e in self.logging.validate()])

        return errors


# Global settings instance
_settings: tp.Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get the global settings instance.

    Returns:
        Global settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings.load_from_env()
    return _settings


def reload_settings() -> Settings:
    """
    Reload settings from environment.

    Returns:
        Reloaded settings instance
    """
    global _settings
    _settings = Settings.load_from_env()
    return _settings
