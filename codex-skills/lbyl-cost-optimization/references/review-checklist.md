# Review Checklist

Run this checklist before finalizing any report from the cost-optimization
skill.

## Before

- [ ] The scope is explicit: audit mode or design review mode
- [ ] The relevant stack surfaces have been identified
- [ ] Local repo evidence was read before making recommendations
- [ ] Any missing pricing or limit facts are clearly marked for external research

## During

### Cost Model

- [ ] Direct vendor spend is named where relevant
- [ ] Infrastructure pressure is covered separately from vendor billing
- [ ] Scale drivers are identified for each major surface
- [ ] Existing controls are noted: caches, quotas, rate limits, dedup, flags

### Loading And Caching

- [ ] Static vs dynamic rendering was evaluated when relevant
- [ ] Cache placement was discussed explicitly
- [ ] Invalidation constraints were named
- [ ] HTML, JS, media, and third-party payload costs were considered
- [ ] Polling alternatives were considered where polling exists

### Third-Party Usage

- [ ] AI/model usage was examined for necessity and guardrails
- [ ] Search/maps enrichment was examined for fallback-only usage and cacheability
- [ ] Messaging/retry/fan-out paths were examined for duplication
- [ ] Analytics and replay scope were checked for low-signal volume

## After

- [ ] Recommendations are concrete, not generic
- [ ] Tradeoffs are explicit, not implied
- [ ] The report includes a decision
- [ ] The action plan is prioritized and usable by planning workflows
- [ ] The report distinguishes sourced facts from inference

## Red Flags

- [ ] Recommending caching without naming invalidation
- [ ] Treating all dynamic routes as bad by default
- [ ] Treating all AI calls as waste without checking product need
- [ ] Suggesting provider swaps with no migration or risk discussion
- [ ] Giving performance advice with no cost model
- [ ] Giving cost advice with no delivery or UX discussion
