import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: 需要真实 FMP API Key 才能运行")
