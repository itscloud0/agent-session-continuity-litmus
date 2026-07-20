# Reproducible benchmark

## Contract

Each client receives three continuity profiles with varying exact values. Every repetition pairs a no-compaction baseline with the client's documented native manual-compaction API. A path passes only when the boundary completes, all six fields match exactly, the artifact bytes match, and phase two uses no tools.

## 2026-07-19 and 2026-07-20 matrix

| Client | Profile | Baseline | Native compaction | Finding |
| --- | --- | --- | --- | --- |
| Codex CLI 0.144.5 | opaque task | 6/6 twice | 6/6 twice | no exact drift observed |
| Codex CLI 0.144.5 | completed artifact / unresolved decision | 6/6 twice | 6/6 twice | no exact drift observed |
| Codex CLI 0.144.5 | wait for user | 6/6 twice | 6/6 twice | no exact drift observed |
| opencode 1.16.2 | opaque task | 6/6 twice | 6/6, then 5/6 | one exact intent token drifted only after compaction |
| opencode 1.16.2 | completed artifact / unresolved decision | 6/6 twice | 6/6 twice | no exact drift observed |
| opencode 1.16.2 | wait for user | 6/6 twice | 6/6 twice | no exact drift observed |

Across 24 controlled paths, all 12 no-compaction baselines passed and 11/12 native-compaction paths passed. Exact fields scored 143/144. All artifacts matched and no phase-two response used tools. The single controlled failure is documented evidence of intermittent exact-state drift, not a claim that opencode always loses state or that Codex cannot fail.

## Workflow improvement

The CLI replaces manual session-database inspection, transcript comparison, artifact hashing, and boundary-event correlation with paired exact reports and raw local captures. It distinguishes ordinary response drift from boundary-attributable drift by using the same values in a client-specific baseline. No measured time-saving or adoption claim is made.

## Known failures and limits

- One opencode opaque-task compacted run replaced the exact intent token with a paraphrase while its paired baseline preserved it.
- A separate 2026-07-18 feasibility capture changed two exact opencode fields after compaction; that unpaired run is supporting evidence, not part of the controlled totals.
- Automatic context-pressure compaction, failed compaction, Windows/Linux hosts, other client versions, GUI clients, and model-independent causality are unvalidated.
