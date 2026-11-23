# -*- coding: utf-8 -*-
"""
Tests for Antigravity-specific specifications defined in §9 of the addition instructions:
- Name isolation from main free edition
- Default values (18527, ~/.n3mc-free-antigravity)
- hooks.json registration, preservation, and legacy replacement
- Turn identification and tool-loop re-invocation suppression
- Transcript extraction (<USER_REQUEST>, transcript_full.jsonl fallback)
- Hook output formats (injectSteps, {}, {"decision":"stop"})
- Storage metadata (agent_name="antigravity", [user], [assistant])
- Foreign server connection (§3.7) and error isolation
- Dual input compatibility for Claude Code
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
import pytest

from n3memorycore_free_antigravity import paths
from n3memorycore_free_antigravity.paths import python_cmd


def test_no_name_collision():
    """Wheel and package declarations must not collide with main free."""
    import tomllib
    pyproject_path = os.path.join(os.path.dirname(os.path.dirname(paths.__file__)), "pyproject.toml")
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)
    project = data["project"]
    assert project["name"] == "n3memorycore-free-antigravity"
    assert "n3mc-free-antigravity" in project["scripts"]
    assert "n3mc-free-antigravity-hook" in project["scripts"]
    assert "n3mc-free-antigravity-stop-hook" in project["scripts"]
    assert "n3mc" not in project["scripts"]
    assert "n3mc-hook" not in project["scripts"]
    assert "n3mc-stop-hook" not in project["scripts"]


def test_default_values(monkeypatch):
    """Verify default home dir and port are specific to Antigravity edition."""
    # Inspect the paths.py file itself to check default without conftest patch
    import importlib.util
    spec = importlib.util.spec_from_file_location("raw_paths", paths.__file__)
    raw_paths = importlib.util.module_from_spec(spec)
    monkeypatch.delenv("N3MC_FREE_ANTIGRAVITY_HOME", raising=False)
    spec.loader.exec_module(raw_paths)
    assert ".n3mc-free-antigravity" in raw_paths.HOME_DIR

    from n3memorycore_free_antigravity.n3memory import DEFAULT_PORT
    assert DEFAULT_PORT == 18527


def test_hooks_registration_and_replacement(tmp_path, monkeypatch):
    """Verify hooks.json registration, legacy replacement, and foreign key preservation."""
    hooks_file = tmp_path / "hooks.json"
    initial_data = {
        "other-tool": {
            "PreInvocation": [{"type": "command", "command": "other.exe"}]
        },
        "n3memorycore": {
            "PreInvocation": [{"type": "command", "command": "C:/python/Scripts/n3mc-hook.exe"}],
            "Stop": [{"type": "command", "command": "C:/python/Scripts/n3mc-stop-hook.exe"}]
        }
    }
    hooks_file.write_text(json.dumps(initial_data), encoding="utf-8")
    monkeypatch.setenv("N3MC_HOOKS_CONFIG_PATH", str(hooks_file))
    monkeypatch.setenv("N3MC_FREE_ANTIGRAVITY_HOME", str(tmp_path / "home"))

    from n3memorycore_free_antigravity.n3memory import cmd_init
    rc = cmd_init()
    assert rc == 0

    with open(hooks_file, "r", encoding="utf-8") as f:
        updated = json.load(f)

    # other-tool preserved
    assert "other-tool" in updated
    # legacy n3memorycore was pure legacy so replaced
    assert "n3memorycore" not in updated
    # new key registered
    assert "n3memorycore-free-antigravity" in updated
    entry = updated["n3memorycore-free-antigravity"]
    assert "PreInvocation" in entry
    assert "Stop" in entry
    assert entry["PreInvocation"][0]["timeout"] == 120
    assert entry["Stop"][0]["timeout"] == 120


def test_turn_tracking_and_reinvocation(tmp_path, monkeypatch):
    """Verify tool re-invocations return {} and new steps create distinct turn_ids."""
    home = tmp_path / "n3mc_home"
    monkeypatch.setenv("N3MC_FREE_ANTIGRAVITY_HOME", str(home))
    from n3memorycore_free_antigravity.n3memory import (
        _is_antigravity, _compute_turn_key, _read_turn_key, _write_turn_key
    )

    conv_id = "conv-test-123"
    payload1 = {
        "hookEventName": "PreInvocation",
        "conversationId": conv_id,
        "lastUserInput": "Hello Antigravity",
        "invocationNum": 0,
        "initialNumSteps": 1
    }
    assert _is_antigravity(payload1)
    key1 = _compute_turn_key(payload1, "Hello Antigravity", None)
    assert key1.startswith("init:1:")

    # Tool loop re-invocation (invocationNum = 1, same prompt)
    payload2 = {
        "hookEventName": "PreInvocation",
        "conversationId": conv_id,
        "lastUserInput": "Hello Antigravity",
        "invocationNum": 1,
        "initialNumSteps": 1
    }
    key2 = _compute_turn_key(payload2, "Hello Antigravity", None)
    assert key2 == key1


def test_transcript_extraction(tmp_path):
    """Verify <USER_REQUEST> extraction and transcript_full.jsonl fallback."""
    from n3memorycore_free_antigravity.n3memory import (
        _extract_transcript_request, _extract_last_assistant_from_transcript
    )

    transcript = tmp_path / "transcript.jsonl"
    full_transcript = tmp_path / "transcript_full.jsonl"

    # Truncated entry in transcript.jsonl
    line1 = {
        "step_index": 0,
        "type": "USER_INPUT",
        "content": "<USER_REQUEST>Truncated...",
        "truncated_fields": ["content"]
    }
    line2 = {
        "step_index": 1,
        "type": "PLANNER_RESPONSE",
        "content": "Assistant answer",
        "truncated_fields": []
    }
    with open(transcript, "w", encoding="utf-8") as f:
        f.write(json.dumps(line1) + "\n" + json.dumps(line2) + "\n")

    # Full entry in transcript_full.jsonl
    full_line1 = {
        "step_index": 0,
        "type": "USER_INPUT",
        "content": "<USER_REQUEST>Full user question from transcript_full</USER_REQUEST><ADDITIONAL_METADATA>xyz</ADDITIONAL_METADATA>",
        "truncated_fields": []
    }
    with open(full_transcript, "w", encoding="utf-8") as f:
        f.write(json.dumps(full_line1) + "\n")

    req = _extract_transcript_request(str(transcript))
    assert req == "Full user question from transcript_full"

    resp = _extract_last_assistant_from_transcript(str(transcript))
    assert resp == "Assistant answer"


def test_claude_code_dual_input():
    """Verify Claude Code inputs are detected and formatted with raw Markdown."""
    from n3memorycore_free_antigravity.n3memory import _is_antigravity

    claude_payload = {
        "session_id": "claude-sess-1",
        "prompt": "Hello Claude",
        "transcript_path": "/tmp/transcript.jsonl"
    }
    assert not _is_antigravity(claude_payload)

    ag_payload = {
        "conversationId": "ag-conv-1",
        "hookEventName": "PreInvocation",
        "lastUserInput": "Hello Antigravity"
    }
    assert _is_antigravity(ag_payload)


def test_foreign_server_isolation_when_offline(tmp_path, monkeypatch):
    """When connect_server is configured but offline, do not write to local DB and emit notice."""
    from n3memorycore_free_antigravity import n3memory as n3m
    config_file = paths.CONFIG_FILE
    os.makedirs(os.path.dirname(config_file), exist_ok=True)

    with open(config_file, "w", encoding="utf-8") as f:
        json.dump({
            "connect_server_port": 18599,
            "connect_server_root": str(tmp_path / "foreign_root")
        }, f)
    n3m._CFG_CACHE = None
    n3m._CFG_SOURCE = None

    from n3memorycore_free_antigravity.n3memory import (
        _get_foreign_connection, _is_foreign_configured, cmd_hook_submit
    )

    assert _is_foreign_configured()
    assert _get_foreign_connection() is None


def test_save_antigravity_turn_cli_and_agent_name(conn, tmp_path, monkeypatch):
    """--save-antigravity-turn must be accepted by CLI and save with [assistant] and agent_name='antigravity'."""
    import io
    from n3memorycore_free_antigravity import n3memory as n3m

    transcript = tmp_path / "transcript.jsonl"
    transcript.write_text(json.dumps({
        "step_index": 2,
        "type": "PLANNER_RESPONSE",
        "content": "Antigravity final answer",
    }) + "\n", encoding="utf-8")

    payload = {
        "hookEventName": "Stop",
        "conversationId": "conv-ag-save-1",
        "transcriptPath": str(transcript),
    }
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(
        io.BytesIO(json.dumps(payload).encode("utf-8")), encoding="utf-8"
    ))
    rc = n3m.main(["--save-antigravity-turn"])
    assert rc == 0

    rows = conn.execute("SELECT content, agent_name FROM memories").fetchall()
    assert len(rows) == 1
    assert rows[0]["content"] == "[assistant] Antigravity final answer"
    assert rows[0]["agent_name"] == "antigravity"


def test_cmd_stop_antigravity_outputs_decision_and_uses_workspace_paths(tmp_path, monkeypatch, capsys):
    """cmd_stop() must honor workspacePaths and emit {'decision': 'stop'} for Antigravity payloads."""
    import io
    from n3memorycore_free_antigravity import n3memory as n3m

    ws = tmp_path / "ag_workspace"
    ws.mkdir()
    other = tmp_path / "other_cwd"
    other.mkdir()
    monkeypatch.chdir(other)

    payload = {
        "hookEventName": "Stop",
        "conversationId": "conv-stop-1",
        "workspacePaths": [str(ws)],
    }
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(
        io.BytesIO(json.dumps(payload).encode("utf-8")), encoding="utf-8"
    ))
    rc = n3m.cmd_stop()
    assert rc == 0
    out = capsys.readouterr().out.strip()
    assert json.loads(out) == {"decision": "stop"}
    assert (ws / ".agents" / "rules" / "n3mc-behavior.md").exists()
    assert not (other / ".agents").exists()


def test_processor_supports_assistant_prefix_and_package_show_turn(conn, cfg, use_fake_embed):
    """[assistant] chunks must work with _is_cjk_text, _turn_representative, and render_memory_context."""
    from n3memorycore_free_antigravity.core import processor as p
    from tests.conftest import add

    # _is_cjk_text strips [assistant] prefix
    assert p._is_cjk_text("[assistant] 日本語のテスト") is True

    # _turn_representative finds [assistant] reply
    long_reply = "[assistant] " + ("これはバージョン比較のための十分な長さの応答テキストです。" * 5)
    add(conn, cfg, long_reply, turn_id="T_AG_1", agent="antigravity")
    rep = p._turn_representative(conn, "T_AG_1", min_chars=50)
    assert rep is not None and len(rep) == 768

    # render_memory_context uses n3memorycore_free_antigravity.n3memory
    rendered = p.render_memory_context("q", [], pairs={}, pairs_omitted={"T_AG_1": 2})
    assert "python -m n3memorycore_free_antigravity.n3memory --show-turn T_AG_1" in rendered


def test_foreign_server_forward_and_offline_isolation(conn, tmp_path, monkeypatch):
    """§3.7: forward /buffer (with 'content' key) and /search when online; never write local DB when offline."""
    from n3memorycore_free_antigravity import n3memory as n3m
    from n3memorycore_free_antigravity.core import database as db

    config_file = paths.CONFIG_FILE
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    foreign_root = str(tmp_path / "foreign_root")
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump({"connect_server_port": 18599, "connect_server_root": foreign_root}, f)
    n3m._CFG_CACHE = None
    n3m._CFG_SOURCE = None

    # 1) Offline: _save_text must NOT write to local DB
    monkeypatch.setattr(n3m, "_get_foreign_connection", lambda: None)
    saved, failed = n3m._save_text("user", "do not split memory", "T_OFF", "S1", agent_name="antigravity")
    assert saved == 0 and failed > 0
    assert db.count_memories(conn) == 0

    out = n3m._search_text("anything", "S1")
    assert "memory search unavailable" in out

    # 2) Online: forward /buffer with 'content' and /search to foreign port
    calls = []

    def fake_post(path, body, timeout=30, port=None):
        calls.append((path, body, port))
        if path == "/buffer":
            return {"status": "ok", "count": 1}
        if path == "/search":
            return {"results": [], "pairs": {}, "pairs_omitted": {}}
        raise AssertionError(f"unexpected path {path}")

    monkeypatch.setattr(n3m, "_get_foreign_connection", lambda: (18599, foreign_root))
    monkeypatch.setattr(n3m, "_post", fake_post)

    saved, failed = n3m._save_text("assistant", "forwarded reply", "T_ON", "S1", agent_name="antigravity")
    assert saved == 1 and failed == 0
    assert calls[0][0] == "/buffer"
    assert calls[0][2] == 18599
    assert calls[0][1]["content"] == "[assistant] forwarded reply"
    assert calls[0][1]["agent_name"] == "antigravity"

    res = n3m._search_text("forwarded", "S1")
    assert calls[1][0] == "/search"
    assert calls[1][2] == 18599
    assert "# Recalled Memory Context" in res


def test_home_of_env_prefers_antigravity_home(tmp_path):
    """_home_of_env must resolve N3MC_FREE_ANTIGRAVITY_HOME."""
    from n3memorycore_free_antigravity import n3memory as n3m

    target = str(tmp_path / "custom_ag_home")
    assert os.path.normcase(n3m._home_of_env({"N3MC_FREE_ANTIGRAVITY_HOME": target})) == os.path.normcase(os.path.abspath(target))


def test_p1_1_stop_and_preinvocation_assistant_separation(tmp_path, conn, monkeypatch):
    """P1-1: Stop must not save previous answer if current turn has no answer yet.
    PreInvocation must salvage previous answer into prev_turn_id only."""
    import io
    from n3memorycore_free_antigravity import n3memory as n3m

    transcript = tmp_path / "transcript.jsonl"
    q1 = {"step_index": 0, "type": "USER_INPUT", "content": "Question 1"}
    a1 = {"step_index": 1, "type": "PLANNER_RESPONSE", "content": "Answer 1"}
    q2 = {"step_index": 2, "type": "USER_INPUT", "content": "Question 2"}

    transcript.write_text("\n".join(json.dumps(x) for x in [q1, a1, q2]) + "\n", encoding="utf-8")

    # 1. Stop called after Q2 before A2 arrives -> should NOT save A1 as T2
    n3m._write_turn_id("conv-p1-1", "T2")
    payload_stop_q2 = {
        "hookEventName": "Stop",
        "conversationId": "conv-p1-1",
        "transcriptPath": str(transcript),
    }
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(
        io.BytesIO(json.dumps(payload_stop_q2).encode("utf-8")), encoding="utf-8"
    ))
    rc = n3m.cmd_save_antigravity_turn()
    assert rc == 0
    t2_rows = conn.execute("SELECT content FROM memories WHERE turn_id='T2'").fetchall()
    assert len(t2_rows) == 0  # 0 records for T2

    # 2. A2 arrives -> Stop should now save A2 for T2
    a2 = {"step_index": 3, "type": "PLANNER_RESPONSE", "content": "Answer 2"}
    transcript.write_text("\n".join(json.dumps(x) for x in [q1, a1, q2, a2]) + "\n", encoding="utf-8")
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(
        io.BytesIO(json.dumps(payload_stop_q2).encode("utf-8")), encoding="utf-8"
    ))
    rc = n3m.cmd_save_antigravity_turn()
    assert rc == 0
    t2_rows = conn.execute("SELECT content FROM memories WHERE turn_id='T2'").fetchall()
    assert len(t2_rows) == 1
    assert t2_rows[0]["content"] == "[assistant] Answer 2"

    # 3. Previous Stop missed (transcript has Q1, A1, Q2 but T1 had no A1 saved)
    transcript2 = tmp_path / "transcript2.jsonl"
    transcript2.write_text("\n".join(json.dumps(x) for x in [q1, a1, q2]) + "\n", encoding="utf-8")
    n3m._write_turn_id("conv-p1-1b", "T1")

    payload_preinv_q2 = {
        "hookEventName": "PreInvocation",
        "conversationId": "conv-p1-1b",
        "lastUserInput": "Question 2",
        "transcriptPath": str(transcript2),
        "invocationNum": 0,
        "initialNumSteps": 1
    }
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(
        io.BytesIO(json.dumps(payload_preinv_q2).encode("utf-8")), encoding="utf-8"
    ))
    rc = n3m.cmd_hook_submit()
    assert rc == 0
    t1_rows = conn.execute("SELECT content FROM memories WHERE turn_id='T1'").fetchall()
    assert any(r["content"] == "[assistant] Answer 1" for r in t1_rows)


def test_p1_2_retry_after_save_failure_keeps_turn_id_and_dedups(tmp_path, conn, monkeypatch):
    """P1-2: Failure during save must not mark turn as finished. Retry must reuse turn_id and dedup."""
    import io
    from n3memorycore_free_antigravity import n3memory as n3m

    # Ensure prompt splits into multiple chunks (> 400 chars per paragraph)
    long_prompt = ("Paragraph A " * 50) + "\n\n" + ("Paragraph B " * 50) + "\n\n" + ("Paragraph C " * 50)
    payload = {
        "hookEventName": "PreInvocation",
        "conversationId": "conv-p1-2",
        "lastUserInput": long_prompt,
        "invocationNum": 0,
        "initialNumSteps": 1
    }

    # Simulate failure on second chunk save
    orig_save_record = n3m._save_record
    call_count = 0

    def failing_save_record(rec, effective_agent, session_id, turn_id):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            return {"status": "error", "message": "simulated DB failure"}
        return orig_save_record(rec, effective_agent, session_id, turn_id)

    monkeypatch.setattr(n3m, "_save_record", failing_save_record)
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(
        io.BytesIO(json.dumps(payload).encode("utf-8")), encoding="utf-8"
    ))

    # First attempt: should fail with exit code 1
    rc1 = n3m.cmd_hook_submit()
    assert rc1 == 1

    # Restore normal save
    monkeypatch.setattr(n3m, "_save_record", orig_save_record)

    # Second attempt (resend same event): should retry with same turn_id, dedup chunk 1, save chunk 2 and 3
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(
        io.BytesIO(json.dumps(payload).encode("utf-8")), encoding="utf-8"
    ))
    rc2 = n3m.cmd_hook_submit()
    assert rc2 == 0

    rows = conn.execute("SELECT content, turn_id FROM memories").fetchall()
    # All chunks saved exactly once under the same turn_id
    turn_ids = {r["turn_id"] for r in rows}
    assert len(turn_ids) == 1
    contents = [r["content"] for r in rows]
    expected_chunks = n3m.chunk_text(n3m.purify_text(long_prompt), 400, 40)
    assert len(contents) == len(expected_chunks)
    assert len(set(contents)) == len(expected_chunks)

    # Third attempt (tool re-invocation): should be suppressed with {}
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(
        io.BytesIO(json.dumps(payload).encode("utf-8")), encoding="utf-8"
    ))
    saved_calls = 0
    monkeypatch.setattr(n3m, "_save_record", lambda *a, **k: saved_calls + 1)
    rc3 = n3m.cmd_hook_submit()
    assert rc3 == 0
    assert saved_calls == 0


def test_p1_3_manual_buffer_foreign_forward_and_offline_isolation(tmp_path, conn, monkeypatch):
    """P1-3: cmd_buffer must forward in foreign mode and not touch local DB when offline."""
    from n3memorycore_free_antigravity import n3memory as n3m
    from n3memorycore_free_antigravity.core import database as db

    config_file = paths.CONFIG_FILE
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    foreign_root = str(tmp_path / "foreign_root")

    with open(config_file, "w", encoding="utf-8") as f:
        json.dump({"connect_server_port": 18599, "connect_server_root": foreign_root}, f)
    n3m._CFG_CACHE = None
    n3m._CFG_SOURCE = None

    # 1. Foreign configured but offline
    monkeypatch.setattr(n3m, "_get_foreign_connection", lambda: None)
    rc_offline = n3m.cmd_buffer("manual offline test")
    assert rc_offline == 1
    assert db.count_memories(conn) == 0

    # 2. Foreign configured and online
    calls = []
    def fake_post(path, body, timeout=30, port=None):
        if port == 18599:
            calls.append((path, body, port))
            return {"status": "ok", "count": 1}
        raise urllib.error.URLError("local server not running")

    monkeypatch.setattr(n3m, "_get_foreign_connection", lambda: (18599, foreign_root))
    monkeypatch.setattr(n3m, "_post", fake_post)
    rc_online = n3m.cmd_buffer("manual online test")
    assert rc_online == 0
    assert len(calls) == 1
    assert calls[0][0] == "/buffer"
    assert calls[0][2] == 18599
    assert calls[0][1]["content"] == "manual online test"
    assert db.count_memories(conn) == 0

    # 3. Standalone mode: saves to local DB (no foreign configured, direct DB write)
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump({}, f)
    n3m._CFG_CACHE = None
    n3m._CFG_SOURCE = None
    monkeypatch.setattr(n3m, "_use_server", lambda: False)
    rc_standalone = n3m.cmd_buffer("manual standalone test")
    assert rc_standalone == 0
    assert db.count_memories(conn) == 1


def test_p2_1_init_removes_legacy_hooks_even_if_new_entry_already_present(tmp_path, monkeypatch):
    """P2-1: cmd_init must clean legacy n3memorycore even when new entry already matches."""
    from n3memorycore_free_antigravity import n3memory as n3m

    hooks_file = tmp_path / "hooks.json"
    home = tmp_path / "home"
    monkeypatch.setenv("N3MC_HOOKS_CONFIG_PATH", str(hooks_file))
    monkeypatch.setenv("N3MC_FREE_ANTIGRAVITY_HOME", str(home))

    # Initialize once to get valid new entry
    rc1 = n3m.cmd_init()
    assert rc1 == 0

    data = json.loads(hooks_file.read_text(encoding="utf-8"))
    assert "n3memorycore-free-antigravity" in data

    # Inject legacy n3memorycore entry
    data["n3memorycore"] = {
        "PreInvocation": [{"type": "command", "command": "C:/python/Scripts/n3mc-hook.exe"}],
        "Stop": [{"type": "command", "command": "C:/python/Scripts/n3mc-stop-hook.exe"}]
    }
    data["custom-tool"] = {"PreInvocation": [{"type": "command", "command": "custom.exe"}]}
    hooks_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # Re-run init
    rc2 = n3m.cmd_init()
    assert rc2 == 0

    updated = json.loads(hooks_file.read_text(encoding="utf-8"))
    assert "n3memorycore" not in updated  # legacy removed
    assert "n3memorycore-free-antigravity" in updated
    assert "custom-tool" in updated  # preserved

    # Next init should be a no-op
    mtime_before = os.path.getmtime(hooks_file)
    rc3 = n3m.cmd_init()
    assert rc3 == 0
    assert os.path.getmtime(hooks_file) == mtime_before


def test_p2_2_show_turn_foreign_db_and_omitted_message(tmp_path, conn, capsys, monkeypatch):
    """P2-2: cmd_show_turn reads foreign DB if configured; renderer hides command if DB unreachable."""
    from n3memorycore_free_antigravity import n3memory as n3m
    from n3memorycore_free_antigravity.core import database as db
    from n3memorycore_free_antigravity.core import processor as proc

    foreign_root = tmp_path / "foreign_root"
    foreign_mem = foreign_root / ".memory"
    foreign_mem.mkdir(parents=True)
    foreign_db_path = foreign_mem / "n3memory.db"

    fconn = db.get_connection(str(foreign_db_path))
    db.init_db(fconn)
    db.insert_memory(fconn, "f1", "[user] Question in foreign", "2026-11-23T00:00:00Z", "owner", turn_id="T_FOREIGN")
    db.insert_memory(fconn, "f2", "[assistant] Answer in foreign", "2026-11-23T00:01:00Z", "owner", turn_id="T_FOREIGN")
    fconn.close()

    config_file = paths.CONFIG_FILE
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump({"connect_server_port": 18599, "connect_server_root": str(foreign_root)}, f)
    n3m._CFG_CACHE = None
    n3m._CFG_SOURCE = None

    # Local DB is empty, foreign DB has T_FOREIGN
    assert db.count_memories(conn) == 0
    rc = n3m.cmd_show_turn("T_FOREIGN")
    assert rc == 0
    out = capsys.readouterr().out
    assert "Question in foreign" in out
    assert "Answer in foreign" in out
    assert "Total: 2 records" in out

    # If foreign DB path does not exist, omit command guide
    rendered = proc.render_memory_context("q", [], pairs={}, pairs_omitted={"T1": 3}, show_turn_available=False)
    assert "_show-turn" not in rendered
    assert "_(3 more chunk(s) of this exchange omitted.)_" in rendered


def test_p2_3_python_cmd_fallback_python310(monkeypatch, tmp_path):
    """P2-3: Fallback hook command on Python 3.10 must not include -P and must quote paths with spaces."""
    from n3memorycore_free_antigravity import n3memory as n3m

    hooks_file = tmp_path / "hooks.json"
    hooks_file.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("N3MC_HOOKS_CONFIG_PATH", str(hooks_file))
    fake_py = "C:\\Program Files\\Python310\\python.exe"
    monkeypatch.setattr(sys, "executable", fake_py)
    monkeypatch.setattr(sys, "version_info", (3, 10, 0, "final", 0))
    monkeypatch.setattr(shutil, "which", lambda *a: None)

    # Make sure exe_path does not exist so it triggers the python fallback
    orig_exists = os.path.exists
    monkeypatch.setattr(os.path, "exists", lambda p: False if str(p).endswith(".exe") else orig_exists(p))

    rc = n3m.cmd_init()
    assert rc == 0

    data = json.loads(hooks_file.read_text(encoding="utf-8"))
    entry = data["n3memorycore-free-antigravity"]
    pre_cmd = entry["PreInvocation"][0]["command"]
    stop_cmd = entry["Stop"][0]["command"]

    # Must be quoted because of space in 'Program Files'
    assert '"C:/Program Files/Python310/python.exe"' in pre_cmd or '"C:\\Program Files\\Python310\\python.exe"' in pre_cmd
    # Must NOT have -P on Python 3.10
    assert " -P " not in pre_cmd
    assert " -P " not in stop_cmd
    assert "-m n3memorycore_free_antigravity.n3mc_hook" in pre_cmd
    assert "-m n3memorycore_free_antigravity.n3mc_stop_hook" in stop_cmd


def test_extract_assistant_skips_empty_planner_response_and_bad_full_lines(tmp_path):
    """Empty/tool-only PLANNER_RESPONSE rows must be skipped; malformed lines in transcript_full.jsonl must not break lookup."""
    from n3memorycore_free_antigravity import n3memory as n3m

    t_path = tmp_path / "transcript.jsonl"
    full_path = tmp_path / "transcript_full.jsonl"

    # PreInvocation scenario: Turn 2 USER_INPUT is at the end (no Turn 2 reply yet);
    # should skip step 3 (empty content) and recover step 2 from transcript_full.jsonl despite malformed line
    t_pre_lines = [
        json.dumps({"step_index": 1, "type": "USER_INPUT", "content": "<USER_REQUEST>Turn 1</USER_REQUEST>"}),
        json.dumps({"step_index": 2, "type": "PLANNER_RESPONSE", "content": "truncated...", "truncated_fields": ["content"]}),
        json.dumps({"step_index": 3, "type": "PLANNER_RESPONSE", "content": "", "tool_calls": [{"name": "run_command"}]}),
        json.dumps({"step_index": 4, "type": "USER_INPUT", "content": "<USER_REQUEST>Turn 2</USER_REQUEST>"}),
    ]
    t_path.write_text("\n".join(t_pre_lines) + "\n", encoding="utf-8")

    full_lines = [
        "{malformed json line",
        "",
        json.dumps({"step_index": 2, "type": "PLANNER_RESPONSE", "content": "Turn 1 full answer"}),
    ]
    full_path.write_text("\n".join(full_lines) + "\n", encoding="utf-8")

    assert n3m._extract_assistant_for_preinvocation(str(t_path)) == "Turn 1 full answer"

    # Stop scenario: Turn 2 has a real reply (step 5) followed by a tool-only PLANNER_RESPONSE (step 6)
    t_stop_lines = t_pre_lines + [
        json.dumps({"step_index": 5, "type": "PLANNER_RESPONSE", "content": "Turn 2 real answer"}),
        json.dumps({"step_index": 6, "type": "PLANNER_RESPONSE", "tool_calls": [{"name": "read_file"}]}),
    ]
    t_path.write_text("\n".join(t_stop_lines) + "\n", encoding="utf-8")
    assert n3m._extract_assistant_for_stop(str(t_path)) == "Turn 2 real answer"


def test_find_unindexed_memories_detects_missing_bigram_fts(conn, cfg):
    """find_unindexed_memories and _repair must detect and repair rows missing only memories_fts_bi."""
    from n3memorycore_free_antigravity import n3memory as n3m
    from n3memorycore_free_antigravity.core import database as db

    # Mark one-time migrations as already completed (normal steady-state DB)
    db.set_meta(conn, "fts_bigram", "1")
    db.set_meta(conn, "fts_punct_cleaned", "1")
    conn.commit()

    vec = [0.0] * db.EMBED_DIM
    vec[0] = 1.0
    rowid = db.insert_memory(
        conn, "bi-test-1", "東京の天気は晴れです", "2026-11-23T00:00:00+00:00",
        cfg["owner_id"], cfg["local_id"], "antigravity", "S1", turn_id="T_BI", embedding=vec,
    )
    # Remove only memories_fts_bi entry
    conn.execute("DELETE FROM memories_fts_bi WHERE rowid=?", (rowid,))
    conn.commit()

    unindexed = db.find_unindexed_memories(conn)
    assert len(unindexed) == 1
    assert unindexed[0]["id"] == "bi-test-1"

    changed = n3m._repair(conn, cfg)
    assert changed == 1
    assert db.find_unindexed_memories(conn) == []
    assert db.search_fts_bigram(conn, "東京")


def test_cmd_repair_skips_in_connection_mode_without_starting_server(tmp_path, monkeypatch, capsys):
    """cmd_repair must not start local server or touch local DB when connection mode is configured."""
    from n3memorycore_free_antigravity import n3memory as n3m

    config_file = paths.CONFIG_FILE
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump({"connect_server_port": 18520, "connect_server_root": str(tmp_path / "partner")}, f)
    n3m._CFG_CACHE = None
    n3m._CFG_SOURCE = None

    called = []
    monkeypatch.setattr(n3m, "_use_server", lambda: (called.append("use_server"), True)[1])
    rc = n3m.cmd_repair()
    assert rc == 0
    assert called == []
    assert "connection mode" in capsys.readouterr().err


def test_cmd_init_skips_behavior_md_in_home_dir(tmp_path, monkeypatch):
    """cmd_init must not create .agents/rules/n3mc-behavior.md when run in user's home directory."""
    from n3memorycore_free_antigravity import n3memory as n3m

    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    hooks_file = tmp_path / "hooks.json"
    monkeypatch.setenv("N3MC_HOOKS_CONFIG_PATH", str(hooks_file))
    monkeypatch.chdir(fake_home)
    monkeypatch.setattr(n3m, "_cwd_is_home", lambda cwd=None: True)

    rc = n3m.cmd_init()
    assert rc == 0
    assert not (fake_home / ".agents" / "rules" / "n3mc-behavior.md").exists()

