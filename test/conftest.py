import pytest


def pytest_addoption(parser):
    parser.addoption("--endpoint", action="store", default="http://localhost:9990")
    parser.addoption("--queryfile", action="store", default="")
    parser.addoption("--querydir", action="store", default="")


def pytest_configure(config):
    pytest.endpoint = config.getoption("--endpoint").strip("/")
    pytest.queryfile = config.getoption("--queryfile").strip("/")
    pytest.querydir = config.getoption("--querydir").strip("/")
