# Agent Session Continuity Litmus — Product Spec

## User and job

Target users are coding-agent client authors, extension authors, reliability engineers, and developers who depend on long-running native coding-agent sessions.

The job is to determine in 5–30 minutes whether an installed coding-agent client preserves exact task intent, completed-action facts, artifact hashes, unresolved decisions, and wait-vs-continue state across its native resume and compaction boundaries.

## Product boundary

The primary surface is a local CLI that creates a disposable fixture, starts or attaches to an explicitly selected installed client, triggers a documented native boundary, and scores the post-boundary response against deterministic field oracles. Live model use must require an explicit opt-in, client sessions must be isolated, and raw captures must stay local by default.

This is not a memory layer, session database, transcript summarizer, generic agent benchmark, prompt substitute, or wrapper that merely exposes client APIs. It does not repair continuity failures. Client-specific bugs and fixes remain upstream work; the standalone value is one comparable cross-client fixture contract and evidence format.

## Version 0.1 scope

- guarded Codex app-server adapter using `thread/compact/start`;
- guarded opencode headless adapter using `session.summarize`;
- direct-resume baseline and native-manual-compaction run modes;
- exact scoring for opaque intent/action tokens, sentinel, artifact SHA-256, decision state, and next-action state;
- three fixture profiles: opaque task contract, completed-artifact plus unresolved-decision contract, and wait-for-user state contract;
- JSON and Markdown reports with client version, boundary API, raw-capture paths, and documented failures.

Automatic context-pressure compaction, compaction failure injection, Claude Code, Gemini CLI, GUI clients, and claims about model-independent behavior are outside v0.1 unless a stable public boundary can be exercised reproducibly.

## Success and kill criteria

Success requires deterministic local scoring, at least three unrelated continuity cases, two installed-client ecosystems, a same-fixture direct-resume baseline, repeated native-compaction runs, raw evidence, documented failures, and a demonstrated workflow improvement over manually reading client transcripts or session databases.

Kill or narrow the project if direct-resume runs lose the same fields as compacted runs, results mainly measure model wording rather than boundary state, native boundaries cannot be invoked without brittle TUI automation, existing client-neutral tools add equivalent installed-client coverage, or the useful evidence is only a client-specific upstream regression fixture.

## Safety and operating constraints

- Require `--allow-live` before any model-backed client call and describe quota or cost risk.
- Use a fresh disposable directory and isolated client configuration wherever the client supports it.
- Default to no network sharing, transcript upload, repository mutation, or session publication.
- Record client and model identifiers without copying credentials or unrelated user history.
- Bound time, output, and retries; surface incomplete compaction as `INCONCLUSIVE`, not `FAIL`.
