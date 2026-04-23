"""Pytest fixtures + config."""

from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Don't pollute tests with a real .env; stub out external auth."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY", "test"))
    monkeypatch.setenv("DEEPGRAM_API_KEY", os.getenv("DEEPGRAM_API_KEY", "test"))
    monkeypatch.setenv("AZURE_SPEECH_KEY", os.getenv("AZURE_SPEECH_KEY", "test"))
    monkeypatch.setenv("AZURE_SPEECH_REGION", "westeurope")
    yield
