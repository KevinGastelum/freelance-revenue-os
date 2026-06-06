# Operator Manual — Freelance Revenue OS

## Quick Start

### 1. Initialize

```bash
# Copy example config
cp config/settings.example.toml config/settings.toml
cp config/portfolio.example.yaml config/portfolio.yaml

# Initialize database
freelance-os init
```

### 2. Add a Lead

```bash
# From URL
freelance-os lead add-url "https://upwork.com/jobs/~01abc123" --description "Python API project..."

# From pasted text
freelance-os lead add-text --source upwork
# (paste job description, then Ctrl+D)
```

### 3. Score Leads

```bash
# Score a specific lead
freelance-os lead score 1

# Score all new leads at once
freelance-os lead score --all-new
```

### 4. Review and Draft

```bash
# List all leads
freelance-os lead list

# Show a specific lead
freelance-os lead show 1

# Generate a proposal draft (deterministic, no LLM calls)
freelance-os lead draft 1

# Validate the draft
freelance-os lead validate-draft 1

# Interactive review queue
freelance-os lead review
```

### 5. Mark Status

```bash
# Mark as applied (manually — you submit on the platform)
freelance-os lead status 1 APPLIED_MANUALLY

# Mark as won
freelance-os lead status 1 WON
```

### 6. Client Workspace

```bash
# Initialize client workspace for a WON lead
freelance-os client init --lead 1

# List client projects
freelance-os client list

# Generate delivery package
freelance-os client package --project acme-corp-python-api-build

# Generate tmux session script (run manually)
freelance-os client tmux --project acme-corp-python-api-build

# View worktree setup commands (dry-run)
freelance-os client worktree --project acme-corp-python-api-build --repo git@github.com:client/repo.git
```

### 7. Outcomes and Reports

```bash
# Record an outcome
freelance-os outcome add --lead 1

# Weekly performance report
freelance-os report weekly

# Export report to markdown
freelance-os report weekly --export reports/weekly.md
```

## Configuration

### config/settings.toml

```toml
[user]
name = "Your Name"
target_hourly_rate = 75
minimum_project_value = 300

[paths]
client_work_dir = "./client-work"
portfolio_file = "./config/portfolio.yaml"
database_path = "./data/freelance_os.sqlite"

<!--
[safety]
# These MUST all remain false
allow_browser_automation = false
allow_auto_submit = false
allow_auto_message = false
allow_scraping = false
require_human_approval = true
-->
```

### config/portfolio.yaml

Add your real portfolio items here. Include:
- `name` — project name
- `tags` — tech stack keywords for matching
- `proof_points` — specific, verifiable accomplishments
- `allowed_claims` — claims you can make in proposals
- `forbidden_claims` — claims that would be false or exaggerated

<!--
## Safety Rules (Non-Negotiable)

1. **Never submit proposals automatically.** Copy the draft and submit manually.
2. **Never send messages automatically.** The delivery message is a draft — send it manually.
3. **Never log in to platforms.** The tool does not handle platform authentication.
4. **Review all AI-generated content** before using it.

See [SAFETY_POLICY.md](SAFETY_POLICY.md) for the full safety policy.
-->

## Data Location

- Database: `data/freelance_os.sqlite`
- Client workspaces: `client-work/<client>-<project>/`
- Config: `config/settings.toml`, `config/portfolio.yaml`

## Backing Up

```bash
# Backup the database
cp data/freelance_os.sqlite data/freelance_os.sqlite.bak
```
