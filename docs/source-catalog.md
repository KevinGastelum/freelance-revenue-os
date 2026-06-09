# Master Source Catalog

_Every platform, validated and organized. Compiled 2026-06-08._
_Companions: `lead-sources.md` (the 5 models + ingest schema mapping) · `niche-strategy.md`
(what work to hunt). Models A-E are defined in `lead-sources.md`._

## How to read this

- **Model** — A=open bid · B=you-list/inbound · C=vetted match · D=community board · E=cold
  outbound (see `lead-sources.md`).
- **Fit** — **CORE** (project-based build/software work; you send a proposal/bid/cold-pitch;
  matches "build it & flip it") · **ADJACENT** (high AI-leverage but not software-building —
  content/translation; easy money, secondary to your framing) · **VETTED** (apply once, get
  matched; no scraping; run in parallel) · **SKIP** (poor fit; reason given).
- Per source: **Lead type · Categories · Access technique · Data structure · Outreach method.**

---

## TIER 1 — CORE, scrapeable (point the scraper here first)

### Hacker News — "Freelancer? Seeking freelancer?" (monthly)
- **Model D · CORE.** Lead: tech/startup clients posting real build work.
- Categories: web/app builds, integrations, AI/N7, scripting.
- Access: **HN Algolia API (open, free, no ToS issue).**
- Data: `hn.algolia.com/api/v1/search?tags=comment,story_<id>` -> `author`, `comment_text`
  (HTML), `created_at_i`, `objectID`. Find the month's story, pull its comments, keep
  "SEEKING FREELANCER".
- Outreach: email/DM the poster directly — capability + a verifiable plan + rate.

### Reddit — r/forhire (+ r/slavelabour, r/DoneDirtCheap)
- **Model D · CORE.** Lead: "[Hiring]" posts. r/forhire $15/hr floor, ~50/day; the other two
  are sub-$30 quick wins (reputation mode).
- Categories: scripting/N2, small builds/N4, bots, data, web.
- Access: **open JSON** (`reddit.com/r/forhire/new.json?limit=100`, custom UA, ~60 req/min) or
  official OAuth API for volume.
- Data: `data.children[].data` -> `title`, `selftext`, `author`, `created_utc`, `permalink`,
  `link_flair_text` (keep "Hiring").
- Outreach: reply per subreddit rules + DM a quote.

### Freelancer.com
- **Model A · CORE** (the one big bid-marketplace with a real public API).
- Lead: clients post projects; you bid fixed/hourly vs other bidders. High volume, lots of
  low-budget global competition — lean on the niche filter.
- Categories: everything, incl. N1 legacy (indexes AS400/COBOL/Delphi keywords).
- Access: **official REST API, OAuth** — `GET /api/projects/0.1/projects/active/`.
- Data: `budget {minimum, maximum}`, `currency`, `type` (fixed/hourly), `jobs[]`, `title`,
  `description`, `bid_stats`. Maps cleanly to the `ingest` schema.
- Outreach: bid + short proposal; win-rate comes from the niche edge, not price.

### Google Places (no-website businesses) — cold outbound
- **Model E · CORE, highest margin** (no platform cut, no bid competition).
- Lead: local SMBs with no `website` field = needs-a-site. ~27% of US small biz (~8M) in 2026;
  highest no-site rates: cleaning 45-50%, retail 40-45%, trades 35-40%.
- Categories: website builds, booking/automation, "add AI"/N7.
- Access: **Google Places API** (also Yelp, BuiltWith, Secretary-of-State filings).
- Data: business records; filter where `website` absent; capture name, category, phone, maps url.
- Outreach: cold email/DM/call with a value-first pitch (or a pre-built demo site).

---

## TIER 2 — CORE, but gated / not scrapeable (manual browse or paid relay)

| Source | Model | Lead type | Access / Data | Outreach |
|---|---|---|---|---|
| **Upwork** | A · CORE | largest open-bid; fixed/hourly | RSS retired 2024; API partner-gated; **do NOT raw-scrape (ban risk).** Route via a paid alert relay ($15-29/mo, Vollna/UpHunt) into the operator inbox -> `ingest` | proposal + Connects credits |
| **Fiverr** | B · CORE (productized) | you publish "gigs"; buyers buy; also buyer Briefs | inbound — no job feed to scrape. Set up productized AI/dev gigs (build-a-bot, build-a-script) | buyers come to your listing; optimize gig SEO |
| **PeoplePerHour** | A · CORE | bid on briefs; post fixed "Hourlies" | no public API/RSS (old `projects_rss` gone); manual browse | bid or list an Hourlie |
| **Guru** | A · CORE | hourly/milestone via WorkRooms | no public API; manual browse (indexes legacy keywords) | quote + WorkRoom |
| **Truelancer** | A · CORE | traditional bidding, 10% freelancer fee | no public API; manual/HTML | bid + proposal |
| **GoLance** | A/C · CORE | direct-matching (not bidding wars), 0% buyer fee / 7.95% freelancer | profile + match; no public job API | strong vetted profile -> inbound match |
| **Contra** | A/B · CORE | commission-free; apply to posts + portfolio inbound; "Indy AI" extension scans LinkedIn/X | no documented public job API; portfolio-first | apply to project posts + maintain portfolio |
| **Jobbers (jobbers.io)** | A/B · CORE | commission-free; clients post + you list a profile; ~300k daily visits | no documented public API | apply to posts / get found |
| **Hubstaff Talent** | B · CORE-adjacent | 100% free directory; you list a profile, clients contact you | inbound only; no job feed | optimize profile -> inbound |
| **Legiit** | B · ADJACENT | Fiverr-style you-list; SEO/marketing/IT/**AI marketplace** | inbound listings; free directory, order fees | publish service listings |

---

## TIER 3 — VETTED networks (apply once, get matched; no scraping; parallel track) — Model C

Pass the screen, then receive client briefs. Higher rates, less competition. Worth applying to
the dev ones now while the scraper feeds Tier 1.

- **Dev/build (apply these):** Toptal (top-3%, enterprise, 2-5x rates) · Arc.dev · Gun.io ·
  Gigster · Lemon.io (~1% accept, startups) · Flexiple · ScalablePath · **Codeable** (WordPress,
  brief->3-5 experts, no bidding) · **Storetasker** (Shopify, matched in minutes) ·
  **Braintrust** (client posts, 15% client fee, talent keeps 100%).
- **Design (only if you take design work):** Folyo (curated design jobs) · Awesomic
  (subscription design matching).
- Outreach for all: pass vetting -> accept/decline algorithmic matches. No feed to scrape.

---

## TIER 4 — ADJACENT (high AI-leverage, but NOT "building software")

Easy AI money if you want it, but off your stated "build & flip" framing — treat as secondary.

- **Content/writing networks (Model C):** Contently, ClearVoice, Skyword, Compose.ly,
  WriterAccess, Verblio — apply, get matched to writing briefs. AI writes well; race-to-quality.
- **Writing task hubs (Model B/queue):** Textbroker, iWriter, Constant Content — claim open
  article briefs by rating tier. Low rate, high volume.
- **Translation:** Proz.com — industry-standard directory; AI translation + human polish.

---

## TIER 5 — SKIP (poor fit — listed so we don't revisit them)

| Source(s) | Why skip |
|---|---|
| **Belay, Boldly, Time Etc, MyOutDesk, Prialto, Zirtual** | VA/admin — ongoing human relationships, not bounded buildable deliverables. |
| **Voices** | Voiceover — intrinsically human-embodiment; hard-NO per niche-strategy filters. |
| **99designs, Designhill, DesignCrowd** | Design *contests* — submit work speculatively, maybe win. Bad margin model (unpaid spec work); AI doesn't fix the gamble. |
| **Clickworker** | Micro-tasks (data entry, image tagging) — value too low even for reputation. |
| **MarketerHire, Zavops, GrowTal, Mayple, Wripple** | Marketing-strategy networks — ongoing advisory, not bounded builds. (Revisit only if a productized "build a marketing automation" angle emerges -> then it's N4/N7.) |

---

## Action summary

1. **Scraper targets, in order:** HN Algolia -> Reddit JSON -> Freelancer.com API -> Google
   Places. All legitimate public APIs (see `lead-sources.md` build order).
2. **Parallel manual/relay:** apply to Toptal/Codeable/Storetasker/Lemon.io; set up 2-3 Fiverr
   productized AI gigs; consider an Upwork alert relay.
3. **Filter everything through `niche-strategy.md`** — hunt N1-N7, skip the hard-NO list.
4. Whatever a source returns, the scraper emits the `ingest` schema (`lead-sources.md` mapping)
   and the scorer ranks it.

## Sources
- [Hubstaff Talent (free, operational 2026)](https://talent.hubstaff.com/) ·
  [Legiit marketplace](https://legiit.com/marketplace) ·
  [goLance vs Upwork (0% buyer fee, direct match)](https://golance.com/hiring/api-developers-vs-upwork) ·
  [Truelancer review 2026](https://www.stackinsight.net/2026-truelancer-review/)
- [Contra](https://contra.com/) · [Jobbers vs Contra (zero-commission)](https://www.jobbers.io/jobbers-io-vs-contra-zero-commission-platform-showdown/) ·
  [Awesomic fastest platforms](https://www.awesomic.com/blog/10-fastest-freelance-platforms-for-startups-in-2025)
- [60 freelance platforms compared (Useme)](https://useme.com/en/blog/freelance-platforms/)
