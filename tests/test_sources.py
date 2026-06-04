"""Tests for platform source directory loading and filtering."""

import pytest
from pathlib import Path


@pytest.fixture
def example_sources_yaml(tmp_path):
    """Write a minimal sources YAML to tmp_path."""
    content = """
sources:
  - name: Upwork
    url: https://www.upwork.com
    categories: [WEB_APP, AI_AUTOMATION]
    fee_notes: "10% flat fee"
    vetted: false
    region: global
    newcomer_friendly: true
    notes: "Large marketplace"
  - name: Toptal
    url: https://www.toptal.com
    categories: [WEB_APP, DATA_DASHBOARD]
    fee_notes: "No freelancer fee"
    vetted: true
    region: global
    newcomer_friendly: false
    notes: "Vetted top 3%"
  - name: Workana
    url: https://www.workana.com
    categories: [WEB_APP, DATA_DASHBOARD]
    fee_notes: "5-20%"
    vetted: false
    region: latam
    newcomer_friendly: true
    notes: "LATAM focus"
"""
    (tmp_path / "sources.yaml").write_text(content, encoding="utf-8")
    return str(tmp_path)


def test_load_sources_reads_yaml(example_sources_yaml):
    from freelance_os.sources import load_sources
    sources = load_sources(example_sources_yaml)
    assert len(sources) == 3
    names = [s["name"] for s in sources]
    assert "Upwork" in names
    assert "Toptal" in names


def test_load_sources_returns_empty_when_missing(tmp_path):
    from freelance_os.sources import load_sources
    sources = load_sources(str(tmp_path / "nonexistent"))
    assert sources == []


def test_load_sources_falls_back_to_example(tmp_path):
    """Falls back to sources.example.yaml when sources.yaml is absent."""
    content = """
sources:
  - name: TestPlatform
    url: https://example.com
    categories: [OTHER]
    vetted: false
    region: global
    newcomer_friendly: true
"""
    (tmp_path / "sources.example.yaml").write_text(content, encoding="utf-8")
    from freelance_os.sources import load_sources
    sources = load_sources(str(tmp_path))
    assert len(sources) == 1
    assert sources[0]["name"] == "TestPlatform"


def test_filter_by_category(example_sources_yaml):
    from freelance_os.sources import load_sources, filter_sources
    sources = load_sources(example_sources_yaml)
    ai_sources = filter_sources(sources, category="AI_AUTOMATION")
    assert len(ai_sources) == 1
    assert ai_sources[0]["name"] == "Upwork"


def test_filter_by_newcomer(example_sources_yaml):
    from freelance_os.sources import load_sources, filter_sources
    sources = load_sources(example_sources_yaml)
    newcomer = filter_sources(sources, newcomer=True)
    names = [s["name"] for s in newcomer]
    assert "Toptal" not in names
    assert "Upwork" in names
    assert "Workana" in names


def test_filter_by_region(example_sources_yaml):
    from freelance_os.sources import load_sources, filter_sources
    sources = load_sources(example_sources_yaml)
    latam = filter_sources(sources, region="latam")
    assert len(latam) == 1
    assert latam[0]["name"] == "Workana"


def test_filter_combined(example_sources_yaml):
    from freelance_os.sources import load_sources, filter_sources
    sources = load_sources(example_sources_yaml)
    # WEB_APP + newcomer_friendly
    result = filter_sources(sources, category="WEB_APP", newcomer=True)
    names = [s["name"] for s in result]
    assert "Toptal" not in names  # vetted=true, newcomer_friendly=false
    assert "Upwork" in names


def test_example_sources_yaml_loads():
    """The bundled sources.example.yaml is valid and contains expected platforms."""
    from freelance_os.sources import load_sources
    sources = load_sources("config")
    names = [s["name"] for s in sources]
    for expected in ["Upwork", "Fiverr", "Toptal", "Contra", "Codeable"]:
        assert expected in names, f"Expected {expected} in bundled sources"


def test_example_sources_categories_are_valid():
    """All categories in sources.example.yaml are valid JobCategory values."""
    from freelance_os.sources import load_sources
    from freelance_os.models import JobCategory
    valid = {c.value for c in JobCategory}
    sources = load_sources("config")
    for s in sources:
        for cat in s.get("categories", []):
            assert cat in valid, f"Platform {s['name']} has invalid category '{cat}'"
