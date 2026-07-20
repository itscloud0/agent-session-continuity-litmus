# Security

Agent Session Continuity Litmus creates disposable workspaces and invokes configured Codex or opencode clients only with explicit `--allow-live` opt-in.

- Live runs may consume provider quota and send fixture prompts to the provider configured by the selected client.
- Do not point output at an existing repository or place secrets in a fixture workspace.
- Raw captures may include local paths, fixture prompts, session identifiers, and model output. Review them before sharing.
- Codex uses fresh ephemeral app-server threads. opencode uses fresh sessions with plugins disabled by `--pure`; its normal local configuration still supplies authentication.
- The tool sends no telemetry, uploads no captures, and does not read unrelated session history. Provider data handling remains controlled by the invoked client.

Report security issues privately through the repository owner's GitHub security contact after publication. Do not include credentials or private repository content.
