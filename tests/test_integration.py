import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def run(cwd: Path, *args: str):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT)
    return subprocess.run(
        [sys.executable, "-m", "symlegion", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
    )


def test_help_explains_config_lookup_and_modes(tmp_path: Path):
    p = run(tmp_path, "--help")
    assert p.returncode == 0
    assert "Config lookup:" in p.stdout
    assert "with --config: use that YAML file" in p.stdout
    assert (
        "direct mode: relative source and links resolve from the YAML file folder"
        in p.stdout
    )
    assert (
        "recursive mode: source and links stay relative to each matched project root"
        in p.stdout
    )

    p = run(tmp_path, "sync", "--help")
    assert p.returncode == 0
    assert "Recursive mode notes:" in p.stdout
    assert "depth defaults to 5" in p.stdout

    p = run(tmp_path, "init", "--help")
    assert p.returncode == 0
    assert "The generated config includes starter mappings for:" in p.stdout
    assert (
        ".opencode/commands -> .claude/commands, .pi/prompts, .goose/recipes"
        in p.stdout
    )


def test_init_sync_check_clean(tmp_path: Path):
    (tmp_path / ".git").mkdir()

    p = run(tmp_path, "init")
    assert p.returncode == 0
    assert (tmp_path / ".symlegion.yaml").exists()
    config_text = (tmp_path / ".symlegion.yaml").read_text(encoding="utf-8")
    assert "mode: direct" in config_text
    assert "mode: recursive" in config_text
    assert "source: AGENTS.md" in config_text
    assert "- CLAUDE.md" in config_text
    assert "- .claude/CLAUDE.md" in config_text
    assert "- .goosehints" in config_text
    assert "source: .opencode/commands/" in config_text
    assert "- .claude/commands/" in config_text
    assert "- .pi/prompts/" in config_text
    assert "- .goose/recipes/" in config_text

    p = run(tmp_path, "check")
    assert p.returncode == 1

    (tmp_path / "AGENTS.md").write_text("hello", encoding="utf-8")
    (tmp_path / ".opencode" / "commands").mkdir(parents=True)
    p = run(tmp_path, "sync")
    assert p.returncode == 0
    assert "[create]" in p.stdout

    for link in ["CLAUDE.md", ".claude/CLAUDE.md", ".goosehints"]:
        assert (tmp_path / link).is_symlink()
    for link in [".claude/commands", ".pi/prompts", ".goose/recipes"]:
        assert (tmp_path / link).is_symlink()

    p = run(tmp_path, "check")
    assert p.returncode == 0
    assert "All links are correctly configured" in p.stdout

    p = run(tmp_path, "--dry-run", "clean")
    assert p.returncode == 0
    assert "would remove" in p.stdout


def test_sync_uses_explicit_config_file(tmp_path: Path):
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    custom_config = config_dir / "custom.yaml"
    custom_config.write_text(
        """- source: ../shared/AGENTS.md
  links:
    - ../repo/CLAUDE.md
""",
        encoding="utf-8",
    )

    source = tmp_path / "shared" / "AGENTS.md"
    source.parent.mkdir()
    source.write_text("hello", encoding="utf-8")

    p = run(tmp_path, "--config", str(custom_config), "sync")
    assert p.returncode == 0
    assert (tmp_path / "repo" / "CLAUDE.md").is_symlink()

    p = run(tmp_path, "--config", str(custom_config), "check")
    assert p.returncode == 0
    assert str(source) in p.stdout


def test_sync_multiple_groups_with_directory_source(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    (tmp_path / "bundle").mkdir()
    (tmp_path / "bundle" / "rules.md").write_text("hi", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text("hello", encoding="utf-8")
    (tmp_path / ".symlegion.yaml").write_text(
        """- source: CLAUDE.md
  links:
    - AGENTS.md
- source: bundle
  links:
    - .ai/rules
""",
        encoding="utf-8",
    )

    p = run(tmp_path, "sync")
    assert p.returncode == 0
    assert (tmp_path / "AGENTS.md").is_symlink()
    assert (tmp_path / ".ai" / "rules").is_symlink()

    p = run(tmp_path, "check")
    assert p.returncode == 0
    assert p.stdout.count("Source:") == 2


def test_recursive_sync_creates_links_and_warns_for_missing_search_path(tmp_path: Path):
    existing_root = tmp_path / "workspace"
    repo_root = existing_root / "client" / "project"
    source_dir = repo_root / ".opencode" / "commands"
    source_dir.mkdir(parents=True)
    (source_dir / "prompt.md").write_text("hello", encoding="utf-8")

    missing_root = tmp_path / "missing"

    (tmp_path / ".symlegion.yaml").write_text(
        f"""- mode: recursive
  source: .opencode/commands
  links:
    - .claude/commands
    - .pi/prompts
  search:
    - {missing_root}
    - {existing_root}
  depth: 3
""",
        encoding="utf-8",
    )

    p = run(tmp_path, "sync")
    assert p.returncode == 0
    assert "Search path does not exist" in p.stderr
    assert (repo_root / ".claude" / "commands").is_symlink()
    assert (repo_root / ".pi" / "prompts").is_symlink()

    p = run(tmp_path, "check")
    assert p.returncode == 0
    assert "Search path does not exist" in p.stderr
    assert str(repo_root / ".opencode" / "commands") in p.stdout


def test_recursive_sync_resolves_relative_search_paths_from_config_dir(tmp_path: Path):
    config_dir = tmp_path / "configs"
    config_dir.mkdir()

    search_root = tmp_path / "workspace"
    repo_root = search_root / "client" / "project"
    source_dir = repo_root / ".opencode" / "commands"
    source_dir.mkdir(parents=True)
    (source_dir / "prompt.md").write_text("hello", encoding="utf-8")

    (config_dir / ".symlegion.yaml").write_text(
        """- mode: recursive
  source: .opencode/commands
  links:
    - .claude/commands
  search:
    - ../workspace
""",
        encoding="utf-8",
    )

    p = run(config_dir, "sync")
    assert p.returncode == 0
    assert (repo_root / ".claude" / "commands").is_symlink()
