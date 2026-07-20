# Build Results

Lifecycle step: `BUILD`.

Implemented one primary CLI surface with:

- three varying continuity profiles;
- exact six-field and artifact-byte scoring;
- same-fixture no-compaction baseline and native-compaction paths;
- guarded Codex app-server and opencode headless adapters;
- explicit `--allow-live` opt-in;
- local JSON, Markdown, event, message, and stderr captures;
- boundary-attributable drift comparison.

The completed-artifact/unresolved-decision and wait-for-user profiles were added on 2026-07-20. The CLI accepts repeatable `--profile` arguments and stores each profile's paired runs separately.

## Verification

- Python 3.12 unit tests: 10 passed.
- Python 3.12 `compileall`: passed.
- Offline fixture CLI smoke: passed.
- Targeted secret-pattern scan outside ignored live captures: no matches.
- Eight live paths completed: baseline and native compaction, twice each, for Codex CLI 0.144.5 and opencode 1.16.2.
- Python 3.12 compileall passed with its cache redirected to a writable temporary directory.
- Sixteen additional live paths completed for the two new profiles; all scored 6/6 with exact artifact bytes and no post-boundary tools.
- Wheel and source distribution built successfully; a clean Python 3.12 virtual environment installed the wheel and passed the installed CLI smoke.
