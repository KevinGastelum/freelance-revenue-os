"""Phase 6: Client delivery scaffold generator tests."""

import pytest
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _scaffold(tmp_path: Path, scaffold_type: str, name: str = "test-project", force: bool = False) -> Path:
    from freelance_os.client.scaffold import generate_scaffold
    return generate_scaffold(scaffold_type=scaffold_type, target_dir=tmp_path / name, name=name, force=force)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# SCAFFOLD_TYPES list
# ---------------------------------------------------------------------------

def test_scaffold_types_list():
    from freelance_os.client.scaffold import SCAFFOLD_TYPES
    assert "scraper" in SCAFFOLD_TYPES
    assert "data-pipeline" in SCAFFOLD_TYPES
    assert "powerbi" in SCAFFOLD_TYPES
    assert "nextjs" in SCAFFOLD_TYPES
    assert "wordpress" in SCAFFOLD_TYPES
    assert len(SCAFFOLD_TYPES) == 5


# ---------------------------------------------------------------------------
# Unknown type
# ---------------------------------------------------------------------------

def test_unknown_type_raises(tmp_path: Path):
    from freelance_os.client.scaffold import generate_scaffold
    with pytest.raises(ValueError, match="Unknown scaffold type"):
        generate_scaffold("bogus", tmp_path / "x", "x")


# ---------------------------------------------------------------------------
# No-overwrite guard
# ---------------------------------------------------------------------------

def test_no_overwrite_without_force(tmp_path: Path):
    from freelance_os.client.scaffold import generate_scaffold
    target = tmp_path / "guard-test"
    generate_scaffold("scraper", target, "guard-test")
    with pytest.raises(FileExistsError, match="already exists"):
        generate_scaffold("scraper", target, "guard-test", force=False)


def test_force_overwrites(tmp_path: Path):
    from freelance_os.client.scaffold import generate_scaffold
    target = tmp_path / "force-test"
    generate_scaffold("scraper", target, "force-test")
    # Should not raise
    result = generate_scaffold("scraper", target, "force-test", force=True)
    assert result == target


# ---------------------------------------------------------------------------
# Scraper scaffold
# ---------------------------------------------------------------------------

class TestScraperScaffold:
    def test_creates_scraper_py(self, tmp_path: Path):
        d = _scaffold(tmp_path, "scraper")
        assert (d / "scraper.py").exists()

    def test_creates_config_yaml(self, tmp_path: Path):
        d = _scaffold(tmp_path, "scraper")
        assert (d / "config.yaml").exists()

    def test_creates_output_dir(self, tmp_path: Path):
        d = _scaffold(tmp_path, "scraper")
        assert (d / "output").is_dir()

    def test_creates_test_stub(self, tmp_path: Path):
        d = _scaffold(tmp_path, "scraper")
        assert (d / "tests" / "test_scraper.py").exists()

    def test_creates_readme(self, tmp_path: Path):
        d = _scaffold(tmp_path, "scraper")
        assert (d / "README.md").exists()

    def test_creates_acceptance(self, tmp_path: Path):
        d = _scaffold(tmp_path, "scraper")
        assert (d / "ACCEPTANCE.md").exists()

    def test_creates_dispatch_brief(self, tmp_path: Path):
        d = _scaffold(tmp_path, "scraper")
        assert (d / "DISPATCH_BRIEF.md").exists()

    def test_dispatch_brief_contains_safety_reminder(self, tmp_path: Path):
        d = _scaffold(tmp_path, "scraper")
        content = _read(d / "DISPATCH_BRIEF.md")
        assert "DRAFT ONLY" in content
        assert "proxy rotation" in content.lower() or "challenge" in content.lower()

    def test_acceptance_has_criteria(self, tmp_path: Path):
        d = _scaffold(tmp_path, "scraper")
        content = _read(d / "ACCEPTANCE.md")
        assert "Acceptance Criteria" in content
        assert "Delivery Checklist" in content

    def test_scraper_py_contains_name(self, tmp_path: Path):
        d = _scaffold(tmp_path, "scraper", name="my-scraper")
        content = _read(d / "scraper.py")
        assert "my-scraper" in content

    def test_scraper_py_no_proxy_code(self, tmp_path: Path):
        d = _scaffold(tmp_path, "scraper")
        content = _read(d / "scraper.py")
        assert "proxy" not in content.lower()
        assert "captcha" not in content.lower()

    def test_config_has_target_url(self, tmp_path: Path):
        d = _scaffold(tmp_path, "scraper")
        content = _read(d / "config.yaml")
        assert "target_url" in content

    def test_all_files_utf8(self, tmp_path: Path):
        d = _scaffold(tmp_path, "scraper")
        for f in d.rglob("*.py"):
            assert isinstance(f.read_text(encoding="utf-8"), str)
        for f in d.rglob("*.md"):
            assert isinstance(f.read_text(encoding="utf-8"), str)
        for f in d.rglob("*.yaml"):
            assert isinstance(f.read_text(encoding="utf-8"), str)


# ---------------------------------------------------------------------------
# Data-pipeline scaffold
# ---------------------------------------------------------------------------

class TestDataPipelineScaffold:
    def test_creates_pipeline_py(self, tmp_path: Path):
        d = _scaffold(tmp_path, "data-pipeline")
        assert (d / "pipeline.py").exists()

    def test_creates_config(self, tmp_path: Path):
        d = _scaffold(tmp_path, "data-pipeline")
        assert (d / "config.yaml").exists()

    def test_creates_data_dirs(self, tmp_path: Path):
        d = _scaffold(tmp_path, "data-pipeline")
        assert (d / "data" / "input").is_dir()
        assert (d / "data" / "output").is_dir()

    def test_creates_test_stub(self, tmp_path: Path):
        d = _scaffold(tmp_path, "data-pipeline")
        assert (d / "tests" / "test_pipeline.py").exists()

    def test_creates_dispatch_brief(self, tmp_path: Path):
        d = _scaffold(tmp_path, "data-pipeline")
        assert (d / "DISPATCH_BRIEF.md").exists()

    def test_creates_acceptance(self, tmp_path: Path):
        d = _scaffold(tmp_path, "data-pipeline")
        assert (d / "ACCEPTANCE.md").exists()

    def test_pipeline_py_has_etl_stages(self, tmp_path: Path):
        d = _scaffold(tmp_path, "data-pipeline")
        content = _read(d / "pipeline.py")
        assert "def extract" in content
        assert "def transform" in content
        assert "def load" in content

    def test_dispatch_brief_safety(self, tmp_path: Path):
        d = _scaffold(tmp_path, "data-pipeline")
        content = _read(d / "DISPATCH_BRIEF.md")
        assert "DRAFT ONLY" in content

    def test_all_files_utf8(self, tmp_path: Path):
        d = _scaffold(tmp_path, "data-pipeline")
        for f in d.rglob("*"):
            if f.is_file() and f.suffix in (".py", ".md", ".yaml"):
                assert isinstance(f.read_text(encoding="utf-8"), str)


# ---------------------------------------------------------------------------
# Power BI scaffold
# ---------------------------------------------------------------------------

class TestPowerBIScaffold:
    def test_creates_data_prep_py(self, tmp_path: Path):
        d = _scaffold(tmp_path, "powerbi")
        assert (d / "data_prep.py").exists()

    def test_creates_model_md(self, tmp_path: Path):
        d = _scaffold(tmp_path, "powerbi")
        assert (d / "MODEL.md").exists()

    def test_creates_data_dirs(self, tmp_path: Path):
        d = _scaffold(tmp_path, "powerbi")
        assert (d / "data" / "input").is_dir()
        assert (d / "data" / "output").is_dir()

    def test_creates_dispatch_brief(self, tmp_path: Path):
        d = _scaffold(tmp_path, "powerbi")
        assert (d / "DISPATCH_BRIEF.md").exists()

    def test_creates_acceptance(self, tmp_path: Path):
        d = _scaffold(tmp_path, "powerbi")
        assert (d / "ACCEPTANCE.md").exists()

    def test_model_md_has_dax(self, tmp_path: Path):
        d = _scaffold(tmp_path, "powerbi")
        content = _read(d / "MODEL.md")
        assert "DAX" in content
        assert "SUM" in content

    def test_model_md_has_tables(self, tmp_path: Path):
        d = _scaffold(tmp_path, "powerbi")
        content = _read(d / "MODEL.md")
        assert "Tables" in content
        assert "Columns" in content

    def test_data_prep_has_clean_fn(self, tmp_path: Path):
        d = _scaffold(tmp_path, "powerbi")
        content = _read(d / "data_prep.py")
        assert "def clean" in content
        assert "def save" in content

    def test_dispatch_brief_no_pbi_automation(self, tmp_path: Path):
        d = _scaffold(tmp_path, "powerbi")
        content = _read(d / "DISPATCH_BRIEF.md")
        assert "GUI" in content or "manual" in content.lower()

    def test_all_files_utf8(self, tmp_path: Path):
        d = _scaffold(tmp_path, "powerbi")
        for f in d.rglob("*"):
            if f.is_file() and f.suffix in (".py", ".md", ".yaml"):
                assert isinstance(f.read_text(encoding="utf-8"), str)


# ---------------------------------------------------------------------------
# Next.js scaffold
# ---------------------------------------------------------------------------

class TestNextjsScaffold:
    def test_creates_structure_md(self, tmp_path: Path):
        d = _scaffold(tmp_path, "nextjs")
        assert (d / "STRUCTURE.md").exists()

    def test_creates_env_example(self, tmp_path: Path):
        d = _scaffold(tmp_path, "nextjs")
        assert (d / ".env.example").exists()

    def test_creates_dispatch_brief(self, tmp_path: Path):
        d = _scaffold(tmp_path, "nextjs")
        assert (d / "DISPATCH_BRIEF.md").exists()

    def test_creates_acceptance(self, tmp_path: Path):
        d = _scaffold(tmp_path, "nextjs")
        assert (d / "ACCEPTANCE.md").exists()

    def test_creates_readme(self, tmp_path: Path):
        d = _scaffold(tmp_path, "nextjs")
        assert (d / "README.md").exists()

    def test_structure_md_has_supabase(self, tmp_path: Path):
        d = _scaffold(tmp_path, "nextjs")
        content = _read(d / "STRUCTURE.md")
        assert "Supabase" in content

    def test_structure_md_has_app_router(self, tmp_path: Path):
        d = _scaffold(tmp_path, "nextjs")
        content = _read(d / "STRUCTURE.md")
        assert "App Router" in content or "app/" in content

    def test_env_example_has_supabase_keys(self, tmp_path: Path):
        d = _scaffold(tmp_path, "nextjs")
        content = _read(d / ".env.example")
        assert "SUPABASE_URL" in content
        assert "SUPABASE_ANON_KEY" in content

    def test_env_example_no_real_secrets(self, tmp_path: Path):
        d = _scaffold(tmp_path, "nextjs")
        content = _read(d / ".env.example")
        assert "your-supabase" in content or "your-" in content

    def test_dispatch_brief_no_auto_deploy(self, tmp_path: Path):
        d = _scaffold(tmp_path, "nextjs")
        content = _read(d / "DISPATCH_BRIEF.md")
        assert "manually" in content.lower() or "manual" in content.lower()

    def test_all_files_utf8(self, tmp_path: Path):
        d = _scaffold(tmp_path, "nextjs")
        for f in d.rglob("*"):
            if f.is_file() and f.suffix in (".md", ".example"):
                assert isinstance(f.read_text(encoding="utf-8"), str)


# ---------------------------------------------------------------------------
# WordPress scaffold
# ---------------------------------------------------------------------------

class TestWordPressScaffold:
    def test_creates_plugin_php(self, tmp_path: Path):
        d = _scaffold(tmp_path, "wordpress", name="my-awesome-plugin")
        # plugin dir slug derived from name
        php_files = list(d.glob("**/*.php"))
        assert len(php_files) >= 1

    def test_creates_readme_txt(self, tmp_path: Path):
        d = _scaffold(tmp_path, "wordpress", name="my-plugin")
        txt_files = list(d.glob("**/*.txt"))
        assert len(txt_files) >= 1

    def test_creates_dispatch_brief(self, tmp_path: Path):
        d = _scaffold(tmp_path, "wordpress", name="my-plugin")
        assert (d / "DISPATCH_BRIEF.md").exists()

    def test_creates_acceptance(self, tmp_path: Path):
        d = _scaffold(tmp_path, "wordpress", name="my-plugin")
        assert (d / "ACCEPTANCE.md").exists()

    def test_creates_readme_md(self, tmp_path: Path):
        d = _scaffold(tmp_path, "wordpress", name="my-plugin")
        assert (d / "README.md").exists()

    def test_plugin_php_has_header(self, tmp_path: Path):
        d = _scaffold(tmp_path, "wordpress", name="my-plugin")
        php_file = next(d.glob("**/*.php"))
        content = _read(php_file)
        assert "Plugin Name:" in content
        assert "ABSPATH" in content

    def test_plugin_php_uses_esc_html(self, tmp_path: Path):
        d = _scaffold(tmp_path, "wordpress", name="my-plugin")
        php_file = next(d.glob("**/*.php"))
        content = _read(php_file)
        assert "esc_html" in content

    def test_plugin_php_no_direct_access(self, tmp_path: Path):
        d = _scaffold(tmp_path, "wordpress", name="my-plugin")
        php_file = next(d.glob("**/*.php"))
        content = _read(php_file)
        assert "direct access" in content.lower() or "ABSPATH" in content

    def test_dispatch_brief_no_auto_publish(self, tmp_path: Path):
        d = _scaffold(tmp_path, "wordpress", name="my-plugin")
        content = _read(d / "DISPATCH_BRIEF.md")
        assert "manually" in content.lower() or "manual" in content.lower()

    def test_all_files_utf8(self, tmp_path: Path):
        d = _scaffold(tmp_path, "wordpress", name="my-wp-plugin")
        for f in d.rglob("*"):
            if f.is_file() and f.suffix in (".php", ".md", ".txt"):
                assert isinstance(f.read_text(encoding="utf-8"), str)


# ---------------------------------------------------------------------------
# Cross-cutting: DISPATCH_BRIEF and ACCEPTANCE present for all types
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("scaffold_type", ["scraper", "data-pipeline", "powerbi", "nextjs", "wordpress"])
def test_all_types_have_dispatch_brief(tmp_path: Path, scaffold_type: str):
    d = _scaffold(tmp_path, scaffold_type)
    brief = d / "DISPATCH_BRIEF.md"
    assert brief.exists(), f"DISPATCH_BRIEF.md missing for {scaffold_type}"
    content = _read(brief)
    assert "Objective" in content
    assert "Validation" in content
    assert "Safety" in content


@pytest.mark.parametrize("scaffold_type", ["scraper", "data-pipeline", "powerbi", "nextjs", "wordpress"])
def test_all_types_have_acceptance(tmp_path: Path, scaffold_type: str):
    d = _scaffold(tmp_path, scaffold_type)
    acc = d / "ACCEPTANCE.md"
    assert acc.exists(), f"ACCEPTANCE.md missing for {scaffold_type}"
    content = _read(acc)
    assert "Acceptance Criteria" in content
    assert "Delivery Checklist" in content


@pytest.mark.parametrize("scaffold_type", ["scraper", "data-pipeline", "powerbi", "nextjs", "wordpress"])
def test_all_types_have_readme(tmp_path: Path, scaffold_type: str):
    d = _scaffold(tmp_path, scaffold_type)
    readme = d / "README.md"
    assert readme.exists(), f"README.md missing for {scaffold_type}"


@pytest.mark.parametrize("scaffold_type", ["scraper", "data-pipeline", "powerbi", "nextjs", "wordpress"])
def test_all_types_use_pathlib_output(tmp_path: Path, scaffold_type: str):
    """Verify generate_scaffold returns a Path object (not a string)."""
    from freelance_os.client.scaffold import generate_scaffold
    result = generate_scaffold(scaffold_type, tmp_path / scaffold_type, "test", force=True)
    assert isinstance(result, Path)


@pytest.mark.parametrize("scaffold_type", ["scraper", "data-pipeline", "powerbi", "nextjs", "wordpress"])
def test_all_types_dispatch_brief_is_utf8(tmp_path: Path, scaffold_type: str):
    d = _scaffold(tmp_path, scaffold_type)
    content = (d / "DISPATCH_BRIEF.md").read_text(encoding="utf-8")
    assert isinstance(content, str)
