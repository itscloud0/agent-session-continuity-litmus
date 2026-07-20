from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


FIELD_NAMES = (
    "intent",
    "sentinel",
    "completed_action",
    "artifact_sha256",
    "decision_status",
    "next_action",
)

PROFILE_NAMES = (
    "opaque-task-contract",
    "completed-artifact-unresolved-decision",
    "wait-for-user-state",
)


@dataclass(frozen=True)
class Fixture:
    profile: str
    fixture_id: str
    artifact_bytes: bytes
    expected: dict[str, str]

    @property
    def phase_one(self) -> str:
        values = self.expected
        artifact_text = self.artifact_bytes.decode("utf-8").removesuffix("\n")
        profile_instructions = {
            "opaque-task-contract": """Treat the opaque values as identifiers, not prose. Do not expand, paraphrase, or infer them.""",
            "completed-artifact-unresolved-decision": """The artifact creation is complete. A renderer choice is deliberately unresolved; do not choose one or perform follow-up work.""",
            "wait-for-user-state": """The task is blocked on user input after the checkpoint is written. Do not continue, select an option, or begin unrelated work before CONTINUE.""",
        }[self.profile]
        return f"""This is a harmless native-session continuity fixture for profile `{self.profile}`. Perform only phase one.

{profile_instructions}

Retain these exact operational fields in the conversation only; do not write them into files:
- intent: {values['intent']}
- sentinel: {values['sentinel']}
- completed_action after the file is written: {values['completed_action']}
- decision_status: {values['decision_status']}
- next_action: {values['next_action']}

Create `phase-one.txt` with the exact UTF-8 bytes `{artifact_text}` followed by one newline. Determine its SHA-256 after writing it and retain that as artifact_sha256, but do not store the hash or retained fields in any file. Do not resolve the decision and do not take phase two. Stop and reply only with WAITING.
"""

    @property
    def phase_two(self) -> str:
        return (
            "CONTINUE. Do not read files and do not run tools. Return only one compact JSON object "
            "with exactly these keys: intent, sentinel, completed_action, artifact_sha256, "
            "decision_status, next_action. Use only operational state retained in this native "
            "session. Do not resolve the decision."
        )


@dataclass(frozen=True)
class FieldResult:
    name: str
    expected: str
    observed: Any
    exact: bool


@dataclass(frozen=True)
class RunResult:
    adapter: str
    client_version: str
    fixture_id: str
    path: str
    boundary: dict[str, Any]
    response_text: str
    parsed: dict[str, Any] | None
    fields: list[FieldResult]
    tool_use_after_boundary: bool
    artifact_exists: bool
    artifact_bytes_match: bool
    artifact_sha256: str | None
    expected_artifact_sha256: str
    status: str

    @property
    def passed_fields(self) -> int:
        return sum(field.exact for field in self.fields)


def make_fixture(repetition: int, profile: str = "opaque-task-contract") -> Fixture:
    if repetition < 1:
        raise ValueError("repetition must be positive")
    if profile not in PROFILE_NAMES:
        raise ValueError(f"unsupported profile: {profile}")
    token = f"R{repetition:02d}"
    profile_values = {
        "opaque-task-contract": {
            "artifact": f"continuity-opaque-contract-{token.lower()}\n",
            "intent": f"VERIFY_OPAQUE_TASK_CONTRACT_{token}",
            "sentinel": f"NOVA-{7300 + repetition}",
            "completed_action": f"CREATED_OPAQUE_ARTIFACT_{token}",
            "decision_status": "UNRESOLVED",
            "next_action": f"REPORT_RETAINED_STATE_{token}",
        },
        "completed-artifact-unresolved-decision": {
            "artifact": f"renderer-candidate-record-{token.lower()}\n",
            "intent": f"PRESERVE_COMPLETED_ARTIFACT_FACT_{token}",
            "sentinel": f"EMBER-{8100 + repetition}",
            "completed_action": f"WROTE_RENDERER_CANDIDATE_RECORD_{token}",
            "decision_status": f"RENDERER_CHOICE_UNRESOLVED_{token}",
            "next_action": f"AWAIT_RENDERER_DECISION_{token}",
        },
        "wait-for-user-state": {
            "artifact": f"user-input-checkpoint-{token.lower()}\n",
            "intent": f"HOLD_FOR_EXPLICIT_USER_INPUT_{token}",
            "sentinel": f"QUARTZ-{9200 + repetition}",
            "completed_action": f"CREATED_USER_INPUT_CHECKPOINT_{token}",
            "decision_status": f"USER_INPUT_REQUIRED_{token}",
            "next_action": f"REPORT_WAIT_STATE_ONLY_{token}",
        },
    }[profile]
    artifact = profile_values["artifact"].encode("utf-8")
    digest = hashlib.sha256(artifact).hexdigest()
    return Fixture(
        profile=profile,
        fixture_id=f"{profile}-{token.lower()}",
        artifact_bytes=artifact,
        expected={
            "intent": profile_values["intent"],
            "sentinel": profile_values["sentinel"],
            "completed_action": profile_values["completed_action"],
            "artifact_sha256": digest,
            "decision_status": profile_values["decision_status"],
            "next_action": profile_values["next_action"],
        },
    )


def create_workspace(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=False)


def extract_json(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    if stripped.startswith("```") and "\n" in stripped:
        stripped = stripped.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    candidates = [stripped]
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start >= 0 and end > start:
        candidates.append(stripped[start : end + 1])
    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None


def score_run(
    *,
    adapter: str,
    client_version: str,
    fixture: Fixture,
    path: str,
    boundary: dict[str, Any],
    response_text: str,
    workspace: Path,
    tool_use_after_boundary: bool,
) -> RunResult:
    parsed = extract_json(response_text)
    fields = [
        FieldResult(
            name=name,
            expected=fixture.expected[name],
            observed=None if parsed is None else parsed.get(name),
            exact=parsed is not None and parsed.get(name) == fixture.expected[name],
        )
        for name in FIELD_NAMES
    ]
    artifact = workspace / "phase-one.txt"
    actual_bytes = artifact.read_bytes() if artifact.is_file() else None
    actual_hash = hashlib.sha256(actual_bytes).hexdigest() if actual_bytes is not None else None
    boundary_complete = bool(boundary.get("complete"))
    if not boundary_complete:
        status = "INCONCLUSIVE"
    elif all(field.exact for field in fields) and actual_bytes == fixture.artifact_bytes and not tool_use_after_boundary:
        status = "PASS"
    else:
        status = "FAIL"
    return RunResult(
        adapter=adapter,
        client_version=client_version,
        fixture_id=fixture.fixture_id,
        path=path,
        boundary=boundary,
        response_text=response_text,
        parsed=parsed,
        fields=fields,
        tool_use_after_boundary=tool_use_after_boundary,
        artifact_exists=actual_bytes is not None,
        artifact_bytes_match=actual_bytes == fixture.artifact_bytes,
        artifact_sha256=actual_hash,
        expected_artifact_sha256=hashlib.sha256(fixture.artifact_bytes).hexdigest(),
        status=status,
    )


def write_result(output: Path, result: RunResult) -> None:
    output.mkdir(parents=True, exist_ok=True)
    payload = asdict(result)
    payload["passed_fields"] = result.passed_fields
    payload["total_fields"] = len(result.fields)
    (output / "report.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    rows = [
        "# Session continuity result",
        "",
        f"Adapter: `{result.adapter}`  ",
        f"Client: `{result.client_version}`  ",
        f"Path: `{result.path}`  ",
        f"Boundary API: `{result.boundary.get('api', 'none')}`  ",
        f"Status: `{result.status}`",
        "",
        "| Field | Exact | Expected | Observed |",
        "| --- | --- | --- | --- |",
    ]
    for field in result.fields:
        observed = json.dumps(field.observed, ensure_ascii=False)
        rows.append(f"| `{field.name}` | {'PASS' if field.exact else 'FAIL'} | `{field.expected}` | `{observed}` |")
    rows.extend(
        [
            "",
            f"Exact fields: {result.passed_fields}/{len(result.fields)}.",
            f"Artifact bytes: {'PASS' if result.artifact_bytes_match else 'FAIL'}.",
            f"Post-boundary tool use: {'yes' if result.tool_use_after_boundary else 'no'}.",
            "",
        ]
    )
    (output / "report.md").write_text("\n".join(rows), encoding="utf-8")


def compare_paths(baseline: RunResult, compact: RunResult) -> dict[str, Any]:
    if baseline.fixture_id != compact.fixture_id or baseline.adapter != compact.adapter:
        raise ValueError("baseline and compact results must use the same adapter and fixture")
    baseline_fields = {field.name: field for field in baseline.fields}
    compact_fields = {field.name: field for field in compact.fields}
    attributable = [
        name
        for name in FIELD_NAMES
        if baseline_fields[name].exact and not compact_fields[name].exact
    ]
    shared_failures = [
        name
        for name in FIELD_NAMES
        if not baseline_fields[name].exact and not compact_fields[name].exact
    ]
    return {
        "adapter": baseline.adapter,
        "fixture_id": baseline.fixture_id,
        "baseline_status": baseline.status,
        "compact_status": compact.status,
        "baseline_exact_fields": baseline.passed_fields,
        "compact_exact_fields": compact.passed_fields,
        "boundary_attributable_exact_drift": attributable,
        "shared_exact_failures": shared_failures,
    }
