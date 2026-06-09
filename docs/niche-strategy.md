# Niche / Obscure-Stack Strategy

_The AI-leverage thesis, made into an actionable hunting plan. Compiled 2026-06-08._
_Companion: `source-catalog.md` (WHERE to find these) · `lead-sources.md` (the 5 models)._

## Thesis — breadth is the moat

A human freelancer is rate-limited by what THEY personally know. Ramping on COBOL, AutoLISP,
HL7, or XSLT takes them weeks, so they decline those gigs — which keeps competition (and bids)
thin and rates high. An agent with good documentation picks up an obscure-but-bounded task in
minutes. So we deliberately **hunt the niches humans avoid**. An obscure stack is a **feature**
(low competition, high margin), not a disqualifier — this is the scorer's existing
"AI-leverage margin, never weight by human-stack match" rule, made concrete.

**Validated:** AS400/RPG contract work runs **$50-55/hr with "relatively limited
competition"**; COBOL/Delphi migration in steady demand with thin human supply (ZipRecruiter,
Upwork hire pages, June 2026).

## What makes a niche lead GOOD (all should hold)

1. **Bounded scope** — a discrete deliverable with a clear "done" (fix this / build this script
   / migrate this), not open-ended ownership.
2. **Documented** — the language/API/format has public docs/specs/examples the agent can read.
   Obscure != undocumented.
3. **Verifiable output** — you can prove it works (tests pass, file converts, script runs,
   output matches a spec). The proposal verifier + your local run is the acceptance gate.
4. **Thin human supply** — few freelancers bid / the skill is "rare." That's the margin.
5. **No privileged access required** — no credentials, prod systems, proprietary SDKs, hardware,
   or data we can't legally obtain.
6. **Self-contained delivery** — handed over as code/files/docs, not weeks of meetings.

## Hard NO filters (skip regardless of margin)

- Licensure / regulated judgment (medical, legal, financial/tax advice, engineering stamps).
- Safety- or liability-critical (medical devices, aviation, anything where a bug hurts someone).
- Unbounded "be our ongoing dev" retainers — can't AI-leverage a relationship.
- Real-time human presence (live ops, phone support, on-call).
- Physical/hardware or in-person access.
- Intrinsically human-embodiment skills (voiceover, acting, on-camera).
- Anything violating a platform's AI-use policy or requiring prohibited misrepresentation.

## Target niche taxonomy — where the margin lives

| # | Category | Example task types | Best-fit sources |
|---|---|---|---|
| **N1** | **Legacy & obscure languages** — COBOL, Fortran, Delphi/Pascal, Perl, Tcl, ABAP, RPG/CL (AS400), MUMPS/M, ColdFusion, Classic ASP, Visual FoxPro, ActionScript, AutoLISP | bug fix, add feature, migrate to modern stack, document an undocumented codebase, backfill tests | Upwork, Freelancer.com, Guru (index legacy keywords), HN |
| **N2** | **Domain DSLs, scripting & config** — regex, AWK/sed, jq, XSLT, LaTeX, Terraform/HCL, Ansible, Nix, Bash/PowerShell, SQL tuning, shaders, GDScript, Apps Script, Excel/Sheets + VBA | write/fix a script, format a document, optimize a query, automate a workflow | Reddit r/forhire, Upwork, Fiverr (productized), PPH Hourlies |
| **N3** | **Data formats & integration glue** — EDI (X12/EDIFACT), HL7/FHIR, SWIFT, iCal/vCard, proprietary/binary parsing, PDF/OCR pipelines, CSV/Excel->app, API-to-API, webhook glue, Zapier/Make/n8n steps | build a parser/converter, wire two systems, ETL a messy dataset | Upwork, Freelancer.com, HN, cold outbound to SMBs |
| **N4** | **Platform-specific customization** — WordPress/WooCommerce, Shopify Liquid, Salesforce Apex/Flows, HubSpot, Airtable, Notion API, QuickBooks/ERP, Webflow/Bubble custom code, browser extensions, Discord/Telegram/Slack bots | a plugin, a custom field, an automation, a bot | Codeable (WP), Storetasker (Shopify) — apply once; Upwork/Fiverr for the rest |
| **N5** | **Modernization & migration** — jQuery->React, AngularJS->Angular, Python2->3, PHP upgrades, framework migrations, monolith->module extraction, dep upgrades, type/test backfill, doc generation | a defined migration chunk with a passing test suite as the acceptance gate | Upwork, HN, Freelancer.com |
| **N6** | **Scientific / academic / data** — R/Stata/SPSS/SAS, MATLAB/Simulink, Mathematica, bioinformatics, GIS (QGIS/PostGIS), data viz, scraping+structuring, scientific LaTeX | a stats script, a reproducible analysis, a map, a cleaned dataset | Upwork, r/forhire, Freelancer.com, operator-sourced uni lists |
| **N7** | **AI-leverage meta-gigs** — RAG chatbots, AI agents/wrappers, prompt pipelines, doc-Q&A, "add AI to my app", fine-tune glue | a working AI feature/bot scoped to a use case | HN, Upwork, Contra, cold outbound |

N7 is ironically the fastest-growing and highest-margin: high demand, and the agent is
excellent at building its own kind of tooling.

## How niches plug into the existing pipeline

- **Scorer** already rewards AI-leverage margin and never penalizes obscure stacks. ACTION:
  add a **niche-keyword booster** — a curated keyword list (this taxonomy) that bumps
  confidence/score when a lead matches, because "obscure + bounded + documented" is our
  highest-win-rate zone.
- **Drafter** pitch angle for these: lead with capability + speed + a verifiable plan, NOT
  credentials. "I can deliver this [obscure thing] with a working test/demo by [date]." Claim
  outcome + proof, not years of human experience.
- **Reputation mode:** the small bounded N2/N4 scripts are ideal first wins — cheap, fast,
  verifiable, review-building.

## Starter keyword set (drop into scraper/search queries this week)

```
COBOL fix, RPG AS400, Delphi maintenance, VBA macro, Excel automation, Google Apps Script,
regex, XSLT, LaTeX format, Shopify Liquid, WooCommerce plugin, Zapier automation, Make.com,
PDF parser, web scraper script, API integration, Python2 to 3, jQuery to React, Airtable
script, Discord bot, Telegram bot, RAG chatbot, AI agent, HL7, EDI X12, QGIS, MATLAB script
```

`source-catalog.md` maps WHERE to run each of these. The scorer ranks what comes back.

## Sources
- [Freelance AS400/RPG jobs $83k-$145k (ZipRecruiter)](https://www.ziprecruiter.com/Jobs/Freelance-As400-Rpg-Programmer) ·
  [Freelance COBOL devs (Upwork)](https://www.upwork.com/hire/cobol-developers/) ·
  [AS400/iSeries (Guru)](https://www.guru.com/m/hire/freelancers/as400-iseries/)
