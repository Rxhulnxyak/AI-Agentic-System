import os
import pytest
from config import settings
from logger import logger
from utils import ensure_dir

def test_config_loading():
    """Verify that configuration loads and has default values."""
    assert settings.system.log_level in ["INFO", "DEBUG", "WARNING", "ERROR"]
    assert settings.voice.wake_word == "nova"

def test_logger_initialization():
    """Verify that the logger is functional."""
    try:
        logger.info("Test log message")
        assert True
    except Exception as e:
        pytest.fail(f"Logger failed to initialize: {e}")

def test_ensure_dir():
    """Verify directory creation utility."""
    test_dir = "test_dir_delete_me"
    ensure_dir(test_dir)
    assert os.path.exists(test_dir)
    os.rmdir(test_dir)
