# Demand Evidence

## Repeated public pain

- Codex issue #8310 reports task-pointer regression and repeated completed work after auto-compaction plus resume: https://github.com/openai/codex/issues/8310
- Codex issue #9198 reports post-compaction turns missing or resume jumping back to the compaction point: https://github.com/openai/codex/issues/9198
- Codex issue #14589 reports compaction discarding tool outputs and assistant reasoning: https://github.com/openai/codex/issues/14589
- Codex issue #22335 reports failed compaction stranding tasks and resumed sessions losing task continuity: https://github.com/openai/codex/issues/22335
- Claude Code issue #24304 reports broken parent chains and resume loading only the last message despite fuller JSONL history: https://github.com/anthropics/claude-code/issues/24304
- Claude Code issue #34556 reports repeated knowledge loss across 59 compactions and a custom pre-compaction persistence workaround: https://github.com/anthropics/claude-code/issues/34556
- opencode issue #18794 distinguishes active-task from wait-for-user state and reports `/compact` continuing unrelated work: https://github.com/anomalyco/opencode/issues/18794
- VS Code issue #251250 reports Copilot losing problem context and proposed solutions after conversation summarization, then looping: https://github.com/microsoft/vscode/issues/251250

These eight reports span four independent product families and cover forgotten completed work, lost task pointers, missing history/tool facts, broken resume chains, and incorrect wait/continue state.

## Alternatives and insufficiency

- ContinuityBench evaluates interrupted-state recovery under controlled no-context and summary conditions at framework/benchmark level. It does not run the documented native resume and compaction boundaries of an installed Codex or opencode client: https://openreview.net/pdf?id=3N3BzvoLbG
- Microsoft STATE-Bench evaluates stateful enterprise workflows and memory or learning hooks, not installed coding-client session rehydration: https://github.com/microsoft/STATE-Bench
- AICTX stores repo-local operational state across tools, and agentmemory provides a cross-client memory layer. They are continuity workarounds rather than native-client conformance tests: https://aictx.org/ and https://github.com/rohitg00/agentmemory
- Client issue fixtures are the correct home for each implementation fix, but they do not provide a shared field oracle or comparable capture format across installed clients.

The standalone gap is narrow: a client-neutral, installed-client fixture contract for native boundary behavior. It is not a new memory implementation or general benchmark.

## Targeted validation on 2026-07-17 and 2026-07-18

Plain native resume feasibility on 2026-07-17:

- Codex CLI 0.144.5 returned all six requested continuity fields without tools after resume.
- opencode 1.16.2 retained intent, sentinel, completed action, exact artifact hash, and unresolved decision, but returned `WAITING` instead of the requested next action.
- Both clients created the expected 21-byte artifact with SHA-256 `666c50452736866c3c08862bc9212ab6943b3bd4a590cede9b7a3006a19342a6`.

Native manual-compaction validation on 2026-07-18 used a fresh 32-byte artifact and six exact operational fields:

- Codex CLI 0.144.5 invoked `thread/compact/start`, emitted a completed `contextCompaction` item, preserved the artifact SHA-256 `3028336f79de467d8a853abfd41f3654109c3c22787760dea9d92c77ded0bd46`, and returned 6/6 exact fields after continuation.
- opencode 1.16.2 invoked `session.summarize`, returned HTTP 200/`true`, preserved the exact sentinel, artifact hash, unresolved decision, and next action, but its compaction summary replaced the exact intent and completed-action tokens with paraphrases. The post-boundary response scored 4/6 exact fields.
- Both clients created the exact artifact bytes. The opencode capture shows the two token changes inside the native compaction summary itself, rather than only in the later response.

Raw local evidence is stored under `.automation/tmp/flagship-session-continuity-compaction-2026-07-18/`. This is one bounded feasibility run, not a reproducibility or adoption claim.

## Value gate

`PASS` for `SPEC`.

- Target user and job: concrete.
- External pain: `PASS` with eight reports from four independent product families.
- Alternative insufficiency: `PASS` for the narrow installed-client native-boundary matrix; adjacent work covers framework recovery or continuity storage, not this comparative contract.
- First 5–30 minute outcome: demonstrated. A user can trigger the native boundary and receive a field-level report identifying exact state retention or drift.
- Upstream insufficiency: `PASS` for shared fixtures and comparable evidence; every client-specific defect and fix still belongs upstream.

Build and publication remain gated on same-fixture baselines, repeated results, three fixture profiles, guarded adapters, safety, CI, discoverability, and documented limitations.
