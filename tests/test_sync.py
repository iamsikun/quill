from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import yaml

from quill.assembly import assemble_paper, camera_ready
from quill.workspace import clear_session, create_journal_version, log_decision, new_paper, set_target
from quill.sync import find_repo_root, init_project
from quill.validate import validate_repo
from quill.importer import import_paper
from quill.workspace import sync_context


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    return repo


def test_find_repo_root_walks_up(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    nested = repo / "a" / "b"
    nested.mkdir(parents=True)
    assert find_repo_root(nested) == repo


def test_find_managed_workspace_without_git(tmp_path: Path) -> None:
    init_project(tmp_path)
    nested = tmp_path / "paper/conference/sections"
    nested.mkdir(parents=True)
    assert find_repo_root(nested) == tmp_path


def test_legacy_pepper_workspace_keeps_config_and_templates(tmp_path: Path) -> None:
    init_project(tmp_path)
    (tmp_path / ".quill").rename(tmp_path / ".pepper")
    config = tmp_path / ".pepper/config.yaml"
    config.write_text(config.read_text() + "\n# Local configuration\n")
    original = config.read_bytes()
    custom_template = tmp_path / ".pepper/templates/neurips/local.sty"
    custom_template.write_text("% Custom venue style\n")

    assert not init_project(tmp_path).written_files
    assert config.read_bytes() == original
    assert not (tmp_path / ".quill").exists()
    new_paper(tmp_path, title="Legacy paper", topic="Topic", contributions=["Claim"],
              venue_key="neurips", paper_type="Theory")
    nested = tmp_path / "paper/conference/sections"
    assert find_repo_root(nested) == tmp_path
    main = assemble_paper(tmp_path)
    assert ".pepper/templates/neurips" in main.read_text()
    assert validate_repo(tmp_path).ok
    camera_ready(tmp_path)
    assert (tmp_path / "paper/conference/camera-ready/local.sty").read_bytes() == custom_template.read_bytes()


def test_quill_config_takes_precedence_when_both_exist(tmp_path: Path) -> None:
    from quill.sync import project_assets_dir
    init_project(tmp_path)
    legacy = tmp_path / ".pepper"
    legacy.mkdir()
    (legacy / "config.yaml").write_text("unrelated: preserved\n")
    assert project_assets_dir(tmp_path) == tmp_path / ".quill"
    assert not init_project(tmp_path).written_files
    assert (legacy / "config.yaml").read_text() == "unrelated: preserved\n"


def test_init_preserves_config_and_needs_no_adapters(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    result = init_project(repo)
    assert not result.conflicts
    assert validate_repo(repo).ok
    assert not (repo / "AGENTS.md").exists()
    assert not (repo / ".claude").exists()
    assert not (repo / ".agents").exists()
    config = repo / ".quill/config.yaml"
    config.write_text("custom: true\n")
    assert not init_project(repo).written_files
    assert config.read_text() == "custom: true\n"


def test_new_paper_creates_workspace_and_context(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    init_project(repo)
    (repo / "docs").mkdir()
    (repo / "src").mkdir()

    target = new_paper(
        repo,
        title="Optimal Pricing with LLMs",
        topic="We study dynamic pricing with language-model-assisted demand inference.",
        contributions=["A new demand estimator", "A policy regret bound"],
        venue_key="neurips",
        paper_type="Theory+Experiments",
    )

    assert target == "conference"
    state = yaml.safe_load((repo / "paper/state.yaml").read_text(encoding="utf-8"))
    assert state["active_target"] == "conference"
    assert (repo / "paper/conference/target.yaml").exists()
    context = (repo / "paper/shared/context.md").read_text(encoding="utf-8")
    assert "Optimal Pricing with LLMs" in context
    assert "Documentation: docs" in context


def test_set_target_and_create_journal_version(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    init_project(repo)
    new_paper(
        repo,
        title="Paper",
        topic="Topic",
        contributions=["One"],
        venue_key="neurips",
        paper_type="Theory",
    )
    create_journal_version(repo, venue_key="econometrica", activate=True)
    metadata = set_target(repo, "journal")
    assert metadata["venue"] == "econometrica"
    state = yaml.safe_load((repo / "paper/state.yaml").read_text(encoding="utf-8"))
    assert state["active_target"] == "journal"


def test_assemble_and_camera_ready_generate_outputs(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    init_project(repo)
    new_paper(
        repo,
        title="Paper",
        topic="Topic",
        contributions=["One"],
        venue_key="neurips",
        paper_type="Theory",
    )
    sections = repo / "paper/conference/sections"
    (sections / "abstract.tex").write_text("A concise abstract.\n", encoding="utf-8")
    (sections / "introduction.tex").write_text("\\section{Introduction}\nIntro.\n", encoding="utf-8")
    (sections / "methodology.tex").write_text("\\section{Method}\nMethod.\n", encoding="utf-8")
    (repo / "paper/conference/references.bib").write_text("", encoding="utf-8")

    main_path = assemble_paper(repo)
    assert main_path.exists()
    assert "\\input{sections/introduction}" in main_path.read_text(encoding="utf-8")

    zip_path = camera_ready(repo)
    assert zip_path.exists()
    assert (repo / "paper/conference/camera-ready/VERIFICATION.md").exists()


def test_session_log_lifecycle(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    init_project(repo)
    new_paper(
        repo,
        title="Paper",
        topic="Topic",
        contributions=["One"],
        venue_key="neurips",
        paper_type="Theory",
    )
    # Log decisions
    path = log_decision(repo, "removed tier analysis")
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "removed tier analysis" in text
    assert "Session Decisions Log" in text

    log_decision(repo, "renamed DGPs to descriptive names")
    text = path.read_text(encoding="utf-8")
    assert "renamed DGPs" in text
    assert text.count("- [") == 2  # two entries

    # Clear session
    path = clear_session(repo)
    text = path.read_text(encoding="utf-8")
    assert "Session Decisions Log" in text
    assert "removed tier" not in text


def test_python_module_version_command() -> None:
    env = {**os.environ, "PYTHONPATH": "src"}
    completed = subprocess.run(
        [sys.executable, "-m", "quill", "version"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert completed.returncode == 0
    assert "package version:" in completed.stdout


def test_import_and_context_sync(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    init_project(repo)
    source = tmp_path / "manuscript.tex"
    source.write_text("\\documentclass{article}\n\\begin{document}\n"
                      "\\section{Introduction}\nEvidence.\\label{sec:intro}\n\\end{document}\n")
    target = import_paper(repo, source=source, title="Example", topic="Topic",
                          contributions=["Supported claim"], venue_key="neurips", paper_type="Empirical")
    assert target == "conference"
    context = sync_context(repo).read_text()
    assert "manuscript.tex" in context
    assert (repo / "paper/conference/manuscript.tex").read_bytes() == source.read_bytes()
    assert validate_repo(repo).ok
