# Stack Surfaces

Use this reference to avoid missing common spend and delivery surfaces when the
repo matches the target stack family.

## Cloudflare Runtime And Delivery

Check for:

- Workers entry points and route fan-out
- Durable Objects, KV, R2, Images, Analytics Engine
- cron triggers, polling, and background loops
- cache layers and invalidation
- OpenNext incremental cache and image optimization

Questions:

- What runs on every request that could be precomputed or cached?
- Is the route truly dynamic, or only treated as dynamic?
- Are multiple cache layers doing duplicate work?
- Are scheduled jobs scanning too much data too often?

## Next.js / OpenNext Rendering

Check for:

- static vs dynamic rendering
- revalidation and publish/update invalidation
- client-heavy pages that could ship less JS
- HTML duplication and hydration cost
- media and third-party scripts on public pages

Questions:

- Can this page be static or partially static?
- Is request-time rendering buying anything important?
- Are analytics, chat, maps, or embeds making the page heavier than needed?

## Supabase / Postgres / Drizzle

Check for:

- repeated reads on hot paths
- large joins or wide scans
- write amplification from cron and notification workflows
- auth and profile reads on every route

Questions:

- Which reads should be cached or denormalized?
- Which queries scale directly with traffic?
- Are background jobs forcing avoidable DB churn?

## AI And Metered APIs

Check for:

- model choice
- token size and retry behavior
- deterministic pre-filters
- quota and circuit-breaker protections
- fallback logic

Questions:

- Is an AI call necessary on this path?
- Can deterministic logic handle most cases first?
- Is the expensive model reserved for the cases that need it?

## Messaging And Notifications

Check for:

- email, SMS, WhatsApp, push, and webhook fan-out
- retries and duplication
- reminder cron cadence
- consent and feature-flag gating

Questions:

- Are users getting the same notification over multiple paid channels?
- Can a cheaper channel handle the bulk of the flow?
- Is reminder volume bounded tightly enough?

## Analytics And Replay

Check for:

- event volume
- pageview duplication
- server-side plus client-side capture overlap
- session replay scope
- high-cardinality properties

Questions:

- Is this event useful enough to justify its volume?
- Is replay enabled only where it earns its keep?
- Are analytics vendors collecting expensive low-signal data?

## Media And Storage

Check for:

- upload size limits
- normalized formats
- transformed asset generation
- retention and orphan cleanup
- PDF or media generation loops

Questions:

- Can heavy transforms happen once at upload instead of at read time?
- Are large files being stored or delivered without compression discipline?
- Is old or duplicate media accumulating?

## Payments And External Vendors

Check for:

- per-transaction API calls
- webhook retry gaps
- sync loops with external systems
- vendor calls on dashboard loads or settings screens

Questions:

- Is the integration doing unnecessary status fetches?
- Can writes be queued or batched safely?
- Are webhook-driven updates replacing polling where possible?
