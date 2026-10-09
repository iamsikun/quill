from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
import yaml

from .assembly import assemble_paper, camera_ready
from .importer import import_paper
from .workspace import clear_session, create_journal_version, log_decision, new_paper, set_target, sync_context
from .skills import install_skill, skill_destinations, uninstall_skill
from .migration import migrate_project
from .sync import find_repo_root, init_project, package_version
from .validate import validate_repo
from .doctor import diagnose, format_diagnosis


def _repo_root() -> Path:
    return find_repo_root(Path.cwd())


def _print_conflicts(conflicts: list[str]) -> None:
    print("conflicts detected in managed files:")
    for relative in conflicts:
        print(f"  - {relative}")


def _cmd_skill(args: argparse.Namespace) -> int:
    result = install_skill(_repo_root(), host=args.host, scope=args.scope, sync=args.skill_action == "sync",
                           dry_run=args.dry_run, diff=args.diff)
    if args.dry_run or args.diff:
        for change in result.planned_changes:
            print(f"would {change}")
        for difference in result.diffs:
            print(difference, end="" if difference.endswith("\n") else "\n")
        print("Preview only; no files changed.")
    if result.conflicts:
        _print_conflicts(result.conflicts)
        print("No skill files changed. Preserve or resolve local changes before retrying.")
        return 1
    if args.dry_run or args.diff:
        return 0
    for name, destination in skill_destinations(_repo_root(), host=args.host, scope=args.scope).items():
        print(f"{name}: {destination}")
    print(f"skill ready ({len(result.written_files)} files changed)")
    return 0


def _cmd_skill_uninstall(args: argparse.Namespace) -> int:
    result = uninstall_skill(_repo_root(), host=args.host, scope=args.scope, dry_run=args.dry_run, diff=args.diff)
    if args.dry_run or args.diff:
        for change in result.planned_changes:
            print(f"would {change}")
        for difference in result.diffs:
            print(difference, end="" if difference.endswith("\n") else "\n")
        print("Preview only; no files changed.")
    if result.conflicts:
        _print_conflicts(result.conflicts)
        print("No skill files removed. Preserve or resolve local changes before retrying.")
        return 1
    if args.dry_run or args.diff:
        return 0
    for path in result.written_files:
        print(f"removed: {path}")
    print(f"skill uninstalled ({len(result.written_files)} files removed)")
    return 0


def _cmd_init(_: argparse.Namespace) -> int:
    result = init_project(_repo_root())
    if result.conflicts:
        _print_conflicts(result.conflicts)
        return 1
    print(f"project assets ready ({len(result.written_files)} new files); existing files preserved")
    return 0


def _cmd_migrate(args: argparse.Namespace) -> int:
    result = migrate_project(_repo_root(), dry_run=args.dry_run)
    prefix = "would " if args.dry_run else ""
    for path in result.removed_files:
        print(f"{prefix}remove: {path}")
    for path in result.updated_files:
        print(f"{prefix}update: {path}")
    if result.conflicts:
        _print_conflicts(result.conflicts)
        print("Conflicting files were left unchanged; review them manually.")
        return 1
    if not result.removed_files and not result.updated_files:
        print("no legacy adapters to remove")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    repo_root = _repo_root()
    result = validate_repo(repo_root, target_name=args.target)
    for warning in result.warnings:
        print(f"WARN: {warning}")
    for error in result.errors:
        print(f"ERROR: {error}")
    if result.ok:
        print("validation passed (static checks; compilation not performed)")
        return 0
    print("validation failed")
    return 1


def _cmd_version(_: argparse.Namespace) -> int:
    print(f"package version: {package_version()}")
    return 0


def _cmd_doctor(args: argparse.Namespace) -> int:
    report = diagnose(_repo_root())
    print(json.dumps(report, indent=2) if args.json else format_diagnosis(report))
    return 1 if report['issues'] else 0


def _cmd_new_paper(args: argparse.Namespace) -> int:
    repo_root = _repo_root()
    target = new_paper(
        repo_root,
        title=args.title,
        topic=args.topic,
        contributions=args.contribution,
        venue_key=args.venue,
        paper_type=args.paper_type,
        target_name=args.target,
    )
    print(f"initialized paper workspace for target '{target}'")
    print("use the Quill skill in your host to draft or revise the manuscript")
    return 0


def _cmd_import_paper(args: argparse.Namespace) -> int:
    repo_root = _repo_root()
    target = import_paper(
        repo_root,
        source=Path(args.source),
        title=args.title,
        topic=args.topic,
        contributions=args.contribution,
        venue_key=args.venue,
        paper_type=args.paper_type,
        import_mode=args.import_mode,
        target_name=args.target,
        source_root=Path(args.source_root) if args.source_root else None,
    )
    print(f"imported paper into target '{target}'")
    print("use the Quill skill to revise the imported manuscript")
    return 0


def _cmd_set_target(args: argparse.Namespace) -> int:
    metadata = set_target(_repo_root(), args.target)
    print(f"active target switched to '{args.target}' (stage: {metadata.get('stage', 'unknown')})")
    return 0


def _cmd_create_journal_version(args: argparse.Namespace) -> int:
    create_journal_version(_repo_root(), venue_key=args.venue, activate=args.activate)
    print(f"created journal target for venue '{args.venue}'")
    if args.activate:
        print("journal is now the active target")
    return 0


def _cmd_assemble(args: argparse.Namespace) -> int:
    main_path = assemble_paper(_repo_root(), compile_pdf=args.compile, target_name=args.target)
    print(f"assembled paper at {main_path}")
    return 0


def _cmd_camera_ready(args: argparse.Namespace) -> int:
    zip_path = camera_ready(_repo_root(), compile_pdf=args.compile, target_name=args.target)
    print(f"created submission archive at {zip_path}")
    return 0


def _cmd_sync_context(args: argparse.Namespace) -> int:
    path = sync_context(_repo_root(), target_name=args.target)
    print(f"updated context at {path}")
    return 0


def _cmd_log_decision(args: argparse.Namespace) -> int:
    path = log_decision(_repo_root(), args.text)
    print(f"logged decision to {path}")
    return 0


def _cmd_clear_session(args: argparse.Namespace) -> int:
    path = clear_session(_repo_root())
    print(f"cleared session log at {path}")
    return 0


def _add_common_metadata_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--title", required=True, help="Working paper title")
    parser.add_argument("--topic", default="", help="Optional topic description")
    parser.add_argument("--contribution", action="append", default=[], help="Optional; repeat for each contribution")
    parser.add_argument("--venue", default="generic", help="Venue key from .quill/config.yaml; default: generic")
    parser.add_argument("--paper-type", default="", help="Optional manuscript type")
    parser.add_argument("--target", help="New target name; defaults to manuscript, conference, or journal")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="quill")
    subparsers = parser.add_subparsers(dest="command", required=True)

    skill_parser = subparsers.add_parser(
        "skill", help="Copy the writing skill into a project (or user folder) without auto-updates")
    skill_actions = skill_parser.add_subparsers(dest="skill_action", required=True)
    for action in ("install", "sync", "uninstall"):
        action_parser = skill_actions.add_parser(action)
        action_parser.add_argument("--host", choices=("codex", "claude", "all"), default="all")
        action_parser.add_argument("--scope", choices=("user", "project"), default="user")
        action_parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing files")
        action_parser.add_argument("--diff", action="store_true", help="Show proposed diffs; implies --dry-run")
        action_parser.set_defaults(func=_cmd_skill_uninstall if action == "uninstall" else _cmd_skill)

    init_parser = subparsers.add_parser("init", help="Add missing optional project configuration and templates")
    init_parser.set_defaults(func=_cmd_init)

    migration_parser = subparsers.add_parser("migrate", help="Remove unchanged, owned legacy adapters")
    migration_parser.add_argument("--dry-run", action="store_true", help="Preview without changing files")
    migration_parser.set_defaults(func=_cmd_migrate)

    validate_parser = subparsers.add_parser("validate", help="Validate an optional managed manuscript project")
    validate_parser.add_argument("--target", help="Check one target; default: every declared target")
    validate_parser.set_defaults(func=_cmd_validate)

    version_parser = subparsers.add_parser("version", help="Show the installed package version")
    version_parser.set_defaults(func=_cmd_version)

    doctor_parser = subparsers.add_parser("doctor", help="Inspect installations, update health, and optional dependencies")
    doctor_parser.add_argument("--json", action="store_true", help="Return machine-readable diagnostics")
    doctor_parser.set_defaults(func=_cmd_doctor)

    new_parser = subparsers.add_parser("new-paper", help="Initialize a new paper workspace")
    _add_common_metadata_arguments(new_parser)
    new_parser.set_defaults(func=_cmd_new_paper)

    import_parser = subparsers.add_parser("import-paper", help="Import an existing LaTeX project")
    import_parser.add_argument("source", help="Path to a TeX file or directory")
    import_parser.add_argument("--source-root", help="Compilation root containing the entry point and its dependencies")
    import_parser.add_argument("--import-mode", default="review", choices=("review", "revise", "retarget"))
    _add_common_metadata_arguments(import_parser)
    import_parser.set_defaults(func=_cmd_import_paper)

    set_target_parser = subparsers.add_parser("set-target", help="Switch the active paper target")
    set_target_parser.add_argument("target", help="Target name such as conference or journal")
    set_target_parser.set_defaults(func=_cmd_set_target)

    journal_parser = subparsers.add_parser("create-journal-version", help="Create a journal target")
    journal_parser.add_argument("venue", help="Non-ML venue key from .quill/config.yaml")
    journal_parser.add_argument("--activate", action="store_true", help="Activate the journal target after creation")
    journal_parser.set_defaults(func=_cmd_create_journal_version)

    assemble_parser = subparsers.add_parser("assemble", help="Assemble main.tex deterministically")
    assemble_parser.add_argument("--target", help="Override the active target")
    assemble_parser.add_argument("--compile", action="store_true", help="Run pdflatex/bibtex after writing main.tex")
    assemble_parser.set_defaults(func=_cmd_assemble)

    sync_context_parser = subparsers.add_parser("sync-context", help="Update context.md from actual .tex files")
    sync_context_parser.add_argument("--target", help="Override the active target")
    sync_context_parser.set_defaults(func=_cmd_sync_context)

    log_decision_parser = subparsers.add_parser("log-decision", help="Append an editorial decision to the session log")
    log_decision_parser.add_argument("text", help="Decision text to log")
    log_decision_parser.set_defaults(func=_cmd_log_decision)

    clear_session_parser = subparsers.add_parser("clear-session", help="Clear the session decisions log")
    clear_session_parser.set_defaults(func=_cmd_clear_session)

    camera_parser = subparsers.add_parser("camera-ready", help="Build the camera-ready package")
    camera_parser.add_argument("--target", help="Override the active target")
    camera_parser.add_argument("--compile", action="store_true", help="Compile the camera-ready directory before zipping")
    camera_parser.set_defaults(func=_cmd_camera_ready)

    return parser


REMOVED_COMMANDS = {
    "install": "quill skill install (skill) or quill init (project assets)",
    "sync": "quill skill sync",
    "dev-sync-root": "edit skills/quill directly; there are no generated adapters",
    **dict.fromkeys(
        ("workflow-brief", "literature-search", "draft-paper", "draft-section",
         "edit-section", "review-paper", "revise-paper", "polish"),
        "use the Quill writing skill in your host ($quill in Codex, /quill in Claude); "
        "standalone literature search is outside Quill's scope",
    ),
}


def main(argv: list[str] | None = None) -> None:
    arguments = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    if arguments and arguments[0] in REMOVED_COMMANDS:
        parser.error(f"'{arguments[0]}' was removed in Quill 0.2; {REMOVED_COMMANDS[arguments[0]]}")
    args = parser.parse_args(arguments)
    try:
        status = args.func(args)
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as exc:
        print(f"quill: {exc}", file=sys.stderr)
        status = 1
    sys.exit(status)
