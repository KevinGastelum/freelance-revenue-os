"""Client delivery scaffold generator — Command Center Phase 6.

Generates ready-to-build project skeletons for common gig types.
Each scaffold includes: source skeleton, config, README.md,
ACCEPTANCE.md (acceptance criteria), and DISPATCH_BRIEF.md (Warren prompt).
"""

import re
from pathlib import Path

SCAFFOLD_TYPES = ["scraper", "data-pipeline", "powerbi", "nextjs", "wordpress"]


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text)[:40]


def generate_scaffold(
    scaffold_type: str,
    target_dir: Path,
    name: str,
    force: bool = False,
) -> Path:
    """Generate a project scaffold in target_dir.

    Raises ValueError for unknown type.
    Raises FileExistsError if DISPATCH_BRIEF.md already exists without --force.
    Returns the scaffold directory path.
    """
    if scaffold_type not in SCAFFOLD_TYPES:
        raise ValueError(
            f"Unknown scaffold type '{scaffold_type}'. Valid: {', '.join(SCAFFOLD_TYPES)}"
        )
    sentinel = target_dir / "DISPATCH_BRIEF.md"
    if sentinel.exists() and not force:
        raise FileExistsError(
            f"Scaffold already exists at {target_dir}\n"
            "Use --force to overwrite."
        )
    target_dir.mkdir(parents=True, exist_ok=True)
    _GENERATORS[scaffold_type](target_dir, name)
    return target_dir


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# =============================================================================
# Scraper
# =============================================================================

def _gen_scraper(d: Path, name: str) -> None:
    _write(d / "scraper.py", _scraper_py(name))
    _write(d / "config.yaml", _SCRAPER_CONFIG)
    _write(d / "output" / ".gitkeep", "")
    _write(d / "tests" / "test_scraper.py", _SCRAPER_TESTS)
    _write(d / "README.md", _readme(name, "Web Scraper", "python scraper.py"))
    _write(d / "ACCEPTANCE.md", _acceptance(name, "Web Scraper", _SCRAPER_CRITERIA))
    _write(d / "DISPATCH_BRIEF.md", _dispatch_brief(
        name=name,
        scaffold_type="scraper",
        objective=f"Complete the web scraper in scraper.py for project '{name}' per the client spec.",
        files="scraper.py, config.yaml, output/, tests/test_scraper.py",
        test_cmd="uv run pytest -q",
        extra_constraints=(
            "- Output must be UTF-8 CSV or JSON written to output/\n"
            "- Respect robots.txt; add 1-2 s delay between requests\n"
            "- Do NOT add proxy rotation, challenge-bypass, or stealth anti-bot features"
        ),
        non_goals=(
            "- No authenticated scraping\n"
            "- No browser automation or platform login\n"
            "- No residential proxy rotation"
        ),
    ))


def _scraper_py(name: str) -> str:
    return (
        '"""Web scraper skeleton — ' + name + ".\n\n"
        "Adapt selectors and config.yaml to the client's target site.\n"
        "Run: python scraper.py\n"
        '"""\n\n'
        "import csv\n"
        "import json\n"
        "import time\n"
        "from pathlib import Path\n"
        "from typing import Any\n\n"
        "import httpx\n"
        "from bs4 import BeautifulSoup\n\n"
        'CONFIG_FILE = Path(__file__).parent / "config.yaml"\n'
        'OUTPUT_DIR = Path(__file__).parent / "output"\n\n\n'
        "def load_config() -> dict:\n"
        "    import yaml  # type: ignore[import]\n"
        '    with CONFIG_FILE.open(encoding="utf-8") as f:\n'
        "        return yaml.safe_load(f)\n\n\n"
        "def fetch(url: str, delay: float = 1.0) -> str:\n"
        '    """Fetch a page; returns HTML. Respects a polite crawl delay."""\n'
        "    time.sleep(delay)\n"
        "    resp = httpx.get(\n"
        "        url, timeout=30, follow_redirects=True,\n"
        '        headers={"User-Agent": "Mozilla/5.0 (compatible; research-bot/1.0)"},\n'
        "    )\n"
        "    resp.raise_for_status()\n"
        "    return resp.text\n\n\n"
        "def parse(html: str, fields: list) -> list:\n"
        '    """Extract structured items from HTML.\n\n'
        "    TODO: replace the CSS selectors with ones matching the client's site.\n"
        '    """\n'
        '    soup = BeautifulSoup(html, "html.parser")\n'
        "    rows: list = []\n"
        '    for item in soup.select("article, .item, li.result"):  # TODO: adapt\n'
        '        heading = item.find(["h2", "h3"])\n'
        '        link = item.find("a")\n'
        '        desc = item.find("p")\n'
        "        row: dict = {\n"
        '            "title": heading.get_text(strip=True) if heading else "",\n'
        '            "url": link["href"] if link and link.get("href") else "",\n'
        '            "description": desc.get_text(strip=True)[:300] if desc else "",\n'
        "        }\n"
        "        rows.append({k: row.get(k, \"\") for k in fields})\n"
        "    return rows\n\n\n"
        "def save_csv(rows: list, path: Path, fields: list) -> None:\n"
        "    path.parent.mkdir(parents=True, exist_ok=True)\n"
        '    with path.open("w", newline="", encoding="utf-8") as f:\n'
        "        writer = csv.DictWriter(f, fieldnames=fields)\n"
        "        writer.writeheader()\n"
        "        writer.writerows(rows)\n"
        "    print(f\"Saved {len(rows)} rows -> {path}\")\n\n\n"
        "def save_json(rows: list, path: Path) -> None:\n"
        "    path.parent.mkdir(parents=True, exist_ok=True)\n"
        "    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding=\"utf-8\")\n"
        "    print(f\"Saved {len(rows)} rows -> {path}\")\n\n\n"
        "def main() -> None:\n"
        "    cfg = load_config()\n"
        '    target_url: str = cfg["target_url"]\n'
        '    fields: list = cfg["fields"]\n'
        '    output_format: str = cfg.get("output_format", "csv")\n'
        "    html = fetch(target_url)\n"
        "    rows = parse(html, fields)\n"
        "    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)\n"
        '    if output_format == "json":\n'
        '        save_json(rows, OUTPUT_DIR / "results.json")\n'
        "    else:\n"
        '        save_csv(rows, OUTPUT_DIR / "results.csv", fields)\n\n\n'
        'if __name__ == "__main__":\n'
        "    main()\n"
    )


_SCRAPER_CONFIG = """\
# Scraper configuration — edit before running
target_url: "https://example.com/data"   # TODO: client target URL
output_format: "csv"                      # csv or json
fields:
  - title
  - url
  - description
pagination:
  enabled: false
  max_pages: 1
"""

_SCRAPER_TESTS = """\
\"\"\"Scraper unit tests — run with: uv run pytest -q\"\"\"
import pytest


def _make_html(items: list) -> str:
    items_html = "".join(
        f"<article><h2>{i}</h2><p>Desc {i}</p></article>" for i in items
    )
    return f"<html><body>{items_html}</body></html>"


def test_parse_returns_list():
    from scraper import parse
    html = _make_html(["Alpha", "Beta"])
    rows = parse(html, ["title", "url", "description"])
    assert isinstance(rows, list)
    assert len(rows) == 2


def test_parse_extracts_title():
    from scraper import parse
    html = _make_html(["My Title"])
    rows = parse(html, ["title", "url", "description"])
    assert rows[0]["title"] == "My Title"


def test_parse_empty_html_returns_empty():
    from scraper import parse
    rows = parse("<html><body></body></html>", ["title", "url"])
    assert rows == []
"""

_SCRAPER_CRITERIA = """\
- scraper.py runs without errors on a live or mock HTTP response
- Output file (CSV or JSON) is written to output/ with UTF-8 encoding
- All configured fields are present as columns/keys
- No proxy rotation, challenge-bypass, or stealth automation present
- `uv run pytest -q` exits 0"""


# =============================================================================
# Data pipeline
# =============================================================================

def _gen_data_pipeline(d: Path, name: str) -> None:
    _write(d / "pipeline.py", _pipeline_py(name))
    _write(d / "config.yaml", _PIPELINE_CONFIG)
    _write(d / "data" / "input" / ".gitkeep", "")
    _write(d / "data" / "output" / ".gitkeep", "")
    _write(d / "tests" / "test_pipeline.py", _PIPELINE_TESTS)
    _write(d / "README.md", _readme(name, "Data Pipeline", "python pipeline.py"))
    _write(d / "ACCEPTANCE.md", _acceptance(name, "Data Pipeline", _PIPELINE_CRITERIA))
    _write(d / "DISPATCH_BRIEF.md", _dispatch_brief(
        name=name,
        scaffold_type="data-pipeline",
        objective=f"Complete the ETL pipeline in pipeline.py for project '{name}' per the client spec.",
        files="pipeline.py, config.yaml, data/input/, data/output/, tests/test_pipeline.py",
        test_cmd="uv run pytest -q",
        extra_constraints=(
            "- All file I/O must use encoding='utf-8' and pathlib\n"
            "- Validate input schema before transform; log/skip bad rows\n"
            "- Output must match the agreed column spec"
        ),
        non_goals=(
            "- No live database writes until client approves output\n"
            "- No scheduled or automated execution — run is manual"
        ),
    ))


def _pipeline_py(name: str) -> str:
    return (
        '"""Data pipeline skeleton — ' + name + ".\n\n"
        "Stages: extract -> transform -> load.\n"
        "Run: python pipeline.py\n"
        '"""\n\n'
        "import csv\n"
        "import json\n"
        "from pathlib import Path\n"
        "from typing import Any\n\n"
        'CONFIG_FILE = Path(__file__).parent / "config.yaml"\n'
        'DATA_DIR = Path(__file__).parent / "data"\n\n\n'
        "def load_config() -> dict:\n"
        "    import yaml  # type: ignore[import]\n"
        '    with CONFIG_FILE.open(encoding="utf-8") as f:\n'
        "        return yaml.safe_load(f)\n\n\n"
        "# --- Extract --------------------------------------------------------\n\n"
        "def extract(input_path: Path) -> list:\n"
        '    """Read raw data from input file (CSV or JSON)."""\n'
        "    suffix = input_path.suffix.lower()\n"
        '    if suffix == ".json":\n'
        '        return json.loads(input_path.read_text(encoding="utf-8"))\n'
        "    with input_path.open(encoding=\"utf-8\") as f:\n"
        "        return list(csv.DictReader(f))\n\n\n"
        "# --- Transform ------------------------------------------------------\n\n"
        "def transform(rows: list) -> list:\n"
        "    \"\"\"Clean, filter, and reshape rows for the client's spec.\"\"\"\n"
        "    cleaned = []\n"
        "    for row in rows:\n"
        "        row = {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}\n"
        "        # TODO: add client-specific transformations here\n"
        "        if any(v for v in row.values()):\n"
        "            cleaned.append(row)\n"
        "    return cleaned\n\n\n"
        "# --- Load -----------------------------------------------------------\n\n"
        "def load(rows: list, output_path: Path) -> None:\n"
        '    """Write transformed data to output file."""\n'
        "    output_path.parent.mkdir(parents=True, exist_ok=True)\n"
        "    if not rows:\n"
        '        print("No rows to write.")\n'
        "        return\n"
        '    with output_path.open("w", newline="", encoding="utf-8") as f:\n'
        "        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))\n"
        "        writer.writeheader()\n"
        "        writer.writerows(rows)\n"
        "    print(f\"Wrote {len(rows)} rows -> {output_path}\")\n\n\n"
        "# --- Main -----------------------------------------------------------\n\n"
        "def main() -> None:\n"
        "    cfg = load_config()\n"
        '    input_file = DATA_DIR / "input" / cfg["input_file"]\n'
        '    output_file = DATA_DIR / "output" / cfg["output_file"]\n'
        "    raw = extract(input_file)\n"
        "    print(f\"Extracted {len(raw)} rows from {input_file}\")\n"
        "    clean = transform(raw)\n"
        "    print(f\"Transformed: {len(clean)} rows retained\")\n"
        "    load(clean, output_file)\n\n\n"
        'if __name__ == "__main__":\n'
        "    main()\n"
    )


_PIPELINE_CONFIG = """\
# Data pipeline configuration
input_file: "source.csv"   # file in data/input/
output_file: "clean.csv"   # file in data/output/
# TODO: add client-specific field mappings or filter rules
"""

_PIPELINE_TESTS = """\
\"\"\"Data pipeline unit tests — run with: uv run pytest -q\"\"\"
import csv
from io import StringIO
from pathlib import Path
import pytest


def _make_rows(header: list, rows: list) -> list:
    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(header)
    writer.writerows(rows)
    buf.seek(0)
    return list(csv.DictReader(buf))


def test_transform_strips_whitespace():
    from pipeline import transform
    rows = [{"name": "  Alice  ", "value": "  10  "}]
    result = transform(rows)
    assert result[0]["name"] == "Alice"
    assert result[0]["value"] == "10"


def test_transform_drops_empty_rows():
    from pipeline import transform
    rows = [{"a": "", "b": ""}]
    result = transform(rows)
    assert result == []


def test_transform_retains_valid_rows():
    from pipeline import transform
    rows = [{"a": "hello", "b": "world"}]
    result = transform(rows)
    assert len(result) == 1


def test_load_writes_csv(tmp_path):
    from pipeline import load
    rows = [{"col1": "val1", "col2": "val2"}]
    out = tmp_path / "out.csv"
    load(rows, out)
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "col1" in content
    assert "val1" in content
"""

_PIPELINE_CRITERIA = """\
- pipeline.py runs without errors on sample input data
- Output CSV is written to data/output/ with UTF-8 encoding
- Empty and whitespace-only rows are dropped in transform()
- `uv run pytest -q` exits 0
- Output column schema matches the agreed client spec"""


# =============================================================================
# Power BI data prep
# =============================================================================

def _gen_powerbi(d: Path, name: str) -> None:
    _write(d / "data_prep.py", _powerbi_py(name))
    _write(d / "MODEL.md", _powerbi_model(name))
    _write(d / "data" / "input" / ".gitkeep", "")
    _write(d / "data" / "output" / ".gitkeep", "")
    _write(d / "README.md", _readme(name, "Power BI Data Prep", "python data_prep.py"))
    _write(d / "ACCEPTANCE.md", _acceptance(name, "Power BI Prep", _POWERBI_CRITERIA))
    _write(d / "DISPATCH_BRIEF.md", _dispatch_brief(
        name=name,
        scaffold_type="powerbi",
        objective=(
            f"Complete the Power BI data prep script (data_prep.py) and MODEL.md "
            f"for project '{name}' per the client spec."
        ),
        files="data_prep.py, MODEL.md, data/input/, data/output/",
        test_cmd="uv run python data_prep.py  # run against sample input; review output CSV",
        extra_constraints=(
            "- All file I/O must use encoding='utf-8' and pathlib\n"
            "- Output must be a single flat CSV importable directly into Power BI Desktop\n"
            "- Document all DAX measures and table relationships in MODEL.md"
        ),
        non_goals=(
            "- No Power BI Desktop automation (authoring is GUI/manual)\n"
            "- No live database connections — deliver prepared flat files only"
        ),
    ))


def _powerbi_py(name: str) -> str:
    return (
        '"""Power BI data prep — ' + name + ".\n\n"
        "Cleans and reshapes the client's source data into an analysis-ready\n"
        "flat CSV for import into Power BI Desktop.\n\n"
        "Run: python data_prep.py\n"
        '"""\n\n'
        "import csv\n"
        "from pathlib import Path\n"
        "from typing import Any\n\n"
        'INPUT_FILE = Path(__file__).parent / "data" / "input" / "source.csv"\n'
        'OUTPUT_FILE = Path(__file__).parent / "data" / "output" / "model_ready.csv"\n\n\n'
        "def load_csv(path: Path) -> list:\n"
        '    with path.open(encoding="utf-8") as f:\n'
        "        return list(csv.DictReader(f))\n\n\n"
        "def clean(rows: list) -> list:\n"
        '    """Standardize columns, types, and values for Power BI import.\n\n'
        "    TODO: adapt column names and transformations to the client's data.\n"
        '    """\n'
        "    cleaned = []\n"
        "    for row in rows:\n"
        "        row = {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}\n"
        "        cleaned.append({\n"
        '            "Date": row.get("Date", row.get("date", "")),\n'
        '            "Category": row.get("Category", row.get("category", "")).upper(),\n'
        '            "Amount": _parse_float(row.get("Amount", row.get("amount", "0"))),\n'
        '            "Label": row.get("Label", row.get("Name", row.get("name", ""))),\n'
        "        })\n"
        "    return [r for r in cleaned if r[\"Date\"]]\n\n\n"
        "def _parse_float(val: Any) -> float:\n"
        "    try:\n"
        "        return float(str(val).replace(\",\", \"\").replace(\"$\", \"\").strip())\n"
        "    except (ValueError, TypeError):\n"
        "        return 0.0\n\n\n"
        "def save(rows: list, path: Path = OUTPUT_FILE) -> None:\n"
        "    path.parent.mkdir(parents=True, exist_ok=True)\n"
        "    if not rows:\n"
        '        print("No rows to write.")\n'
        "        return\n"
        '    with path.open("w", newline="", encoding="utf-8") as f:\n'
        "        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))\n"
        "        writer.writeheader()\n"
        "        writer.writerows(rows)\n"
        "    print(f\"Wrote {len(rows)} rows -> {path}\")\n\n\n"
        'if __name__ == "__main__":\n'
        "    rows = load_csv(INPUT_FILE)\n"
        "    clean_rows = clean(rows)\n"
        "    save(clean_rows)\n"
    )


def _powerbi_model(name: str) -> str:
    return f"""\
# Power BI Data Model — {name}

## Tables

| Table | Source File | Description |
|-------|-------------|-------------|
| Facts | model_ready.csv | Main fact table (one row per event/transaction) |

## Columns (Facts table)

| Column | Type | Description |
|--------|------|-------------|
| Date | Date | Event/transaction date (YYYY-MM-DD) |
| Category | Text | Grouping category (standardized to UPPER) |
| Amount | Decimal | Numeric value |
| Label | Text | Descriptive label or name |

## Relationships

(Define relationships between tables once dimension tables are identified.)

## DAX Measures

```dax
-- Total Amount
Total Amount = SUM(Facts[Amount])

-- Count of Records
Record Count = COUNTROWS(Facts)

-- Average Amount
Avg Amount = AVERAGE(Facts[Amount])
```

## Power BI Authoring Notes

- Import model_ready.csv via Get Data > Text/CSV
- Set Date column type to Date (not Text) in Power Query
- Set Amount column type to Decimal Number
- The client authors the report in Power BI Desktop (GUI);
  this file defines the data shape and measures they will use.
"""


_POWERBI_CRITERIA = """\
- data_prep.py runs without errors on sample input data
- Output CSV in data/output/ is importable into Power BI Desktop
- Date, Category, Amount, Label columns present and correctly typed
- MODEL.md documents tables, columns, and DAX measures
- All file I/O uses encoding='utf-8' and pathlib"""


# =============================================================================
# Next.js
# =============================================================================

def _gen_nextjs(d: Path, name: str) -> None:
    _write(d / "STRUCTURE.md", _nextjs_structure(name))
    _write(d / ".env.example", _NEXTJS_ENV)
    _write(d / "README.md", _readme(name, "Next.js + Supabase App", "npm run dev"))
    _write(d / "ACCEPTANCE.md", _acceptance(name, "Next.js App", _NEXTJS_CRITERIA))
    _write(d / "DISPATCH_BRIEF.md", _dispatch_brief(
        name=name,
        scaffold_type="nextjs",
        objective=(
            f"Build the Next.js 14 + Supabase app '{name}' per the client spec. "
            "Use the structure in STRUCTURE.md. Use App Router with TypeScript."
        ),
        files="STRUCTURE.md, .env.example, ACCEPTANCE.md",
        test_cmd="npm run build && npm run lint  # zero errors required",
        extra_constraints=(
            "- Use Next.js App Router (app/) with TypeScript\n"
            "- Use Supabase SSR client for auth and DB (@supabase/ssr)\n"
            "- All env vars via .env.local (never commit it)\n"
            "- Deploy target: Vercel — ensure next.config.js is production-safe\n"
            "- Use Tailwind CSS for styling"
        ),
        non_goals=(
            "- No automated platform publishing\n"
            "- No purchase or payment automation\n"
            "- Human deploys to Vercel manually after review"
        ),
    ))


def _nextjs_structure(name: str) -> str:
    return f"""\
# Next.js + Supabase Project Structure — {name}

## Stack

- Next.js 14 (App Router, TypeScript)
- Supabase (Auth + Postgres DB via @supabase/ssr)
- Tailwind CSS
- Vercel (deployment target)

## Proposed Directory Structure

```
{name}/
  app/
    layout.tsx          # Root layout with providers
    page.tsx            # Home / landing page
    (auth)/
      login/page.tsx    # Login form
      signup/page.tsx   # Sign-up form
    dashboard/
      page.tsx          # Protected dashboard (requires auth)
  components/
    ui/                 # Shared UI components
  lib/
    supabase/
      client.ts         # Browser-side Supabase client
      server.ts         # Server-side Supabase client
  middleware.ts         # Auth session refresh (Supabase SSR)
  next.config.js
  tailwind.config.ts
  tsconfig.json
  package.json
```

## Database Schema (Supabase)

Define tables via Supabase Dashboard SQL editor. Example:

```sql
create table profiles (
  id uuid references auth.users on delete cascade,
  full_name text,
  updated_at timestamp with time zone,
  primary key (id)
);

alter table profiles enable row level security;
create policy "Users can view own profile." on profiles
  for select using (auth.uid() = id);
```

## Environment Variables

Copy `.env.example` to `.env.local` and fill in Supabase credentials.
Never commit `.env.local`.

## Getting Started

1. Create a Supabase project at https://supabase.com
2. Copy `.env.example` -> `.env.local`, fill in credentials
3. Warren dispatch (see DISPATCH_BRIEF.md) builds the app skeleton
4. Review locally (`npm run dev`), then deploy to Vercel manually
"""


_NEXTJS_ENV = """\
# Next.js + Supabase environment variables
# Copy to .env.local and fill in your credentials.
# NEVER commit .env.local to git.

NEXT_PUBLIC_SUPABASE_URL=your-supabase-project-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
"""

_NEXTJS_CRITERIA = """\
- `npm run build` completes with zero errors
- `npm run lint` passes with zero warnings or errors
- Auth flow works end-to-end: signup, login, logout (Supabase)
- All protected routes redirect to login when unauthenticated
- No credentials or secrets in committed source code
- Responsive layout on mobile and desktop
- Middleware.ts refreshes Supabase session on each request"""


# =============================================================================
# WordPress plugin
# =============================================================================

def _gen_wordpress(d: Path, name: str) -> None:
    slug = _slugify(name)
    slug_upper = slug.upper().replace("-", "_")
    slug_fn = slug.replace("-", "_")
    plugin_dir = d / slug
    _write(plugin_dir / f"{slug}.php", _wp_plugin_php(name, slug, slug_upper, slug_fn))
    _write(plugin_dir / "readme.txt", _wp_readme_txt(name, slug))
    _write(d / "README.md", _readme(name, "WordPress Plugin", "# Install via WordPress admin > Plugins > Add New > Upload"))
    _write(d / "ACCEPTANCE.md", _acceptance(name, "WordPress Plugin", _WP_CRITERIA))
    _write(d / "DISPATCH_BRIEF.md", _dispatch_brief(
        name=name,
        scaffold_type="wordpress",
        objective=(
            f"Build the WordPress plugin '{name}' (slug: {slug}) per the client spec. "
            f"Start from {slug}/{slug}.php."
        ),
        files=f"{slug}/{slug}.php, {slug}/readme.txt",
        test_cmd=f"php -l {slug}/{slug}.php  # syntax check; manual: activate in WP admin",
        extra_constraints=(
            "- Follow WordPress coding standards\n"
            "- Use esc_html(), sanitize_text_field(), wp_nonce_field() for all output/input\n"
            f"- Prefix all functions, classes, and hooks with '{slug_fn}_'\n"
            "- Use $wpdb->prepare() for all DB queries\n"
            "- Deliver as a zip-able plugin directory"
        ),
        non_goals=(
            "- No automated plugin publishing to wordpress.org\n"
            "- No automated WP admin actions\n"
            "- Human installs the plugin zip manually"
        ),
    ))


def _wp_plugin_php(name: str, slug: str, slug_upper: str, slug_fn: str) -> str:
    return (
        "<?php\n"
        "/**\n"
        f" * Plugin Name: {name}\n"
        f" * Plugin URI:  https://example.com/plugins/{slug}\n"
        f" * Description: TODO: describe what this plugin does.\n"
        " * Version:     1.0.0\n"
        " * Author:      TODO: your name\n"
        " * License:     GPL-2.0-or-later\n"
        f" * Text Domain: {slug}\n"
        " */\n\n"
        "if ( ! defined( 'ABSPATH' ) ) {\n"
        "    exit; // Prevent direct access.\n"
        "}\n\n"
        f"define( '{slug_upper}_VERSION', '1.0.0' );\n"
        f"define( '{slug_upper}_DIR', plugin_dir_path( __FILE__ ) );\n"
        f"define( '{slug_upper}_URL', plugin_dir_url( __FILE__ ) );\n\n\n"
        "// ---------------------------------------------------------------------------\n"
        "// Activation / Deactivation\n"
        "// ---------------------------------------------------------------------------\n\n"
        f"register_activation_hook( __FILE__, '{slug_fn}_activate' );\n"
        f"register_deactivation_hook( __FILE__, '{slug_fn}_deactivate' );\n\n"
        f"function {slug_fn}_activate() {{\n"
        "    // TODO: create custom DB tables, set default options\n"
        "    flush_rewrite_rules();\n"
        "}\n\n"
        f"function {slug_fn}_deactivate() {{\n"
        "    flush_rewrite_rules();\n"
        "}\n\n\n"
        "// ---------------------------------------------------------------------------\n"
        "// Main hooks\n"
        "// ---------------------------------------------------------------------------\n\n"
        f"add_action( 'init', '{slug_fn}_init' );\n\n"
        f"function {slug_fn}_init() {{\n"
        "    // TODO: register custom post types, taxonomies, or shortcodes\n"
        "}\n\n"
        f"add_action( 'wp_enqueue_scripts', '{slug_fn}_enqueue' );\n\n"
        f"function {slug_fn}_enqueue() {{\n"
        f"    // wp_enqueue_style( '{slug}', {slug_upper}_URL . 'assets/style.css', array(), {slug_upper}_VERSION );\n"
        "}\n\n"
        f"add_action( 'admin_menu', '{slug_fn}_admin_menu' );\n\n"
        f"function {slug_fn}_admin_menu() {{\n"
        "    add_options_page(\n"
        f"        esc_html__( '{name} Settings', '{slug}' ),\n"
        f"        esc_html__( '{name}', '{slug}' ),\n"
        "        'manage_options',\n"
        f"        '{slug}',\n"
        f"        '{slug_fn}_settings_page'\n"
        "    );\n"
        "}\n\n"
        f"function {slug_fn}_settings_page() {{\n"
        "    if ( ! current_user_can( 'manage_options' ) ) {\n"
        "        return;\n"
        "    }\n"
        "    // TODO: render settings form with wp_nonce_field()\n"
        "    echo '<div class=\"wrap\"><h1>' . esc_html( get_admin_page_title() ) . '</h1>';\n"
        "    echo '<p>TODO: add settings form here.</p></div>';\n"
        "}\n"
    )


def _wp_readme_txt(name: str, slug: str) -> str:
    return f"""\
=== {name} ===
Contributors: yourname
Tags: TODO, add, tags
Requires at least: 6.0
Tested up to: 6.5
Stable tag: 1.0.0
License: GPLv2 or later
License URI: https://www.gnu.org/licenses/gpl-2.0.html

== Description ==

TODO: describe what this plugin does.

== Installation ==

1. Upload the plugin folder to /wp-content/plugins/.
2. Activate via the Plugins menu in WordPress admin.
3. Configure via Settings > {name}.

== Changelog ==

= 1.0.0 =
* Initial release skeleton.
"""

_WP_CRITERIA = """\
- Plugin activates without PHP errors in WordPress admin
- `php -l <slug>/<slug>.php` reports no syntax errors
- All output is escaped with esc_html() / esc_attr()
- All user input is sanitized (sanitize_text_field() / absint() etc.)
- No direct DB queries without $wpdb->prepare()
- Plugin can be zipped and installed on a fresh WordPress site"""


# =============================================================================
# Shared template helpers
# =============================================================================

def _readme(name: str, type_label: str, run_cmd: str) -> str:
    return f"""\
# {name} — {type_label}

## Overview

TODO: describe the project goal and what this deliverable achieves.

## How to Run

```bash
{run_cmd}
```

## Project Structure

```
.
├── ACCEPTANCE.md       # Acceptance criteria
├── DISPATCH_BRIEF.md   # Warren dispatch prompt to build this out
└── (source files — see type-specific files above)
```

## Delivery Notes

All platform actions are manual. The client reviews and accepts per the
criteria in ACCEPTANCE.md before payment is released.
"""


def _acceptance(name: str, type_label: str, criteria: str) -> str:
    return f"""\
# Acceptance Criteria — {name} ({type_label})

All items below must be satisfied before delivery.

## Functional Requirements

{criteria}

## Quality Requirements

- Code is readable; inline comments explain non-obvious decisions
- No hard-coded credentials or secrets in any committed file
- All file I/O uses pathlib and encoding="utf-8"
- Encoding: all generated text files are UTF-8

## Delivery Checklist

- [ ] All acceptance criteria above are met
- [ ] Reviewed for safety rules (no stealth automation, no challenge-bypass)
- [ ] README.md updated with actual run instructions
- [ ] Tested end-to-end on a realistic sample dataset or environment
"""


def _dispatch_brief(
    name: str,
    scaffold_type: str,
    objective: str,
    files: str,
    test_cmd: str,
    extra_constraints: str,
    non_goals: str,
) -> str:
    branch = f"feat/{scaffold_type}/{_slugify(name)}-impl"
    return f"""\
# Warren Dispatch Brief — {name} ({scaffold_type})

> Copy this prompt into Warren (or `wr-run.sh`) to dispatch a build agent.
> Review and edit TODO sections before dispatching.

---

## Objective

{objective}

## Relevant Files / Dirs

- {files}
- README.md
- ACCEPTANCE.md

## Constraints

{extra_constraints}
- Cross-platform: `encoding="utf-8"` on all file I/O; use `pathlib`
- Do not expose secrets, .env contents, or API tokens
- Keep changes minimal and reviewable

## Non-Goals

{non_goals}

## Validation / Test Command

```
{test_cmd}
```

Gate must exit 0 before the agent reports completion.

## Branch / PR Expectation

- Branch: `{branch}`
- Auto-merge to `main` on green verifier (tests pass + safety check)
- Do NOT commit credentials or .env files

## Safety Reminder (non-negotiable)

This project must NOT introduce:
- Stealth browser automation or fingerprint spoofing
- Residential proxy rotation or challenge-solving/bypassing
- Automated login or authenticated scraping
- Automated platform messaging, order delivery, or payment actions

Generated text is **DRAFT ONLY** — the human reviews and acts manually.
"""


# =============================================================================
# Generator dispatch table (defined after all _gen_* functions)
# =============================================================================

_GENERATORS = {
    "scraper": _gen_scraper,
    "data-pipeline": _gen_data_pipeline,
    "powerbi": _gen_powerbi,
    "nextjs": _gen_nextjs,
    "wordpress": _gen_wordpress,
}
