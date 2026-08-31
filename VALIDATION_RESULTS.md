# Validation Results

## 2026-08-31 workflow reproducibility hardening

The CI workflow now pins checkout v4 and setup-python v5 to the exact commits
resolved from their reviewed tags. A workflow regression test requires every
external action call site to remain a full 40-character commit pin.

Local verification passed the unit suite, compileall, workflow pin test, and
`git diff --check`. Public Actions run `33423682513` passed for commit
`045702d7a990643055c9a5074cccc24dc26a8e61`, covering the supported
Ubuntu/macOS/Windows Python matrix and immutable public-release install smoke.

## 2026-07-19 guarded live matrix

The opaque-task-contract profile ran twice per client. Every repetition used fresh field values and separate baseline and native-compaction sessions.

| Client | No-compaction baseline | Native compaction | Boundary-specific result |
| --- | --- | --- | --- |
| Codex CLI 0.144.5 | 6/6 exact fields in both runs | 6/6 exact fields in both runs | no exact drift observed |
| opencode 1.16.2 | 6/6 exact fields in both runs | 6/6, then 5/6 | run 2 replaced exact `intent` with `native-session continuity fixture phase one` |

All eight paths completed their expected protocol step, produced exact artifact bytes, and used no tools after the phase-two boundary. Codex compaction was proven by a completed `contextCompaction` item from `thread/compact/start`. opencode compaction returned HTTP 200 and `true` from `session.summarize`.

The opencode run-2 failure is attributable to compaction for this sample because its same-value baseline preserved 6/6 fields. The failure occurred in one of two compacted repetitions, so boundary-specific drift is demonstrated but failure repeatability remains `UNKNOWN`.

Raw local reports are under ignored `validation/live/codex-2026-07-19-v2/` and `validation/live/opencode-2026-07-19/` directories. The earlier `codex-2026-07-19/` capture exposed and led to a scorer fix: app-server `userMessage` and `contextCompaction` items are protocol events, not post-boundary tool use.

Exact next validation: add the completed-artifact/unresolved-decision and wait-for-user profiles, then repeat the within-client baseline comparison. Do not publish until all three unrelated profiles, CI, packaging, safety, and discoverability gates pass.

## 2026-07-20 expanded profile matrix

The completed-artifact/unresolved-decision and wait-for-user-state profiles each ran twice per client with fresh exact values and paired no-compaction/native-compaction sessions.

| Client | Profile | No-compaction baseline | Native compaction | Boundary-specific result |
| --- | --- | --- | --- | --- |
| Codex CLI 0.144.5 | completed artifact / unresolved decision | 6/6, 6/6 | 6/6, 6/6 | no exact drift observed |
| Codex CLI 0.144.5 | wait for user | 6/6, 6/6 | 6/6, 6/6 | no exact drift observed |
| opencode 1.16.2 | completed artifact / unresolved decision | 6/6, 6/6 | 6/6, 6/6 | no exact drift observed |
| opencode 1.16.2 | wait for user | 6/6, 6/6 | 6/6, 6/6 | no exact drift observed |

All 16 new paths completed their protocol boundary, preserved exact artifact bytes, returned all six fields exactly, and used no tools after phase two. Together with the 2026-07-19 opaque profile, the controlled benchmark contains 24 paths: all 12 baselines passed, 11/12 compacted paths passed, and one opencode compacted path showed exact intent drift against its passing baseline.

Raw reports remain local under ignored `validation/live/codex-2026-07-20/` and `validation/live/opencode-2026-07-20/` directories.
