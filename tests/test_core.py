"""Tests for the loop_engineering package."""

import loop_engineering
from loop_engineering.core import greet


def test_version():
    assert loop_engineering.__version__ == "0.1.0"


def test_greet_default():
    result = greet()
    assert result == "Hello, World! Welcome to Loop Engineering."


def test_greet_with_name():
    result = greet("Engineer")
    assert result == "Hello, Engineer! Welcome to Loop Engineering."
