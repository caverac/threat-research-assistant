"""Shared fixtures for infra tests."""

import aws_cdk as cdk
import pytest


@pytest.fixture
def app() -> cdk.App:
    """Create a CDK App for stack synthesis in tests."""
    return cdk.App()
