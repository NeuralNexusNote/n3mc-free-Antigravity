# -*- coding: utf-8 -*-
"""Repro for the 2026-11-23 Fable review. Runs inside a copy of the repo (conftest isolation applies)."""
import io
import json
import os
import subprocess
import sys

import pytest

from n3memorycore_free_antigravity import n3memory as n3m
from n3memorycore_free_antigravity import paths as paths_mod


def test_F1_home_of_env_disagrees_with_paths(monkeypatch):
    """Server process started with only N3MC_HOME set: paths.py ignores it, _home_of_env honours it."""
    import importlib.util
    monkeypatch.delenv("N3MC_FREE_ANTIGRAVITY_HOME", raising=False)
    monkeypatch.setenv("N3MC_HOME", r"D:\other-n3mc")
    spec = importlib.util.spec_from_file_location("raw_paths", paths_mod.__file__)
    raw = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(raw)
    real_home = raw.HOME_DIR                       # what the server process really uses
    judged = n3m._home_of_env(dict(os.environ))    # what _is_own_server_process compares
    print("paths.HOME_DIR =", real_home, "| _home_of_env =", judged)
    assert n3m._norm(real_home) == n3m._norm(judged)


def test_F1b_own_server_not_recognised(monkeypatch):
    import psutil

    class P:
        def __init__(self, pid): pass
        def cmdline(self): return ["python", "-P", "-m", "n3memorycore_free_antigravity.n3memory", "--run-server"]
        def environ(self): return {"N3MC_HOME": r"D:\other-n3mc"}   # no N3MC_FREE_ANTIGRAVITY_HOME
    monkeypatch.setattr(psutil, "Process", P)
    # the server's real folder is the default one; pretend ours is the default too
    monkeypatch.setattr(n3m, "HOME_DIR", os.path.abspath(os.path.expanduser(os.path.join("~", ".n3mc-free-antigravity"))))
    assert n3m._is_own_server_process(pid=1234) is True


OLD_RULES = "<!-- n3mc-behavior agy-v1 -->\n# N3MemoryCore Behavioral Guidelines\n\nrun `python -m n3memorycore.n3memory --search \"<keywords>\"`\n"


def test_F2_old_antigravity_rules_file_is_left(tmp_path, monkeypatch):
    import hashlib
    p = tmp_path / "ws" / ".agents" / "rules"
    p.mkdir(parents=True)
    f = p / "n3mc-behavior.md"

    # 1. Unregistered hash is treated as edited by hand and NOT replaced
    f.write_text(OLD_RULES, encoding="utf-8")
    r1 = n3m._ensure_behavior_md(str(tmp_path / "ws"))
    text1 = f.read_text(encoding="utf-8")
    assert r1 == "edited"
    assert "n3memorycore.n3memory" in text1

    # 2. When the hash is in _KNOWN_BEHAVIOR_MD_HASHES, it is replaced with the new template
    h = hashlib.sha256(OLD_RULES.encode("utf-8")).hexdigest()[:16]
    monkeypatch.setattr(n3m, "_KNOWN_BEHAVIOR_MD_HASHES", set(n3m._KNOWN_BEHAVIOR_MD_HASHES) | {h})
    r2 = n3m._ensure_behavior_md(str(tmp_path / "ws"))
    text2 = f.read_text(encoding="utf-8")
    assert r2 == "updated"
    assert "n3memorycore_free_antigravity.n3memory" in text2


def _run_submit(monkeypatch, payload):
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(json.dumps(payload).encode("utf-8")), encoding="utf-8"))
    return n3m.cmd_hook_submit()


def test_F3_server_work_before_reinvocation_check(monkeypatch, tmp_path, capsys):
    calls = []
    monkeypatch.setattr(n3m, "_use_server", lambda: calls.append("use_server") or True)
    monkeypatch.setattr(n3m, "_post", lambda path, body, **k: calls.append(path) or {"status": "ok", "results": [], "pairs": {}, "pairs_omitted": {}, "repaired": 0})
    tr = tmp_path / "transcript_full.jsonl"
    tr.write_text(json.dumps({"type": "USER_INPUT", "step_index": 5, "content": "<USER_REQUEST>hello</USER_REQUEST>"}) + "\n", encoding="utf-8")
    base = {"hookEventName": "PreInvocation", "conversationId": "c1", "lastUserInput": "hello",
            "transcriptPath": str(tr), "initialNumSteps": 6}
    _run_submit(monkeypatch, dict(base, invocationNum=0))
    capsys.readouterr()
    calls.clear()
    _run_submit(monkeypatch, dict(base, invocationNum=1, initialNumSteps=8))
    out = capsys.readouterr().out.strip()
    print("output:", out, "| calls on the re-invocation:", calls)
    assert out == "{}"
    assert calls == []


def test_F4_stop_blocks_on_open_stdin(tmp_path):
    env = dict(os.environ, N3MC_FREE_ANTIGRAVITY_HOME=str(tmp_path / "home"),
               PYTHONPATH=os.path.dirname(os.path.dirname(paths_mod.__file__)))
    proc = subprocess.Popen([sys.executable, "-m", "n3memorycore_free_antigravity.n3memory", "--stop"],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            cwd=str(tmp_path), env=env)
    try:
        proc.wait(timeout=20)
    except subprocess.TimeoutExpired:
        proc.kill()
        pytest.fail("--stop did not end within 20 s while stdin stayed open")


def test_F5_notice_when_connected_server_is_down(monkeypatch, tmp_path, capsys):
    cfg = dict(n3m.get_config(), connect_server_port=59999, connect_server_root=str(tmp_path / "nowhere"))
    monkeypatch.setattr(n3m, "_CFG_CACHE", cfg)
    monkeypatch.setattr(n3m, "_get_foreign_connection", lambda: None)
    _run_submit(monkeypatch, {"hookEventName": "PreInvocation", "conversationId": "c2",
                              "lastUserInput": "hello there", "invocationNum": 0})
    out = capsys.readouterr().out
    print(out)
    assert "N3MC notice" in out


def test_F6_invocation_num_null(monkeypatch, capsys):
    monkeypatch.setattr(n3m, "_use_server", lambda: False)
    rc = _run_submit(monkeypatch, {"hookEventName": "PreInvocation", "conversationId": "c3",
                                   "lastUserInput": "x", "invocationNum": None})
    assert rc in (0, 1)


# -*- coding: utf-8 -*-
import os, sqlite3, json, io, sys
from n3memorycore_free_antigravity import n3memory as n3m


def _partner_db(root):
    mem = root / ".memory"; mem.mkdir(parents=True)
    p = mem / "n3memory.db"
    c = sqlite3.connect(p)
    c.execute("PRAGMA journal_mode = DELETE")
    c.execute("CREATE TABLE memories (id TEXT PRIMARY KEY, content TEXT, timestamp TEXT, owner_id TEXT, local_id TEXT, agent_name TEXT, session_id TEXT, turn_id TEXT)")
    c.execute("INSERT INTO memories VALUES ('1','[user] partner row','2026-11-23T00:00:00+00:00','o','l','claude-code','s','T1')")
    c.commit(); c.close()
    return p


def test_N1_show_turn_changes_partner_db(monkeypatch, tmp_path, capsys):
    root = tmp_path / "partner"
    p = _partner_db(root)
    before = sqlite3.connect(p).execute("PRAGMA journal_mode").fetchone()[0]
    cfg = dict(n3m.get_config(), connect_server_port=59999, connect_server_root=str(root))
    monkeypatch.setattr(n3m, "_CFG_CACHE", cfg)
    n3m.cmd_show_turn("T1")
    print(capsys.readouterr().out)
    after = sqlite3.connect(p).execute("PRAGMA journal_mode").fetchone()[0]
    print("journal_mode before:", before, "after:", after, "| files:", sorted(os.listdir(root / ".memory")))
    assert after == before


def test_N2_show_turn_falls_back_to_local_db(monkeypatch, tmp_path, capsys, conn):
    """Connected, partner DB file not reachable (e.g. PostgreSQL partner), local DB exists."""
    cfg = dict(n3m.get_config(), connect_server_port=59999, connect_server_root=str(tmp_path / "no-file-here"))
    monkeypatch.setattr(n3m, "_CFG_CACHE", cfg)
    rc = n3m.cmd_show_turn("T1")
    cap = capsys.readouterr()
    print("rc", rc, "| out:", cap.out.strip(), "| err:", cap.err.strip())
    assert "Total: 0 records" not in cap.out   # it silently answered from the local DB


def test_N3_list_and_recall_thread_read_local_in_connect_mode(monkeypatch, tmp_path, capsys, conn):
    root = tmp_path / "partner"
    _partner_db(root)
    cfg = dict(n3m.get_config(), connect_server_port=59999, connect_server_root=str(root))
    monkeypatch.setattr(n3m, "_CFG_CACHE", cfg)
    n3m.cmd_list()
    out = capsys.readouterr().out
    print(out)
    assert "partner row" in out


def test_N4_reinvocation_while_partner_down_injects_every_time(monkeypatch, tmp_path, capsys):
    cfg = dict(n3m.get_config(), connect_server_port=59999, connect_server_root=str(tmp_path / "x"))
    monkeypatch.setattr(n3m, "_CFG_CACHE", cfg)
    monkeypatch.setattr(n3m, "_get_foreign_connection", lambda: None)
    outs = []
    for inv in (0, 1, 2):
        payload = {"hookEventName": "PreInvocation", "conversationId": "c9", "lastUserInput": "hello", "invocationNum": inv}
        monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(json.dumps(payload).encode()), encoding="utf-8"))
        n3m.cmd_hook_submit()
        outs.append(capsys.readouterr().out.strip())
    print(outs)
    assert outs[1] == "{}" and outs[2] == "{}"


def test_C3_old_behavior_notice_cleaned(tmp_path):
    ws = tmp_path / "ws"
    p = ws / ".agents" / "rules" / "n3mc-behavior.md"
    p.parent.mkdir(parents=True)
    p.write_text(n3m._BEHAVIOR_MD_CONTENT, encoding="utf-8")

    # Seed notices with old-style key mentioning this path
    notices = {
        "behavior_md_edited:oldkey1": {"message": f"The rules file {str(p)} has been edited by hand..."},
        "behavior_md_edited:other": {"message": "The rules file D:/other/n3mc-behavior.md has been edited..."},
    }
    n3m._notices_write(notices)
    r = n3m._ensure_behavior_md(str(ws))
    assert r == "current"
    after = n3m._notices_read()
    assert "behavior_md_edited:oldkey1" not in after
    assert "behavior_md_edited:other" in after


def test_C4_special_chars_in_partner_db_path(monkeypatch, tmp_path, capsys):
    root = tmp_path / "partner #1 (test)"
    p = _partner_db(root)
    cfg = dict(n3m.get_config(), connect_server_port=59999, connect_server_root=str(root))
    monkeypatch.setattr(n3m, "_CFG_CACHE", cfg)
    rc = n3m.cmd_show_turn("T1")
    assert rc == 0
    out = capsys.readouterr().out
    assert "partner row" in out


def test_stop_with_directory_argument(tmp_path):
    """--stop <dir> accepts target directory as CLI argument without reading stdin."""
    target_dir = tmp_path / "custom_project"
    target_dir.mkdir()
    rc = n3m.main(["--stop", str(target_dir)])
    assert rc == 0
    behavior_file = target_dir / ".agents" / "rules" / "n3mc-behavior.md"
    assert behavior_file.exists()
    assert behavior_file.read_text(encoding="utf-8").startswith("<!-- n3mc-free-antigravity-behavior v3 -->")


def test_housekeeping_cleans_turn_pending_and_turn_key(tmp_path, monkeypatch):
    """_housekeeping cleans 30-day old turn_id, turn_pending, and turn_key files."""
    import time
    old_time = time.time() - 31 * 86400
    for prefix in ("turn_id_old", "turn_pending_old", "turn_key_old", "turn_id", "turn_key", "turn_pending"):
        p = os.path.join(n3m.MEMORY_DIR, f"{prefix}.txt")
        with open(p, "w", encoding="utf-8") as f:
            f.write("test")
        os.utime(p, (old_time, old_time))
    
    # Also create new ones that should stay
    fresh_time = time.time()
    for prefix in ("turn_id_new", "turn_pending_new", "turn_key_new"):
        p = os.path.join(n3m.MEMORY_DIR, f"{prefix}.txt")
        with open(p, "w", encoding="utf-8") as f:
            f.write("test")
        os.utime(p, (fresh_time, fresh_time))
        
    n3m._housekeeping()
    
    # Old ones deleted
    for prefix in ("turn_id_old", "turn_pending_old", "turn_key_old", "turn_id", "turn_key", "turn_pending"):
        assert not os.path.exists(os.path.join(n3m.MEMORY_DIR, f"{prefix}.txt"))
    # New ones preserved
    for prefix in ("turn_id_new", "turn_pending_new", "turn_key_new"):
        assert os.path.exists(os.path.join(n3m.MEMORY_DIR, f"{prefix}.txt"))


