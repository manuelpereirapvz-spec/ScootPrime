"""Application configuration for different environments."""
import os
from pathlib import Path


class Config:
    """Base configuration."""

    SECRET_KEY = os.environ.get("SCOOTPRIME_SECRET", "dev-scootprime-local")
    INSTANCE_PATH = Path(os.environ.get("INSTANCE_PATH", "instance"))

    @property
    def DATABASE(self):
        return str(self.INSTANCE_PATH / "scootprime.db")

    @property
    def BACKUP_DIR(self):
        return str(self.INSTANCE_PATH / "backups")

    @property
    def BRAND_DIR(self):
        return str(self.INSTANCE_PATH / "brand")


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get("SCOOTPRIME_SECRET")


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    DEBUG = True


def get_config():
    """Get configuration based on environment."""

    env = os.environ.get("FLASK_ENV", "development")
    if env == "production":
        config = ProductionConfig()
        if not config.SECRET_KEY:
            raise ValueError("SCOOTPRIME_SECRET must be set in production")
        return config
    if env == "testing":
        return TestingConfig()
    return DevelopmentConfig()
