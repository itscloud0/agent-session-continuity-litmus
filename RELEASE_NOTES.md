# v0.1.0 release notes

Initial release for exact continuity testing across coding-agent native context compaction and session resume.

Included:

- opaque-task, completed-artifact/unresolved-decision, and wait-for-user profiles;
- paired no-compaction baseline and native-compaction paths with varying exact values;
- guarded Codex CLI app-server and opencode headless adapters with explicit live-call opt-in;
- exact six-field, artifact-byte, boundary-completion, and post-boundary tool-use scoring;
- local JSON, Markdown, event, message, and stderr captures;
- reproducible two-client, two-repetition, three-profile benchmark.

Known limitations:

- live validation currently covers macOS, Codex CLI 0.144.5, and opencode 1.16.2;
- automatic context-pressure and failed compaction are not tested;
- Claude Code, Gemini CLI, GUI clients, Windows, and Linux live behavior are not validated;
- results diagnose the selected client/model combination and do not prove model-independent causality or repair continuity failures.
