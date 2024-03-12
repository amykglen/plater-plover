import pytest


def pytest_addoption(parser):
    parser.addoption("--endpoint", action="store", default="http://localhost:9990")
    parser.addoption("--querypath", action="store", default="")


def pytest_configure(config):
    pytest.endpoint = config.getoption("--endpoint").strip("/")
    pytest.querypath = config.getoption("--querypath").strip("/")
