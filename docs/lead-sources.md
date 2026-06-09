# Lead Sources & Scraper Targets

_Reference for the scraper + `freelance-os ingest`. Compiled 2026-06-08._
_Companions: `source-catalog.md` (every validated platform) · `niche-strategy.md` (what to hunt)._

Goal: project-based "build it and flip a profit" leads (send a proposal at $X/job or
$X/hr), NOT part-time or full-time employment. Ranked for an AI-leverage, scraper-fed
pipeline that emits the `ingest` CSV/JSON schema.

---

## The 5 lead-acquisition models (this answers "which are like this, which differ")

| Model | How a lead reaches you | Do you send a proposal? | Scrapeable feed? |
|---|---|---|---|
| **A. Open bid marketplace** | Client posts a job; you browse listings | YES — you bid $X/hr or $X fixed, competing with other bidders | Listings exist but ToS restricts scraping; APIs gated |
| **B. You-list / productized** | You publish a service; buyers come to you | No — buyers purchase your listing (inbound) | No job feed to scrape — the "lead" is a buyer browsing YOU |
| **C. Curated / vetted match** | You pass a vetting test once; platform algo-matches you to a client brief | No bidding — you accept/decline a match | No public listings to scrape (gated) |
| **D. Community board** | People post free-text "hiring" posts | YES — you reply/DM with a pitch | YES — open JSON/APIs, free, low friction |
| **E. Cold outbound** | No marketplace — you find businesses and pitch them | YES — you cold-pitch a fixed price | YES — Maps/Places/BuiltWith; highest margin, no platform fee/competition |

**What this means for you:**
- **Model A** is exactly the "parse listings -> send proposal" flow you described. Richest
  volume, but most have anti-scraping ToS and gated APIs (Freelancer.com is the exception —
  real public API).
- **Model D** is the same browse-and-pitch flow but on OPEN data (Hacker News, Reddit) — the
  cleanest legitimate scraper targets, zero ToS friction, real project work.
- **Model E** is the highest-margin play (no 10-20% platform cut, no bid competition) but
  needs outreach, not just a proposal in a marketplace inbox.
- **Models B and C** are NOT scraper targets — there's no job feed. They're "get accepted,
  receive inbound" channels. Worth applying to in parallel, but the scraper can't feed them.

---

## Ranked source list

### TIER 1 — best scraper targets (open data, real project leads, send-a-proposal)

**Hacker News "Freelancer? Seeking freelancer?" (monthly)** — Model D
- Link: posted ~1st of each month, e.g. `news.ycombinator.com/item?id=47976154` (May 2026).
- Mechanic: "SEEKING FREELANCER" comments are leads; you email/DM the poster with a pitch +
  rate. High-quality startup/tech clients, often real build work.
- **Scrape (fully open, no ToS issue):** HN Algolia API.
  `https://hn.algolia.com/api/v1/search?tags=story&query=Freelancer%20Seeking%20freelancer`
  -> find the month's story `objectID`, then
  `https://hn.algolia.com/api/v1/search?tags=comment,story_<ID>&hitsPerPage=1000`.
  Fields per hit: `author`, `comment_text` (HTML), `created_at_i`, `objectID`,
  `story_id`. Filter `comment_text` for "SEEKING FREELANCER".
- Difficulty: trivial. **Start here.**

**Reddit r/forhire** — Model D
- Link: `reddit.com/r/forhire` (filter flair = **Hiring**). $15/hr minimum, ~50 posts/day.
- Mechanic: "[Hiring]" posts are leads; reply per subreddit rules + DM with a pitch/quote.
- **Scrape (open JSON):** `https://www.reddit.com/r/forhire/new.json?limit=100` (set a
  custom User-Agent; respect rate limits, ~60 req/min). Path:
  `data.children[].data` -> `title`, `selftext`, `author`, `created_utc`, `permalink`,
  `link_flair_text` (keep == "Hiring"). For higher volume use the official OAuth API.
- Difficulty: trivial. **Second target.**

**Reddit r/slavelabour & r/DoneDirtCheap** — Model D
- Same JSON scrape as above. Tasks **under $30** (r/slavelabour rule). Low dollar, but per
  your reputation-mode strategy these are easy wins that build standing — score them.

**Freelancer.com** — Model A (the one with a real public API)
- Link: `freelancer.com`; API docs `developers.freelancer.com`.
- Mechanic: clients post projects; you bid (fixed or hourly), competing with other bidders.
- **Scrape (official REST API, OAuth):**
  `GET /api/projects/0.1/projects/active/` with filters (jobs, budget, query). Returns
  `budget {minimum, maximum}`, `currency`, `jobs[]`, `type` (fixed/hourly), `title`,
  `description`, `bid_stats`. This is a sanctioned feed — prefer it over scraping HTML.
- Difficulty: low (register an app). High volume, but lots of low-budget global competition.

### TIER 2 — high volume, but gated/anti-scraping (use official channel or a paid alert relay)

**Upwork** — Model A
- Largest open-bid marketplace; clients post fixed/hourly jobs, you send proposals (cost
  "Connects"). **RSS feed was retired in 2024.** Official GraphQL API is partner-gated and
  selective. Direct scraping violates ToS and can flag/ban your account.
- **Legit options:** (a) apply for API partner access; (b) a managed alert service
  ($15-29/mo, e.g. Vollna/UpHunt) that relays scored jobs to a webhook/feed your ingest can
  read — this keeps you ToS-clean and is the operator's "own alert inbox" per the build spec.
- Do NOT point a raw scraper at Upwork. Feed `ingest` from the alert relay instead.

**Fiverr** — Model B (mostly)
- You publish gigs; buyers purchase (inbound). Also has buyer "Briefs" matching. Not a
  scraper target — there's no job feed; leads come to your listing. Worth setting up a few
  productized gigs in parallel, but the scraper can't feed it.

**PeoplePerHour, Guru, Workana** — Model A
- Open-bid marketplaces (browse projects -> send proposal, fixed or hourly). **No official
  public job API / RSS** (PPH's old `projects_rss` was discontinued). Scraping HTML is
  against ToS and fragile. Treat as manual-browse or via a paid relay; lower priority than
  Freelancer.com which has a real API.

### TIER 3 — curated / vetted (NOT scraper targets; apply once, receive inbound matches) — Model C

You can't scrape these — there are no public listings. You pass vetting, then the platform
matches you to client briefs. Higher rates, less competition. Apply in parallel:

- **Toptal** — top-3% screening; enterprise clients; 2-5x open-market rates.
- **Codeable** — WordPress only; client posts a brief, algo matches 3-5 vetted experts, no
  bidding. Good if you target WP work.
- **Storetasker** — Shopify only; same match-not-bid model, matched within minutes.
- **Lemon.io** — multi-stack, startup clients; ~1% acceptance; matching team pairs you to a
  brief. **Braintrust** — client posts listing, 15% client-side fee, talent keeps 100%.
- **Contra** — commission-free; $29/mo for priority placement; more of a profile/portfolio
  inbound channel than a job feed.

### TIER 4 — cold outbound (highest margin, needs outreach not just a proposal) — Model E

No platform cut, no bid competition — you generate a list and pitch a fixed price. ~27% of
US small businesses (~8M) still have no website in 2026; highest no-site rates: cleaning/
laundry (45-50%), local retail (40-45%), plumbers/electricians (35-40%), auto repair
(35-40%), tutoring/coaching (30-35%).

- **Google Maps / Places API** — structured business records; flag listings with no
  `website` field = leads. Best automated source.
- **Yelp, Secretary-of-State filings, industry directories** — same idea, free.
- **BuiltWith / Wappalyzer** — target businesses by their CURRENT stack (e.g. outdated/no
  CMS) when you sell a specific build.
- **Lead-finder tools** (WeblessWorld, Targetron, Outscraper) — productized "businesses
  without websites" lists if you want to skip building the scraper for this tier.

---

## Mapping each source to the `ingest` schema

The scraper should emit rows matching `ingest`'s columns so they drop in with zero glue:

| ingest column | HN comment | Reddit post | Freelancer.com API | Google Places |
|---|---|---|---|---|
| `title` | first line of `comment_text` | `title` | `title` | business name |
| `description` | `comment_text` (strip HTML) | `selftext` | `description` | category + "needs website" |
| `url` | `https://news.ycombinator.com/item?id=<objectID>` | `https://reddit.com<permalink>` | project SEO url | Maps url |
| `budget` | parse from text (often absent) | parse from text | `budget.minimum`-`maximum` + `currency` + `type` | (none -> you quote) |
| `skills` | parse keywords | parse keywords | `jobs[].name` | service type |
| `location`/`remote` | usually "Remote" | parse | client `country` | local |
| `client_*` boosters | author karma (proxy) | author age/karma | client rating/reviews/payment_verified | — |

Where `budget` is absent (HN/Reddit/cold), the scorer falls back to effort + confidence;
real PROJECT budgets (Freelancer.com) rank correctly already.

---

## Recommended build order for the scraper

1. **HN Algolia API** — open, free, real build leads, zero ToS risk. Ship first.
2. **Reddit r/forhire + r/slavelabour JSON** — open, high cadence, reputation wins.
3. **Freelancer.com REST API** — sanctioned, structured budgets, high volume.
4. **Google Places (no-website filter)** — the cold-outbound, highest-margin tier.
5. Upwork/PPH/Guru: do NOT raw-scrape (ToS/ban). If you want their volume, route through a
   paid alert relay into the operator alert inbox and feed `ingest` from that.

All four primary targets are legitimate public APIs — consistent with the project's
declined-evasion-scraping stance and the `pull` build spec.

## Sources
- [Best freelance websites 2026 (Upwork)](https://www.upwork.com/resources/best-freelance-websites) ·
  [Useme 60-site comparison](https://useme.com/en/blog/freelance-platforms/)
- [Upwork RSS retired — 2026 alternatives (UpHunt)](https://uphunt.io/blog/rss-alternative)
- [Freelancer.com API portal](https://developers.freelancer.com/)
- [HN Freelancer? Seeking freelancer? (May 2026)](https://news.ycombinator.com/item?id=47976154) ·
  [HNHIRING aggregator](https://hnhiring.com/)
- [Best Reddit communities for freelancers](https://odd-angles-media.com/blog/best-reddit-communities-for-freelancers) ·
  [r/slavelabour intro](https://bettermarketing.pub/an-introduction-to-reddits-slave-labour-subreddit-d5e156655ba1)
- [Codeable posting a project](https://help.codeable.io/en/collections/47931-posting-your-project) ·
  [Storetasker become an expert](https://resources.storetasker.com/become-an-expert) ·
  [Lemon.io for developers](https://lemon.io/for-developers/)
- [Braintrust pricing](https://www.braintrust.dev/pricing) · [Is Contra legit 2026](https://remote100k.com/blog/is-contra-legit)
- [Find local businesses without a website 2026 (Trovn)](https://trovn.io/blog/find-local-businesses-without-website) ·
  [B2BLeadFinder](https://b2bleadfinder.io/blog/how-to-find-businesses-without-websites)
