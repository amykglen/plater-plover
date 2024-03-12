import pytest


def pytest_addoption(parser):
    parser.addoption("--endpoint", action="store", default="http://localhost:9990")
    parser.addoption("--querypath", action="store", default="")
    parser.addoption("--issetfalse", action="store_true", default=False)
    parser.addoption("--issettrue", action="store_true", default=False)
    parser.addoption("--issetunpinned", action="store_true", default=False)


def pytest_configure(config):
    pytest.endpoint = config.getoption("--endpoint").strip("/")
    pytest.querypath = config.getoption("--querypath").strip("/")
    pytest.issetfalse = config.getoption("--issetfalse")
    pytest.issettrue = config.getoption("--issettrue")
    pytest.issetunpinned = config.getoption("--issetunpinned")
