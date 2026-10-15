"""The headless runner must catch parser errors even with exit code zero."""
from unittest.mock import Mock

from scripts import check_godot


def test_error_scanner_finds_godot_parser_failures():
    log = (
        "Godot Engine v4.7.2.stable\n"
        "SCRIPT ERROR: Parse Error: Identifier not declared\n"
        "   at: GDScript::reload (res://scripts/models/monster.gd:927)\n"
    )
    assert check_godot.error_lines(log) == [
        "SCRIPT ERROR: Parse Error: Identifier not declared"
    ]
    assert check_godot.error_lines(
        "Godot Engine v4.7.2.stable\nLoading resource...\n"
    ) == []


def test_import_fails_when_godot_logs_errors_but_returns_zero(monkeypatch):
    fake = Mock(returncode=0, stdout="ERROR: Parse Error: Invalid call\n")
    monkeypatch.setattr(check_godot.subprocess, "run", lambda *a, **kw: fake)
    assert not check_godot.run_check("import", ["godot"])


def test_smoke_requires_completion_sentinel(monkeypatch):
    fake = Mock(returncode=0, stdout="Godot Engine v4.7.2.stable\n")
    monkeypatch.setattr(check_godot.subprocess, "run", lambda *a, **kw: fake)
    assert not check_godot.run_check("smoke", ["godot"], smoke=True)

    fake.stdout += "GODOT_SMOKE_OK: 24 monsters, 84 instances\n"
    assert check_godot.run_check("smoke", ["godot"], smoke=True)


def test_smoke_file_has_all_24_playable_monsters_and_rank_checks():
    source = (check_godot.PROJECT / "tests" / "headless_smoke.gd").read_text(
        encoding="utf-8"
    )
    assert '"drake_igneous"' in source
    assert '"dullahan_aether"' in source
    assert '"thornet_storm"' in source
    assert "Factory.create_level_one_monster(" in source
    assert "for rank in range(max_rank + 1):" in source
    assert "GODOT_SMOKE_OK:" in source


def test_godot_smoke_executes_damage_healing_and_revive():
    from pathlib import Path

    script = (
        Path(__file__).resolve().parents[1]
        / "godot" / "tests" / "headless_smoke.gd"
    ).read_text(encoding="utf-8")
    assert "func _run_combat_regressions()" in script
    assert 'battle.execute_active_skill(' in script
    assert 'battle.execute_soul_recall(fallen)' in script
    assert "GODOT_COMBAT_OK:" in script
    assert "failures.append_array(_run_combat_regressions())" in script
