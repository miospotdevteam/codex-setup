---
name: lbyl-cost-optimization
description: "Review cost, loading, caching, rendering, and provider tradeoffs for applications built on stacks like Cloudflare Workers, OpenNext/Next.js, Supabase/Postgres, Expo, Anthropic, PostHog, and common vendors such as Stripe, Twilio, Resend, Maps APIs, and object storage. Use when the user explicitly asks for cost optimization, or when they ask about tradeoffs involving spend, cacheability, loading strategy, rendering mode, media delivery, polling, analytics, or third-party usage. Supports both existing-stack audits and pre-implementation design review. Do NOT use for generic bug fixing, routine code review, or performance work with no cost or tradeoff goal."
---

# Cost Optimization

Use this skill to make cost-aware engineering decisions without reducing the
problem to "cut the bill at any cost." The job is to reason about:

- direct vendor spend
- runtime and infrastructure pressure
- loading and delivery efficiency
- caching and invalidation strategy
- rendering mode and data-fetch shape
- marginal cost per user action

**Announce at start:** "I'm using the cost-optimization skill to review cost,
loading, caching, and provider tradeoffs."

This skill is stack-specialized but repo-agnostic. It should adapt to codebases
that use some or all of this family of tools:

- Cloudflare Workers, KV, Durable Objects, R2, Images, Analytics Engine
- Next.js / OpenNext / edge rendering
- Supabase / Postgres / Drizzle
- Expo / React Native
- Anthropic and other metered AI APIs
- PostHog and other event/session analytics products
- Stripe, Twilio, Resend, Maps APIs, and similar usage-priced services

If only part of the stack is present, use the relevant parts and ignore the
rest.

For quick stack heuristics and review prompts, read:

- `references/stack-surfaces.md`
- `references/review-checklist.md`

## When To Use It

Use this skill when the user:

- explicitly asks for cost optimization
- asks whether a feature, page, route, HTML delivery, or architecture choice is
  worth the tradeoff
- asks about caching, loading, rendering, or provider tradeoffs
- wants a review of ongoing spend drivers in an existing codebase
- wants concrete recommendations to reduce marginal cost or improve delivery
  efficiency

## Do Not Use It When

- the task is a normal bug fix with no cost or tradeoff question
- the task is generic performance debugging with no spend angle
- the user only wants a code explanation
- the task is a routine code review unrelated to cost, delivery, or provider
  choice

## Modes

Decide which mode applies before doing deeper analysis.

### 1. Audit Mode

Use when the goal is to understand current cost drivers in an existing codebase.

Focus on:

- where money is likely being spent
- which paths scale poorly with usage
- what is already cached, rate-limited, or guarded
- where instrumentation is missing
- which changes are likely to produce the best savings with acceptable risk

### 2. Design Review Mode

Use when the goal is to assess a proposed change before implementation.

Focus on:

- cheaper architecture choices
- static vs dynamic rendering
- cache placement and invalidation
- client payload and hydration impact
- vendor call frequency
- whether the feature creates a bad unit-economics profile

## Workflow

### Phase 1: Detect Stack And Scope

Inspect the repo locally before making recommendations.

Read the minimum relevant evidence:

- root `AGENTS.md`, `README.md`, and package manifests
- deployment and infra configs such as `wrangler`, `open-next`, `eas`, env
  examples, worker bindings, and scheduler configs
- route handlers, jobs, media code, analytics setup, and provider integrations
- any existing caching, throttling, quota, fallback, or feature-flag logic

Use `references/stack-surfaces.md` to avoid missing common cost surfaces in this
stack family.

Build a scoped list of cost surfaces such as:

- runtime and rendering
- database and storage
- media delivery
- AI and search
- messaging and notifications
- analytics and session replay
- polling, cron, and background jobs
- payments and external vendor APIs

If the user is asking about one feature, stay tightly scoped to that feature and
its supporting infrastructure.

### Phase 2: Build A Cost Surface Inventory

Create a concrete inventory grounded in repo evidence. For each meaningful
surface, capture:

- `Surface`
- `Where it appears`
- `Cost model`
  Example: per request, per token, per event, per GB, per seat, baseline infra
- `Scale driver`
  Example: page views, searches, chat sessions, uploads, reminders, sync jobs
- `Existing controls`
  Example: cache TTL, quotas, rate limits, batching, dedup, feature flags
- `Likely risk`
  Example: low, medium, high

Do not guess from stack stereotypes if the repo evidence says otherwise.

Use `references/review-checklist.md` as a mandatory pass before finalizing the
inventory and recommendations.

### Phase 3: Analyze Loading, Rendering, And Caching

This is mandatory for any web page, route, HTML delivery choice, or data-heavy
feature.

Check:

- whether the page/route can be static, partially static, ISR-like, or must be
  fully dynamic
- whether the current design causes repeated work at request time
- HTML payload size and duplication
- client-side hydration cost
- image/media strategy
- caching layer placement:
  browser, CDN, framework cache, KV/R2/object cache, DB query cache
- invalidation strategy and TTL discipline
- polling vs push/webhook/event-driven alternatives

When the user says "should we add an HTML/page/route like this?", explicitly
evaluate:

- static HTML vs server-rendered page vs client-heavy app shell
- whether the page should be cacheable by default
- whether assets can be precomputed or compressed
- whether third-party scripts or analytics should be deferred, sampled, or
  excluded entirely

If the answer is "it depends," name the deciding inputs explicitly:

- expected traffic
- update frequency
- invalidation needs
- personalization/auth requirements
- asset size and media mix

### Phase 4: Evaluate Third-Party And Infrastructure Spend

Reason about direct spend and operational pressure together.

#### AI And Metered APIs

Check:

- model choice
- prompt/token volume
- timeout and retry policy
- quota and circuit-breaker protections
- fallback behavior
- whether an AI call is actually necessary
- whether deterministic logic should replace or pre-filter the call

#### Search, Maps, And Data Enrichment

Check:

- cacheability
- deduplication
- batching
- whether external calls only happen on low-confidence or low-result paths

#### Messaging, Notifications, And Background Fan-Out

Check:

- whether high-frequency notifications are gated by consent and feature flags
- whether retries, cron jobs, and reminder windows amplify spend
- whether there is needless duplication across email, SMS, WhatsApp, and push

#### Analytics And Replay

Check:

- whether pageview/event capture volume is excessive
- whether session replay is enabled too broadly
- whether high-cardinality event design is creating unnecessary volume
- whether server-side analytics calls are additive to client-side tracking with
  little value

#### Storage, Media, And Delivery

Check:

- upload limits and format normalization
- image/video/PDF generation frequency
- storage retention and orphaned object risk
- cache hit opportunities
- whether transformed assets can be pre-generated

#### Runtime, DB, And Scheduled Work

Check:

- hot paths that force expensive compute on every request
- repeated DB reads that should be cached or reshaped
- cron jobs with wide scans or fan-out loops
- edge/runtime choices that are more expensive than necessary

### Phase 5: External Research When Needed

Use local repo evidence first. Research externally only when the answer depends
on information the repo cannot provide, such as:

- current pricing
- current service limits
- current platform behavior
- recently changed vendor recommendations

When researching:

- prefer official pricing pages and official documentation
- state the date of the information you relied on
- separate sourced facts from your inference

Do not present stale pricing or limits as if they were stable facts.

### Phase 6: Recommend Concrete Implementation Patterns

Do not stop at "this is expensive." Recommend what to build instead.

Good recommendations are concrete:

- move route X from dynamic rendering to cached/static generation
- add a 7-day cache with explicit invalidation on publish/update
- replace always-on AI interpretation with deterministic pre-filter + fallback
- sample or narrow session replay scope
- collapse duplicate provider calls behind a shared cache
- replace polling with webhook or event-driven invalidation
- precompute media derivatives at upload time

When relevant, include:

- expected impact direction
- implementation complexity
- user experience risk
- observability needed to prove the change helped

## Output Contract

Default to a thorough Markdown report with these sections:

```markdown
# Cost Optimization Review

## Summary

## Context And Scope

## Detected Stack And Cost Surfaces

## Loading, Rendering, And Caching Analysis

## Third-Party And Infrastructure Spend Risks

## Tradeoffs

## Recommendations

## Implementation Patterns

## Prioritized Action Plan

## Open Questions Or Assumptions

## Decision
```

`Decision` should be explicit:

- `Proceed`
- `Proceed with changes`
- `Do not proceed yet`

`Prioritized Action Plan` must be usable by planning/execution workflows. Each
action should name the problem, the recommended change, and why it is worth
doing now.

## Workflow Integration

If the review happens before implementation:

- shape the output so it can feed directly into planning
- call out the recommended architecture and cache strategy clearly

If the review happens during implementation:

- focus on the smallest high-leverage changes first
- distinguish immediate fixes from later optimizations

If the user asks to implement the recommendations, hand off to the normal
coding workflow after the review rather than mixing architecture review and
implementation reasoning into one opaque step.

## Boundaries

Do not:

- optimize purely for lowest cost while ignoring product quality or reliability
- assume every expensive surface should be removed rather than reshaped
- invent pricing or platform limits
- recommend caching without naming invalidation constraints
- recommend a cheaper provider swap without discussing migration and risk
- turn a tradeoff review into generic performance advice with no cost model

## Acceptance Criteria

- [ ] The report is grounded in repo evidence, not generic stack assumptions
- [ ] Loading, rendering, and caching are analyzed when relevant
- [ ] Direct vendor spend and infrastructure pressure are both covered
- [ ] Recommendations include concrete implementation patterns
- [ ] The output includes a decision and a prioritized action plan
