# LGN Review Generator — Implementation Plan (Draft v1)

Status: DRAFT — build sequencing only, no code written yet.
Companion to: `Review_Tool_Spec.md` (read that first for behavior/requirements).
Last updated: 2026-07-09

---

## Assumptions being made to keep the plan moving

The spec left a few items open (§10). Rather than stall on them, here's what this plan assumes
unless you tell me otherwise — flag any of these and I'll adjust before build starts:

1. **Hosting** — building host-agnostic: a static frontend + one small serverless function
   (the only piece that *must* run somewhere with a server, since it holds the Claude API key).
   This can be deployed as a standalone page on its own domain/subdomain, or embedded via iframe
   into an existing site later — the decision doesn't block starting the build, only the final
   deploy step.
2. **Repeat-platform block is hard, no undo** (per spec §3a recommendation) — going with this
   unless you say otherwise.
3. ~~**Google Place ID**~~ — resolved, see Phase 0 below.
4. ~~**Question wording (spec §3)**~~ — reviewed and approved as-is.

**Yelp is out of scope entirely** (operator's call) — platforms are Google, Facebook, BBB only.

---

## Phase 0 — Groundwork (before any UI work)

- ~~Look up LGN's Google Place ID~~ — done. Verified platform links (spec §7):
  - Google: `https://www.google.com/maps?cid=190491404382669009`
  - Facebook: `https://www.facebook.com/TheLibertyGroupofNV/`
  - BBB: `https://www.bbb.org/us/nv/reno/profile/business-brokers/the-liberty-group-of-nevada-llc-1166-90023748`
    (exact review-submission subpath still needs a manual check — BBB blocks automated access)
- ~~Decide credential handling~~ — done. Same pattern as the rest of LGN's tooling: a
  `db_credentials.py`-style local-only file (Supabase URL/key, Claude API key), resolved via a
  `LGN_CREDENTIALS_PATH`-style environment variable, never synced into the SharePoint folder.
- ~~Question wording review~~ — done. Kathryn reviewed and approved the draft list as-is.

**Phase 0 is complete.** Nothing left blocking Phase 1.

## Phase 1 — Skeleton app

- Basic single-page app shell: landing screen → chat container → draft screen → platform
  picker. No real logic yet, just the screen flow and navigation between them.
- `sessionStorage`-backed session state: tracks which questions have been answered, which
  platform(s) have been used this session (powers the block in spec §3a).

**Done.** Built as a plain static HTML/CSS/JS app at `app/` (no build step, host-agnostic per the
Phase 0 assumption) and verified end-to-end in a browser preview:
- Landing → chat → platform picker → draft → copy & open real platform tab → back to picker.
- After the first platform is used, it shows "Posted ✓" and is no longer clickable (§3a hard
  block) while the other two remain selectable.
- Selecting a second platform correctly shows the "we've adjusted the wording" repeat-site
  notice (§3 step 6) before the draft.
- Session state survives a page reload (sessionStorage), so refreshing mid-flow doesn't lose
  progress.
- Draft text and generation are still placeholders — real content arrives in Phase 3/4.
- Runs locally via `.claude/launch.json` config `review-tool` (python static server on
  port 5173, serving the `app/` folder) — use `preview_start` with that name to view it.

## Phase 2 — Conversational Q&A

- Chat UI presenting the question list one at a time (typed answers first).
- Add browser microphone input (Web Speech API) alongside typing.
- Wire up the "which platforms are available" logic — Google/Facebook/BBB links from
  Phase 0, each carrying LGN's business identifiers (Place ID etc.) — done in Phase 1.

**Done.** Real chat UI built with the 7-question list from spec §3, one at a time as chat
bubbles (bot prompt, then the client's answer), plus a final optional name/email step. Verified
end-to-end in the browser:
- All 6 required questions plus the optional 7th flow correctly; the "Skip this one" button only
  appears on the optional question.
- Contact step (name/email) correctly marked "totally optional" — tested skipping it entirely,
  which still advances to "Continue to review."
- Answers land in `state.chat.answers` keyed by question id, ready for Phase 3 to feed into
  generation.
- Voice input wired via the Web Speech API (`SpeechRecognition`/`webkitSpeechRecognition`);
  mic button disables itself with an explanatory tooltip in browsers that don't support it
  (per the spec's accepted Safari/Firefox tradeoff). Confirmed supported and enabled in this
  Chromium-based test browser; real-device mic testing across Safari/Firefox still pending
  for the Phase 8 test pass.
- Reload-resume verified again: reloading mid-conversation correctly restores the full chat
  history and lands back on the right next question.

## Phase 3 — Review generation (backend)

- Minimal serverless function that takes the Q&A transcript + target platform and calls the
  Claude API, following the generation guardrails in spec §6 (first person, no invented facts,
  natural tone, ~60–120 words, platform-specific rewording on repeat calls).
- This is the one piece of real backend logic in the whole app — everything else is frontend
  state and static content.

**Done.** Built as `server/generate_review.py` — a stdlib-only Python HTTP server (no pip
installs required), so it runs the same way regardless of eventual hosting choice. Runs on
`localhost:5174` via the `review-tool-backend` entry in `.claude/launch.json`.

- **Credentials:** follows the exact pattern already used for `db_credentials.py` — reads
  `ANTHROPIC_API_KEY` from a `review_tool_credentials.py` file living in the same local-only
  folder `LGN_CREDENTIALS_PATH` already points to. Template at
  `Review_Tool/review_tool_credentials_TEMPLATE.py`. **Action needed from Stewart/Kathryn:**
  copy that template into your local credentials folder, rename it, and fill in a real Claude
  API key from https://console.anthropic.com/ — I deliberately never asked for or handled the
  real key myself.
- **Prompt** enforces all of spec §6's guardrails (first person, no invented facts, no
  marketing-speak, ~60–120 words, honest tone for mixed/negative answers) and, when a client is
  posting to a second/third platform, includes their prior generated draft(s) so the model can
  genuinely reword rather than repeat itself — same facts, different phrasing.
- **Frontend wiring:** the draft screen now calls this backend for real, shows "Writing your
  review draft…" while waiting, and disables Approve until it resolves.
- **Verified all three failure paths** (since I have no real API key to test a successful
  generation with):
  1. Backend not running → `ERR_CONNECTION_REFUSED` → graceful fallback: empty textarea with
     placeholder text inviting the client to write their own review, Approve re-enabled.
  2. Backend running, no credentials file → clean `credentials_missing` JSON error → same
     graceful fallback.
  3. Backend running with a syntactically-valid but fake key (dummy value, never a real
     credential) → real network round-trip to `api.anthropic.com`, correctly caught the 401
     response, returned a clean `claude_api_error` → same graceful fallback.
  In every failure case the client is never blocked from writing and posting their own review —
  the app degrades to a blank editable box rather than an error screen.
- **Live generation now verified.** Kathryn added her real Claude API key to
  `C:\Users\kguthrie\LGN_Local\review_tool_credentials.py` and confirmed a real end-to-end run
  in the app: a first draft generated correctly (first person, honest, right length, no
  invented facts), and a second-platform draft came back genuinely reworded — same facts,
  different phrasing — with the repeat-site notice showing correctly.
- One gotcha hit during setup, worth remembering for the next team member who sets this up:
  the credentials file has to be renamed from `review_tool_credentials_TEMPLATE.py` to exactly
  `review_tool_credentials.py` after copying it — a copy left with the `_TEMPLATE` suffix in the
  filename won't be picked up, since the backend looks for that exact filename.

**Refactored for Vercel (hosting decision, see §9/spec §9):** the Claude-calling logic (prompt
building, guardrails, credential loading) now lives in one shared module,
`api/_review_logic.py`, imported by both entrypoints so there's a single source of truth:
- `server/generate_review.py` — local dev entrypoint (unchanged behavior, still a standalone
  stdlib server on port 5174, still CORS-enabled since local dev runs frontend/backend on two
  different ports).
- `api/generate-review.py` — the Vercel entrypoint. Matches Vercel's Python function convention
  (a class named `handler` extending `BaseHTTPRequestHandler` in a file under `api/`). No CORS
  needed here since frontend and function deploy under the same origin in production.
- `load_api_key()` now checks a plain `ANTHROPIC_API_KEY` environment variable first (how Vercel
  provides secrets), falling back to the local `review_tool_credentials.py` file lookup only if
  that's not set — so local dev keeps working exactly as before with zero extra config.
- `app/app.js`'s `BACKEND_URL` is now environment-aware: an absolute `http://localhost:5174` when
  running the local two-port dev setup, or an empty string (same-origin relative path) anywhere
  else — verified this didn't break local testing (re-ran the full chat → draft → generation
  flow end-to-end after the refactor, still works).
- Added `vercel.json` (`{"outputDirectory": "app"}`) so Vercel serves the static frontend from
  `app/` at the project root, and `.vercelignore` to keep `server/` (local-dev only), the spec
  docs, and the credentials template out of the deployed bundle.

## Phase 4 — Draft/proof screen

- Editable textarea showing the generated draft, with an explicit approve action (no
  auto-advance).
- Wire in the "second site" notice (spec §3 step 6) before generating a second/third/fourth
  variant.

**Partially done ahead of schedule:** a per-platform "how to post" instruction now shows on the
draft screen (spec §3 step 4), telling the client what happens after they click Approve and what
to do on the platform's own page (find the write-a-review button, paste). Content is real, not a
placeholder — only the review draft text above it is still a stub pending Phase 3.
Google's and BBB's instructions reference verified links; Facebook's `/reviews` URL still needs
a manual spot-check (see spec §7) — the instruction text itself doesn't depend on that outcome.

## Phase 5 — Copy & redirect + the repeat-platform block

- Clipboard copy on approve, new-tab redirect to the platform's review page (per spec §7 table).
- Disable/label already-used platforms everywhere they appear in the UI (spec §3a).

## Phase 6 — Analytics logging

- Supabase table(s) per spec §8: session funnel data, per-platform-use log (order, variant
  text, edited text, timestamp), optional name/email.
- Reuses LGN's existing Supabase instance; new table(s), separate from the deal-sourcing schema.

## Phase 7 — Branding pass

- Apply LGN's visual identity (logo, colors, fonts) to the shell built in Phases 1–5.

## Phase 8 — Test pass before launch

- Click through the full flow end-to-end for all three platforms, on both desktop and mobile,
  in at least Chrome and Safari (voice input is expected to be weaker in Safari — confirm typing
  fallback works cleanly there).
- Confirm the repeat-platform block actually prevents a second Google/Facebook/BBB copy
  within one session.
- Run a mixed/negative-sentiment test conversation through the flow and confirm the platform
  buttons are still all shown (no accidental gating logic sneaking in).

## Phase 9 — Launch

- ~~Decide final hosting~~ — resolved: Vercel (see spec §9).
- Point real client traffic at it (e.g., included in a post-close email/link).

### Remaining steps — these require Stewart/Kathryn directly; I can't do them for you

1. **Create a Vercel account** (free) at vercel.com, if you don't already have one.
2. **Pick a deploy method** — two options, pick whichever is more comfortable:
   - **Git-based (recommended long-term):** push this project to a GitHub repo, then "Import
     Project" from that repo in the Vercel dashboard. Every future `git push` auto-redeploys.
     Requires a GitHub account and turning this folder into a git repo (it isn't one yet —
     I can set that up if you go this route).
   - **CLI-based (faster for a one-time deploy):** install Node.js, then run `npm install -g
     vercel` and `vercel` from inside the `Review Tool` folder — it deploys directly from your
     machine, no GitHub needed. Re-deploying later means running `vercel` again by hand.
3. **Set the real Claude API key as a Vercel environment variable** — Project Settings →
   Environment Variables → add `ANTHROPIC_API_KEY` with your real key. This is separate from
   the local `review_tool_credentials.py` file (that one only matters for local testing) — never
   paste the real key into any file that goes into git or gets deployed.
4. **Point a subdomain at it** (e.g. `reviews.libertygroupnv.com`) — add it in Vercel's project
   domain settings, then add the CNAME record Vercel gives you at wherever your domain's DNS is
   managed. Vercel issues the HTTPS certificate automatically once that's done.
5. **Add the WordPress link** — a page or button linking to that subdomain, or an iframe embed
   if you want it to feel more native to the site (needs `allow="microphone; clipboard-write"`
   on the iframe tag for voice input and copy-to-clipboard to work inside it).

### Still open: abuse protection for the public endpoint

Once this is live, `/api/generate-review` is reachable by anyone, not just people you've
emailed — worth deciding before wide rollout whether that's an acceptable risk given the link
won't be publicly posted/indexed anywhere (low discovery risk), or whether to add a lightweight
guard (e.g., a shared secret token the frontend sends along — deters casual bots, though anyone
reading the public `app.js` could find it; real rate-limiting would need an external store like
Vercel KV, which is more setup). Vercel's Hobby plan does include a baseline web application
firewall/DDoS mitigation for free, which covers a good chunk of generic abuse already.

---

## What happens next

This plan is sequencing only — no code yet. Say the word when you want to start Phase 0/1, or
if you want to adjust any of the assumptions above first.
