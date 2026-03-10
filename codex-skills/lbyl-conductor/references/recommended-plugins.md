# Recommended Companion Tooling

Codex does not use Claude plugin manifests. During onboarding, suggest the
smallest set of companion skills or tools that materially improves this
project's workflow.

## Universal

| Tooling | Why suggest it |
|---|---|
| `context7` or an equivalent docs MCP | Pull current library docs without leaving the coding flow |
| `gh-address-comments` | Useful when the repo workflow revolves around PR review loops |
| `gh-fix-ci` | Useful when users regularly debug failing GitHub Actions checks |
| `lbyl-agent-setup` | Tightens project-local `AGENTS.md` guidance for Codex sessions |

## Task-specific

| Tooling | When to suggest |
|---|---|
| `lbyl-frontend-design` | The repo includes meaningful web UI work and the user wants distinctive, production-grade frontend output |
| `immersive-frontend` | The user needs cinematic or motion-heavy web experiences |
| `react-native-mobile` | The repo targets React Native or Expo apps |
| `security-best-practices` | The user explicitly asks for security review or secure-by-default guidance |
| `security-threat-model` | The user wants repository-grounded threat modeling |
| `lbyl-skill-creator` | The user wants to create, port, evaluate, or improve skills |

## Guidance

- Prefer skills already available in the current session over inventing a new workflow.
- Suggest new tooling only when it meaningfully reduces repeated manual work.
- If Orbit is available, prefer `orbit_await_review` for plan review instead of ad hoc artifact flows.
