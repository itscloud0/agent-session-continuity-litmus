# agent-session-continuity-litmus

`agent-session-continuity-litmus` tests whether an installed coding-agent client preserves exact task state across native context compaction. It is for client authors and reliability engineers diagnosing session-resume drift, lost completed actions, forgotten decisions, and incorrect wait-vs-continue state.

The guarded CLI runs the same opaque-field fixture through a no-compaction baseline and the client's documented native compaction API. It scores exact retained values, verifies artifact bytes, records boundary completion, and keeps raw evidence local.

## Quickstart

Python 3.10+ and an authenticated supported client are required for live runs. PyPI publication is not available yet, but the public `v0.1.0` tag can be installed without cloning:

```console
python3 -m pip install "git+https://github.com/itscloud0/agent-session-continuity-litmus@v0.1.0"
# Or install an isolated command with pipx:
pipx install "git+https://github.com/itscloud0/agent-session-continuity-litmus@v0.1.0"
# Or use uv's managed tool environment:
uv tool install --from "git+https://github.com/itscloud0/agent-session-continuity-litmus@v0.1.0" agent-session-continuity-litmus
```

Run the offline fixture smoke first; it does not contact a coding-agent client or consume model quota:

```console
agent-session-continuity-litmus fixture --profile opaque-task-contract
```

For a one-off offline smoke without a checkout or persistent install, use `uvx`:

```console
uvx --from "git+https://github.com/itscloud0/agent-session-continuity-litmus@v0.1.0" \
  agent-session-continuity-litmus fixture --profile opaque-task-contract
```

Live runs may consume model quota and require explicit opt-in. Before a live run, install and authenticate the selected client, then confirm its executable is on `PATH` (for example, `codex --version` or `opencode --version`).

```console
agent-session-continuity-litmus run \
  --adapter codex-cli \
  --profile opaque-task-contract \
  --profile completed-artifact-unresolved-decision \
  --profile wait-for-user-state \
  --repetitions 2 \
  --output validation/live/codex \
  --allow-live
```

Use `--adapter opencode-cli` for opencode. Every repetition uses fresh opaque values and separate sessions for the baseline and native-compaction path. Reports and client captures stay under the selected output directory.

## Coding-agent continuity cases

The three profiles cover an opaque task contract, a completed artifact with an unresolved renderer decision, and a session blocked on explicit user input. Each retains exact task intent, a sentinel, a completed-action fact, the artifact SHA-256, decision state, and the permitted next action. Phase two forbids tools so the answer must come from retained native session state.

The primary result is within-client: did native compaction lose fields that the same client's no-compaction baseline preserved? Cross-client differences are descriptive and do not prove model-independent causality.

## Supported native boundaries

- Codex CLI app-server: `thread/compact/start`
- opencode headless server: `session.summarize`

Validated versions are recorded in `VALIDATION_RESULTS.md`. Other versions may return `INCONCLUSIVE` when their protocol differs.

## Safety

- Live model calls require `--allow-live`.
- Workspaces and native sessions are disposable.
- Codex uses ephemeral app-server threads; opencode uses fresh headless sessions with plugins disabled.
- Raw captures remain local and may contain fixture prompts and model output. Review before sharing.
- The tool does not upload transcripts, repair session state, or mutate an existing repository.

## Limitations

This release tests documented manual compaction, not automatic context-pressure compaction or failed compaction. It does not cover Claude Code, Gemini CLI, GUI clients, or model-independent behavior. Exact-token drift may reflect summary behavior, model behavior, or their interaction; the no-compaction baseline controls ordinary paraphrasing but does not isolate every cause. Live validation currently covers macOS with Codex CLI 0.144.5 and opencode 1.16.2.

## Comparison

ContinuityBench and STATE-Bench evaluate broader interrupted or stateful agent workflows. AICTX and agentmemory preserve continuity outside native clients. This project is narrower: comparable local evidence from installed coding-agent session-resume and native context-compaction boundaries.

See `BENCHMARK.md` for the reproducible 24-path matrix, `SECURITY.md` before live runs, and `DISTRIBUTION.md` for accurate search and release surfaces.
