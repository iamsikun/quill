#!/usr/bin/env bash
# Quill installer: one install that stays current.
#
#   curl -fsSL https://raw.githubusercontent.com/iamsikun/quill/stable/install.sh | bash
#
# Commands:
#   install.sh [install] [--no-auto-update] [--no-cli]
#                          clone, link into every detected agent, install the quill CLI
#                          with uv, and schedule daily updates
#   install.sh update      fast-forward to the latest stable release (run by the scheduler)
#   install.sh status      show installed version, links, CLI, and last update
#   install.sh uninstall   remove links, the CLI, the scheduled job, and the clone
#
# Environment overrides:
#   QUILL_HOME  where the clone lives            (default: ~/.local/share/quill)
#   QUILL_REF   branch or tag to track           (default: stable)
#   QUILL_REPO  git URL to clone from            (default: https://github.com/iamsikun/quill.git)

set -euo pipefail

QUILL_HOME="${QUILL_HOME:-$HOME/.local/share/quill}"
QUILL_REF="${QUILL_REF:-stable}"
QUILL_REPO="${QUILL_REPO:-https://github.com/iamsikun/quill.git}"
STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/quill"
LOG_FILE="$STATE_DIR/update.log"
LAUNCHD_LABEL="io.github.iamsikun.quill.update"
LAUNCHD_PLIST="$HOME/Library/LaunchAgents/$LAUNCHD_LABEL.plist"
CRON_MARKER="# quill-auto-update"
CLI_STATE="$STATE_DIR/cli"   # path of the uv that installed the CLI; present only if we own it
CLI_METADATA="$STATE_DIR/cli-metadata"  # fingerprint of the last successfully installed pyproject.toml
LAST_ERROR="$STATE_DIR/last-error"
CLONE_STATE="$STATE_DIR/clone"

say() { printf 'quill: %s\n' "$*"; }
die() { printf 'quill: error: %s\n' "$*" >&2; exit 1; }

skill_src() { printf '%s/skills/quill' "$QUILL_HOME"; }

# Skill directories of agents that appear to be installed. ~/.agents/skills is the
# shared location read by Codex, Gemini CLI, and Cursor.
agent_skill_dirs() {
  [ -d "$HOME/.claude" ] && printf '%s\n' "$HOME/.claude/skills"
  if [ -d "$HOME/.agents" ] || [ -d "$HOME/.codex" ] || [ -d "$HOME/.gemini" ] || [ -d "$HOME/.cursor" ]; then
    printf '%s\n' "$HOME/.agents/skills"
  fi
  [ -d "$HOME/.copilot" ] && printf '%s\n' "$HOME/.copilot/skills"
  [ -d "$HOME/.config/opencode" ] && printf '%s\n' "$HOME/.config/opencode/skills"
  return 0
}

installed_version() {
  sed -n 's/^  version: "\(.*\)"$/\1/p' "$(skill_src)/SKILL.md" 2>/dev/null | head -n1
}

link_skill() {
  local found=0 dir target
  while IFS= read -r dir; do
    [ -n "$dir" ] || continue
    found=1
    target="$dir/quill"
    mkdir -p "$dir"
    if [ -L "$target" ]; then
      if [ "$(readlink "$target")" = "$(skill_src)" ]; then
        say "linked $target"
      else
        say "kept $target (symlink owned elsewhere: $(readlink "$target"))"
      fi
    elif [ -f "$target/.quill-install.json" ]; then
      say "skipped $target (a copy from 'quill skill install'; run 'quill skill uninstall --scope user', then reinstall)"
    elif [ -e "$target" ]; then
      say "skipped $target (already exists and is not a symlink; remove it to let Quill manage it)"
    else
      ln -s "$(skill_src)" "$target"
      say "linked $target"
    fi
  done < <(agent_skill_dirs)
  if [ "$found" -eq 0 ]; then
    say "no supported agent detected; link manually, e.g.:"
    say "  ln -s $(skill_src) ~/.claude/skills/quill"
  fi
  # Earlier versions copied the Codex skill into $CODEX_HOME/skills. Codex would then
  # list Quill twice, so point at the cleanup rather than deleting a copy we don't own.
  local legacy="${CODEX_HOME:-$HOME/.codex}/skills/quill"
  if [ -e "$legacy" ] && [ ! -L "$legacy" ]; then
    say "note: $legacy is an older copy; remove it with 'quill skill uninstall --host codex --scope user'"
  fi
}

unlink_skill() {
  local dir target
  for dir in "$HOME/.claude/skills" "$HOME/.agents/skills" "$HOME/.copilot/skills" "$HOME/.config/opencode/skills"; do
    target="$dir/quill"
    if [ -L "$target" ] && [ "$(readlink "$target")" = "$(skill_src)" ]; then
      rm "$target"
      say "removed $target"
    fi
  done
}

# The scheduler runs with a minimal PATH, so also look where uv's installers put it.
find_uv() {
  local candidate
  for candidate in "$(command -v uv 2>/dev/null)" "$HOME/.local/bin/uv" "$HOME/.cargo/bin/uv" \
                   /opt/homebrew/bin/uv /usr/local/bin/uv; do
    [ -n "$candidate" ] && [ -x "$candidate" ] && { printf '%s\n' "$candidate"; return 0; }
  done
  return 1
}

metadata_fingerprint() { git -C "$QUILL_HOME" hash-object pyproject.toml; }

record_error() {
  mkdir -p "$STATE_DIR"
  printf '%s\n' "$*" > "$LAST_ERROR"
  say "$*"
}

cli_owned() {
  local receipt
  receipt="$("$1" tool dir)/quill/uv-receipt.toml"
  [ -f "$receipt" ] && grep -qF "editable = \"$QUILL_HOME\"" "$receipt"
}

record_cli_success() {
  mkdir -p "$STATE_DIR"
  printf '%s\n' "$1" > "$CLI_STATE"
  metadata_fingerprint > "$CLI_METADATA"
  rm -f "$LAST_ERROR"
}

# Editable install from the clone, so each update reaches the CLI with no extra step.
install_cli() {
  local uv receipt
  if ! uv="$(find_uv)"; then
    say "uv not found; skipped the quill CLI (install uv from https://docs.astral.sh/uv/, then rerun install.sh)"
    return 0
  fi
  receipt="$("$uv" tool dir)/quill/uv-receipt.toml"
  if [ -f "$receipt" ] && ! cli_owned "$uv"; then
    say "kept the existing quill CLI, which was installed from elsewhere (see 'uv tool list')"
    return 0
  fi
  if ! "$uv" tool install --quiet --reinstall --editable "$QUILL_HOME"; then
    record_error "could not install the quill CLI; rerun install.sh to retry; the skill works without it"
    return 0
  fi
  record_cli_success "$uv"
  say "installed the quill CLI with uv"
  local bin
  bin="$("$uv" tool dir --bin)"
  case ":$PATH:" in
    *":$bin:"*) ;;
    *) say "add $bin to your PATH to run 'quill'" ;;
  esac
}

# Reinstalling refreshes the package metadata (version, dependencies, entry points).
refresh_cli() {
  [ -f "$CLI_STATE" ] || return 0
  local uv receipt
  uv="$(cat "$CLI_STATE")"
  [ -x "$uv" ] || uv="$(find_uv)" || { record_error "uv not found; quill CLI refresh pending"; return 1; }
  receipt="$("$uv" tool dir)/quill/uv-receipt.toml"
  if [ -f "$receipt" ] && ! cli_owned "$uv"; then
    record_error "quill CLI receipt no longer belongs to $QUILL_HOME; kept the external installation"
    return 1
  fi
  if [ -f "$receipt" ] && [ -f "$CLI_METADATA" ] && [ "$(cat "$CLI_METADATA")" = "$(metadata_fingerprint)" ]; then
    return 0
  fi
  if "$uv" tool install --quiet --reinstall --editable "$QUILL_HOME"; then
    record_cli_success "$uv"
    say "refreshed the quill CLI"
  else
    record_error "could not refresh the quill CLI; next update will retry"
    return 1
  fi
}

uninstall_cli() {
  [ -f "$CLI_STATE" ] || return 0
  local uv
  uv="$(cat "$CLI_STATE")"
  [ -x "$uv" ] || uv="$(find_uv)" || { die "uv not found; remove the CLI with 'uv tool uninstall quill' before uninstalling"; }
  if cli_owned "$uv"; then
    "$uv" tool uninstall quill >/dev/null 2>&1 || die "could not uninstall the CLI; kept the clone and ownership state"
    say "removed the quill CLI"
  else
    say "kept the quill CLI installed elsewhere"
  fi
  rm -f "$CLI_STATE" "$CLI_METADATA"
}

schedule_updates() {
  local script="$QUILL_HOME/install.sh"
  mkdir -p "$STATE_DIR"
  case "$(uname -s)" in
    Darwin)
      mkdir -p "$(dirname "$LAUNCHD_PLIST")"
      cat > "$LAUNCHD_PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LAUNCHD_LABEL</string>
  <key>ProgramArguments</key>
  <array><string>/bin/bash</string><string>$script</string><string>update</string></array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>QUILL_HOME</key><string>$QUILL_HOME</string>
    <key>QUILL_REF</key><string>$QUILL_REF</string>
  </dict>
  <key>StartInterval</key><integer>86400</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>$LOG_FILE</string>
  <key>StandardErrorPath</key><string>$LOG_FILE</string>
</dict>
</plist>
EOF
      launchctl bootout "gui/$(id -u)/$LAUNCHD_LABEL" 2>/dev/null || true
      launchctl bootstrap "gui/$(id -u)" "$LAUNCHD_PLIST"
      say "daily updates scheduled (launchd: $LAUNCHD_LABEL)"
      ;;
    Linux)
      command -v crontab >/dev/null || { say "crontab not found; run '$script update' to update manually"; return 0; }
      local line="17 9 * * * QUILL_HOME='$QUILL_HOME' QUILL_REF='$QUILL_REF' /bin/bash '$script' update >>'$LOG_FILE' 2>&1 $CRON_MARKER"
      { crontab -l 2>/dev/null | grep -v "$CRON_MARKER" || true; printf '%s\n' "$line"; } | crontab -
      say "daily updates scheduled (cron)"
      ;;
    *)
      say "automatic updates not supported on this OS; run '$script update' to update manually"
      ;;
  esac
}

unschedule_updates() {
  if [ -f "$LAUNCHD_PLIST" ]; then
    launchctl bootout "gui/$(id -u)/$LAUNCHD_LABEL" 2>/dev/null || true
    rm -f "$LAUNCHD_PLIST"
    say "removed launchd job"
  fi
  if command -v crontab >/dev/null && crontab -l 2>/dev/null | grep -q "$CRON_MARKER"; then
    { crontab -l 2>/dev/null | grep -v "$CRON_MARKER" || true; } | crontab -
    say "removed cron job"
  fi
}

cmd_install() {
  local auto=1 cli=1
  for arg in "$@"; do
    case "$arg" in
      --no-auto-update) auto=0 ;;
      --no-cli) cli=0 ;;
      *) die "unknown option: $arg" ;;
    esac
  done
  command -v git >/dev/null || die "git is required"

  if [ -d "$QUILL_HOME/.git" ]; then
    say "existing install found at $QUILL_HOME; updating"
    cmd_update
  else
    mkdir -p "$(dirname "$QUILL_HOME")"
    git clone --quiet --branch "$QUILL_REF" "$QUILL_REPO" "$QUILL_HOME"
    mkdir -p "$STATE_DIR"
    printf '%s\n' "$QUILL_HOME" > "$CLONE_STATE"
    say "installed Quill $(installed_version) ($QUILL_REF) to $QUILL_HOME"
  fi

  link_skill
  if [ "$cli" -eq 1 ]; then
    install_cli
  fi
  if [ "$auto" -eq 1 ]; then
    schedule_updates
  else
    unschedule_updates
    say "automatic updates off; run '$QUILL_HOME/install.sh update' to update"
  fi
  say "done. Restart your agent to pick up the skill."
}

# Fast-forward only: never discards local edits, never moves to unreleased work.
cmd_update() {
  [ -d "$QUILL_HOME/.git" ] || die "Quill is not installed at $QUILL_HOME"
  local before after
  before="$(installed_version)"
  if [ -n "$(git -C "$QUILL_HOME" status --porcelain)" ]; then
    record_error "local changes in $QUILL_HOME; keeping $before"
    return 1
  fi
  if ! git -C "$QUILL_HOME" fetch --quiet --tags origin "$QUILL_REF" 2>/dev/null; then
    say "$(date '+%F %T') offline or fetch failed; keeping $before"
    refresh_cli
    return
  fi
  if ! git -C "$QUILL_HOME" merge --quiet --ff-only FETCH_HEAD 2>/dev/null; then
    record_error "local history in $QUILL_HOME prevents a fast-forward; keeping $before"
    return 1
  fi
  after="$(installed_version)"
  refresh_cli || return 1
  mkdir -p "$STATE_DIR"
  rm -f "$LAST_ERROR"
  date '+%F %T' > "$STATE_DIR/last-update"
  if [ "$before" = "$after" ]; then
    say "$(date '+%F %T') up to date ($after)"
  else
    say "$(date '+%F %T') updated $before -> $after (see $QUILL_HOME/CHANGELOG.md)"
  fi
}

cmd_status() {
  [ -d "$QUILL_HOME/.git" ] || { say "not installed at $QUILL_HOME"; return 0; }
  say "version:     $(installed_version)"
  say "tracking:    $QUILL_REF ($(git -C "$QUILL_HOME" rev-parse --short HEAD))"
  say "location:    $QUILL_HOME"
  say "last update: $(cat "$STATE_DIR/last-update" 2>/dev/null || echo never)"
  [ ! -f "$LAST_ERROR" ] || say "last error:  $(cat "$LAST_ERROR")"
  local dir
  for dir in "$HOME/.claude/skills" "$HOME/.agents/skills" "$HOME/.copilot/skills" "$HOME/.config/opencode/skills"; do
    [ -L "$dir/quill" ] && say "linked:      $dir/quill -> $(readlink "$dir/quill")"
  done
  if [ -f "$CLI_STATE" ]; then
    say "cli:         managed receipt recorded (run quill doctor to inspect versions)"
    if [ ! -f "$CLI_METADATA" ] || [ "$(cat "$CLI_METADATA")" != "$(metadata_fingerprint)" ]; then
      say "cli refresh: pending; run install.sh update"
    fi
  else
    say "cli:         not managed by the installer"
  fi
  if [ -f "$LAUNCHD_PLIST" ] || { command -v crontab >/dev/null && crontab -l 2>/dev/null | grep -q "$CRON_MARKER"; }; then
    say "auto-update: on (daily)"
  else
    say "auto-update: off"
  fi
}

cmd_uninstall() {
  unschedule_updates
  unlink_skill
  uninstall_cli
  if [ -d "$QUILL_HOME/.git" ]; then
    if [ ! -f "$CLONE_STATE" ] || [ "$(cat "$CLONE_STATE")" != "$QUILL_HOME" ]; then
      say "kept $QUILL_HOME because clone ownership is not recorded (including older installs)"
    elif ! git -C "$QUILL_HOME" status --porcelain >/dev/null 2>&1; then
      say "kept $QUILL_HOME because its Git state could not be checked"
    elif [ -n "$(git -C "$QUILL_HOME" status --porcelain --ignored)" ]; then
      say "kept $QUILL_HOME because it has local or ignored files; delete it yourself when done"
    elif ! git -C "$QUILL_HOME" show-ref --verify --quiet refs/remotes/origin/"$QUILL_REF"; then
      say "kept $QUILL_HOME because the tracked remote branch cannot establish published history"
    elif [ -n "$(git -C "$QUILL_HOME" rev-list --all --not --remotes=origin)" ]; then
      say "kept $QUILL_HOME because it has unpublished commits; delete it yourself when done"
    else
      rm -rf "$QUILL_HOME"
      say "removed $QUILL_HOME"
    fi
  fi
  rm -rf "$STATE_DIR"
  say "Quill uninstalled"
}

main() {
  local cmd="${1:-install}"
  case "$cmd" in
    install) shift || true; cmd_install "$@" ;;
    --no-auto-update|--no-cli) cmd_install "$@" ;;
    update) cmd_update ;;
    status) cmd_status ;;
    uninstall) cmd_uninstall ;;
    -h|--help|help) sed -n '2,18p' "$0" 2>/dev/null || true ;;
    *) die "unknown command: $cmd (try: install, update, status, uninstall)" ;;
  esac
}

main "$@"
