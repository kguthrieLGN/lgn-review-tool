# LGN Review Generator — Spec (Draft v1)

Status: DRAFT — for discussion, not yet approved for build.
Owner: Kathryn/Stewart Guthrie, The Liberty Group of Nevada (LGN)
Last updated: 2026-07-09

---

## 1. Purpose

A landing-page tool that turns a past LGN client (buyer or seller in a brokered deal) into a
posted public review with as little friction as possible. The client has a short, guided
conversation about their experience; the app drafts a review in their own words; the client
approves/edits it; the app copies it to their clipboard and sends them straight to the specific
review platform (already on LGN's business profile) to paste and submit.

Core promise to the client: "60 seconds of talking → a review you're happy with, ready to paste."

## 2. Scope for v1

- Single business: The Liberty Group of Nevada only (not a multi-client/multi-tenant product).
- Review platforms: Google Business Profile, Facebook, BBB. (Yelp intentionally excluded —
  operator's call.)
- Input modes: typing and browser microphone (speech-to-text).
- Reviewer identity (name/email) is fully optional — never required to complete the flow.
- Basic usage analytics (funnel + which platform + which agent mentioned).

## 3. End-to-end user flow

1. **Landing page** — short intro, "Share your experience" CTA, explains it takes ~1 minute,
   mic or typing, and that they'll review/edit before anything is posted anywhere.
2. **Conversational Q&A** (chat UI, one question at a time, mic button next to the text input):
   - What did you come to LGN for? (buying a business / selling a business / valuation /
     other — free text, not a rigid dropdown, so it stays conversational)
   - Which team member(s) did you primarily work with? *(feeds the staff-mention feature — see §5)*
   - What stood out most about working with them or the process?
   - Was there anything that surprised you — good or challenging — along the way?
   - How did things turn out, and how do you feel about it?
   - Would you recommend LGN to someone else buying or selling a business — why or why not?
   - Anything else you'd like to add? *(optional, skippable)*
   - Name and email — explicitly marked "totally optional, just for our records."
3. **Platform selection (one at a time)** — instead of showing all three platform buttons at once,
   the client picks a single platform to start with from a simple list (Google / Facebook / BBB).
   This becomes the "active platform" for the next step. All three are enabled at this point.
4. **Draft/proof screen** — the app generates a review draft tailored to the active platform and
   shows it in an editable textarea. Client can tweak wording freely before continuing. No
   auto-submit anywhere — this step is mandatory, not skippable, both for authenticity and so the
   client is always the one who "wrote" it. Since no platform allows linking straight into a
   pre-filled, ready-to-submit review box (§7) — the client always lands on the business's page
   and has to click that platform's own "write a review" button once themselves — this screen
   also shows a short platform-specific instruction (e.g., *"We'll open Google's page in a new
   tab. Once there, click 'Write a review,' then paste (Ctrl+V or Cmd+V) into the box that
   appears."*) so the client knows what to expect instead of being surprised by the extra click.
5. **Copy & go** — approving the draft copies it to the clipboard and opens that platform's review
   page for LGN's specific business profile in a new tab, with a short "Pasted it? Great — thank
   you!" confirmation. That platform is now marked **posted** for the rest of this session — see
   §3a below.
6. **Offer to post elsewhere (optional)** — back on the LGN tab, the client is told "Want to
   share this on another site? If so, click the button for the site above, and we'll provide an
   updated review for that site." The already-used platform is visibly disabled/labeled
   "Posted ✓" in this list, so there's no path to re-selecting it by accident.
   - If they pick a different platform, show a short explanatory note first: *"Since you're
     sharing this on a second site, we'll adjust the wording a bit so it's not identical across
     platforms — that reads better to reviewers and helps avoid spam filters."*
   - Generate a second, platform-tailored variant (same facts, different phrasing) and show it
     as a new draft/proof screen (same pattern as step 4 — the client still approves/edits before
     anything is copied).
   - Approve → copy & go (step 5) → that platform is also marked posted.
   - This repeats for the third platform if the client wants, with the same variant +
     explanatory-note pattern every time after the first.
7. Session ends when the client closes the tab or declines to post anywhere else.

### 3a. Blocking a repeat post to the same platform

- Once a platform is marked "posted" in the current session, its option is disabled everywhere
  it appears in the UI (the initial picker in step 3 if the client somehow lands there again,
  and the "post elsewhere" list in step 6). This is a hard client-side guard, not a soft warning —
  the goal is to make it structurally impossible to trigger a second copy/redirect to a platform
  already used this session.
- **Important limitation to have eyes open on:** this is a browser-session guard (tracked in
  `sessionStorage`, no login involved), not a security control. It reliably prevents *accidental*
  double-clicks within one continuous visit. It cannot stop someone who deliberately closes the
  tab and restarts the whole flow from posting to the same platform twice — there's no account
  system in v1 to detect that across sessions. Worth being explicit with Stewart/Kathryn that
  this solves the "oops, clicked Google twice in a row" case, not determined abuse.
- **Edge case — what if they click through but never actually finish posting** (e.g., they
  back out of Google's page)? Two options:
  - (a) Hard block, no undo — simplest, matches the "make sure we're not flagged" goal. **Recommended for v1.**
  - (b) Small "didn't actually post it? undo" link next to the disabled state — friendlier, but
    reopens the exact double-post risk this feature exists to prevent.
  Going with (a) unless you'd rather have the undo escape hatch.

## 4. Compliance guardrails (non-negotiable)

Google's Business Profile policies and the FTC's rules on fake/deceptive reviews both prohibit
**review gating** — filtering reviewers by sentiment before they reach the public review site,
or otherwise suppressing negative reviews. This app must not do that, ever. Concretely:

- Every client sees the **same conversation**, regardless of how the experience went.
- The draft reflects what they actually said — if the experience was mixed or negative, the
  drafted review is allowed to say so. The app does not steer wording toward positivity.
- The platform-picker buttons (§3 step 4) are shown to **everyone**, with no logic that hides
  or swaps them based on sentiment detected in the conversation.
- A private "send this feedback directly to our team" option may be offered, but only as an
  **additional** choice alongside the public platform buttons — never as a replacement, and
  never framed as an alternative to posting publicly.
- The mandatory edit/approve step (§3 step 4) means the client always has final control over
  the exact words posted — the app assists, it doesn't write reviews on someone's behalf.
- Note: the one-platform-at-a-time sequencing and per-platform variants (§3, §3a, §6) exist for
  a *technical* reason — avoiding duplicate-looking text and accidental double-submits — not to
  filter or steer reviewers by sentiment. Every client goes through the same sequencing regardless
  of how the conversation went, so this doesn't create a gating risk.

## 5. Staff/agent mentions

- One question in the flow asks which team member(s) the client worked with.
- If named, the generated review is encouraged (not forced) to reference that person by name,
  since specific, named-employee reviews read as more credible and are useful internally.
- Captured in analytics as a per-agent tag so LGN can see mention frequency and sentiment trend
  per team member over time.

## 6. Review generation

- Generation is done via an LLM call (Claude API) fed the full Q&A transcript, not just a
  template fill — so phrasing follows how the client actually talks (their own words/phrases
  reused where natural), not a canned structure.
- Guardrails on the generation prompt:
  - First person, past tense, reads like a real customer wrote it.
  - No invented facts — dollar amounts, timelines, or details not mentioned by the client
    must never be added.
  - No superlative-marketing language ("exceeded all expectations!!!") — keep it natural.
  - Default length ~60–120 words (roughly what most reviewers write; adjustable).
- **Decided:** distinct variant per platform, generated on demand rather than all three upfront.
  The first variant is generated right after the client picks their first platform (§3 step 4);
  each additional platform they choose to post to (§3 step 6) triggers generation of a new
  variant at that time, along with the "we'll adjust the wording" notice. This avoids wasting a
  generation call on platforms the client never visits, and matches the one-at-a-time flow.
  Rationale for variants at all — identical text posted verbatim across Google/Facebook/BBB reads
  as templated to anyone who cross-checks, and several platforms' spam/fraud filters flag reviews
  that appear duplicated across sites or in clusters right after a business prompts for reviews.
  Variants must stay 100% consistent on facts, just reworded.

## 7. Platform deep-link behavior

| Platform | Deep link support | Notes |
|---|---|---|
| Google Business Profile | Verified link: `https://www.google.com/maps?cid=190491404382669009` — confirmed via browser test that it lands directly on LGN's correct "Liberty Group of Nevada Inc" listing. One click from there to "Write a review." | The true single-click direct-to-composer link (`search.google.com/local/writereview?placeid=...`) needs Google's alphanumeric Place ID (`ChIJ...` format) — tried both the decimal CID (`190491404382669009`) and hex feature ID (`0x809940cd9caf31ef:0x2a4c2ec4afe88d1`) as the `placeid` param and both 404. Getting the real Place ID requires a Google Places API call (needs a Google Cloud API key/billing) or pulling it from the Business Profile Manager — treated as a nice-to-have upgrade, not a v1 blocker, since the `maps?cid=` link already works and matches the same "land on page, one more click" pattern as Facebook/BBB below. |
| Facebook | `https://www.facebook.com/TheLibertyGroupofNV/reviews` — base page verified; the `/reviews` suffix is a common convention for landing closer to the Recommendations tab, **not yet manually confirmed** (the browser tool used for verification blocks navigating facebook.com directly). Falls back gracefully to the main page if the suffix doesn't resolve as expected. | Requires the client to be logged into Facebook. Kathryn/Stewart: please spot-check this link once. |
| BBB | Business profile confirmed: `https://www.bbb.org/us/nv/reno/profile/business-brokers/the-liberty-group-of-nevada-llc-1166-90023748` | BBB blocks automated browser access, so the exact review-submission subpath (likely a "Customer Reviews" tab off this profile) still needs a manual check during build — the base profile URL itself is verified correct. |

None of these platforms support pre-filling the actual review text box (all disallow that for
anti-fraud reasons) — hence the clipboard-copy-then-paste pattern rather than a true auto-fill.

**Data hygiene note, unrelated to this app:** the Google search result you pasted showed LGN's
old address (819 Riverside Dr) rather than the current 6880 S. McCarran Blvd location — same
business listing (CID matches), just possibly stale info cached on that listing. Worth checking
the Google Business Profile Manager has the current address on file next time someone's in there.

## 8. Data & analytics

- Name/email: optional fields, stored only if the client chooses to provide them.
- Session log (recommend reusing LGN's existing Supabase instance, a new table, not the
  deal-sourcing tables): session start/end timestamps, which question steps were reached
  (funnel drop-off), staff member(s) mentioned, whether name/email were provided.
- Per-platform-use log within each session: which platforms were used, in what order, the
  generated variant text and the client's edited/final version for each, and a timestamp per
  platform click — this is what powers the "already posted this session" block in §3a and lets
  LGN see how often clients post to more than one site.
- Full Q&A transcript stored per session, so LGN can audit tone/quality and refine the question
  set over time.
- No way to confirm the client actually pasted/submitted on the platform's side (no platform
  gives us that signal) — "platform button clicked" is the closest available proxy for "review
  likely posted."
- **Decided and built:** the Claude API key lives in `review_tool_credentials.py`, in the exact
  same local-only folder `LGN_CREDENTIALS_PATH` already points to for `db_credentials.py` — no
  new environment variable needed. Template at `review_tool_credentials_TEMPLATE.py` (safe to
  keep in the synced folder; contains no real values). Never lives in the SharePoint-synced
  folder itself. The Supabase key (Phase 6) will follow the same file/pattern once built.

## 9. Architecture sketch (for the eventual build — not started yet)

- **Frontend:** a small single-page app (chat UI + draft/edit screen + platform buttons).
  Framework-agnostic decision, but nothing here needs to be complex.
- **Voice input:** browser-native Web Speech API — no server round-trip, free, works well in
  Chrome/Edge. (Per your call — accepting weaker support in Safari/Firefox as a v1 tradeoff.)
- **Backend need:** a minimal serverless function (or small endpoint) is required to call the
  Claude API, since the API key can never be exposed in browser JS. This is the one piece that
  can't be "just a static page."
- **Storage:** optional Supabase table(s) as described in §8, using LGN's existing instance.
- **Hosting: decided — Vercel.** Static frontend + the Python function both deploy together
  under one Vercel project/domain (e.g. a subdomain like `reviews.libertygroupnv.com`), with the
  WordPress site just linking or iframing to it. Chosen over Netlify (10-second function
  timeout is too tight a margin for a Claude generation call) and Render (free-tier services
  spin down after 15 min idle, meaning a client opening an infrequently-used emailed link could
  hit a 30–60 second cold-start stall). See `Review_Tool_Implementation_Plan.md` Phase 9 for the
  concrete deploy steps and what only Stewart/Kathryn can do (account creation, real API key).

## 10. Open decisions before moving to build

1. ~~**Hosting**~~ — resolved: Vercel, see §9.
2. ~~**Google Place ID**~~ — resolved for v1 with a verified `maps?cid=` link (§7); true
   one-click composer link is a nice-to-have upgrade for later, not a blocker.
3. ~~**Exact question wording/order**~~ — reviewed and approved as-is.
4. **Repeat-platform edge case (§3a)** — hard block with no undo vs. a small undo escape hatch.
   Recommendation: hard block for v1. Needs sign-off.
5. **Branding** — once a build starts, visual design should follow LGN's brand (logo/colors);
   not addressed in this spec since it's UI-level, not structural.

## 11. Success metrics

- Sessions started vs. completed (funnel completion rate).
- Platform-button click-through rate (proxy for reviews actually posted).
- Reviews-per-month trend vs. pre-launch baseline.
- Per-agent mention frequency (useful for recognizing team members).
