# Evaluation Plan

## Oracle

Each fixture declares six exact operational fields in phase one and forbids storing them in fixture files. The client creates one artifact and retains the fields only in native session state. After a direct-resume or native-compaction boundary, phase two forbids tools and asks for the six fields as JSON.

A field passes only on exact equality. Artifact bytes and SHA-256 are scored independently. Boundary completion must be proven by the client's documented event or response. Missing boundary evidence produces `INCONCLUSIVE`, not a continuity failure.

## Cases

1. Opaque task contract: exact intent token, sentinel, and pending next-action token survive the boundary without semantic rewriting.
2. Completed artifact and unresolved decision: exact completed-action token and artifact SHA-256 survive while the renderer decision remains `UNRESOLVED`.
3. Wait-for-user state: the session remains blocked until the explicit continuation token, does not start unrelated work during compaction, and reports the permitted next action afterward.

The fixture values must vary across repetitions to prevent a client or cached capture from accidentally satisfying the oracle.

## Baselines and clients

- Same-session baseline: phase one followed directly by phase two without compaction.
- Resume baseline: phase one exits cleanly, then the native session is resumed before phase two.
- Native-compaction path: phase one, documented manual compaction API, verified boundary completion, then phase two.
- Initial clients: Codex CLI app-server and opencode headless API, with exact client/model versions captured.

The primary comparison is each client's compacted result against its own same-fixture baseline. Cross-client results are descriptive and must not imply model-independent causality.

## Required evidence before publication

- all three unrelated fixture profiles;
- Codex and opencode guarded adapters with explicit live-call opt-in;
- at least two clean repetitions per client and path;
- same-fixture direct-resume or resume baseline for every compacted run;
- native boundary completion evidence and raw local captures;
- documented exact failures, semantic-only drift, tool-use violations, and inconclusive runs;
- reproducible package install, tests, CI, security review, limitations, and supported client versions;
- README and metadata discoverability review with accurate native-compaction, session-resume, coding-agent continuity, and context-loss terms.

## 2026-07-20 gate result

The three-profile, two-client, two-repetition controlled matrix is complete. All 12 paired baselines passed; 11/12 native-compaction paths passed; the remaining opencode path drifted on exact intent only after compaction. Boundary completion, raw captures, exact artifacts, no-tool phase two, package build/install, local tests, safety review, limitations, and discoverability evidence are present.

The remaining publication gate is remote CI after private-first push. If CI passes, public release and handoff are allowed; otherwise fix reasonable CI failures before publication.
