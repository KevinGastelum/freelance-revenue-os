"""Shared test fixtures."""

import pytest
import tempfile
from pathlib import Path

from freelance_os.db import init_db, reset_engine, get_engine
from freelance_os.models import Lead, LeadStatus


@pytest.fixture
def tmp_db(tmp_path):
    """Provide a temporary SQLite DB for each test."""
    db_path = tmp_path / "test.sqlite"
    reset_engine()
    init_db(db_path)
    yield db_path
    reset_engine()


@pytest.fixture
def sample_lead():
    """Return a sample Lead object (not persisted)."""
    return Lead(
        id=1,
        source="upwork",
        title="Build a Next.js dashboard with Supabase",
        description=(
            "We need a full-stack web application built with Next.js and Supabase. "
            "The app should include authentication, a dashboard with real-time data, "
            "and integration with our PostgreSQL database. Budget is $2,000-$3,000. "
            "Timeline is flexible. Client has 4.8 star rating and payment is verified. "
            "Looking for ongoing collaboration on future projects as well."
        ),
        budget_min=2000,
        budget_max=3000,
        client_rating=4.8,
        client_payment_verified=True,
        status=LeadStatus.NEW,
    )


@pytest.fixture
def low_quality_lead():
    """Return a low-quality lead."""
    return Lead(
        id=2,
        source="upwork",
        title="Quick fix needed ASAP",
        description=(
            "I need a simple quick fix done today only. "
            "Should be easy. Budget is $50. Do a test first for free. "
            "Contact me on Telegram. Let's connect outside Upwork."
        ),
        budget_min=50,
        budget_max=50,
        status=LeadStatus.NEW,
    )
