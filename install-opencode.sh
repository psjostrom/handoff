#!/bin/sh
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_SOURCE="$SCRIPT_DIR/opencode"
GLOBAL_TARGET="${HOME}/.config/opencode"
PROJECT_TARGET="$(pwd)/.opencode"

usage() {
  cat <<'EOF'
Usage:
  ./install-opencode.sh install [--project]
  ./install-opencode.sh uninstall [--project]
  ./install-opencode.sh list [--project]
EOF
}

is_owned_link() {
  owned_source_dir="$1"
  owned_link="$2"
  [ -L "$owned_link" ] || return 1
  owned_link_target="$(readlink "$owned_link")"
  case "$owned_link_target" in
    /*) ;;
    *) owned_link_target="$(dirname "$owned_link")/$owned_link_target" ;;
  esac
  owned_hops=0
  while [ -L "$owned_link_target" ]; do
    owned_hops=$((owned_hops + 1))
    [ "$owned_hops" -le 40 ] || return 1
    owned_target_link="$(readlink "$owned_link_target")"
    case "$owned_target_link" in
      /*) owned_link_target="$owned_target_link" ;;
      *) owned_link_target="$(dirname "$owned_link_target")/$owned_target_link" ;;
    esac
  done
  owned_target_dir="$(dirname "$owned_link_target")"
  [ -d "$owned_target_dir" ] || return 1
  owned_canonical_source="$(cd "$owned_source_dir" && pwd -P)"
  owned_canonical_target="$(cd "$owned_target_dir" && pwd -P)/$(basename "$owned_link_target")"
  case "$owned_canonical_target" in
    "$owned_canonical_source"/*) return 0 ;;
  esac
  return 1
}

prune_stale_links() {
  target="$1"
  for source_dir in "$PLUGIN_SOURCE"/*; do
    [ -d "$source_dir" ] || continue
    category="$(basename "$source_dir")"
    [ -d "$target/$category" ] || continue
    for link in "$target/$category"/*; do
      [ -L "$link" ] || continue
      if is_owned_link "$source_dir" "$link" && [ ! -e "$link" ]; then
        rm "$link"
        echo "  pruned stale $link"
      fi
    done
  done
}

link_plugin() {
  target="$1"
  prune_stale_links "$target"
  for source_dir in "$PLUGIN_SOURCE"/*; do
    [ -d "$source_dir" ] || continue
    category="$(basename "$source_dir")"
    mkdir -p "$target/$category"
    for source in "$source_dir"/*; do
      [ -e "$source" ] || continue
      dest="$target/$category/$(basename "$source")"
      if [ -e "$dest" ] || [ -L "$dest" ]; then
        if ! is_owned_link "$source_dir" "$dest"; then
          echo "  skip $dest — exists and is not Handoff-owned"
          continue
        fi
      fi
      ln -sfn "$source" "$dest"
      echo "  linked $dest"
    done
  done
  echo "Installed Handoff -> $target"
}

unlink_plugin() {
  target="$1"
  prune_stale_links "$target"
  for source_dir in "$PLUGIN_SOURCE"/*; do
    [ -d "$source_dir" ] || continue
    category="$(basename "$source_dir")"
    for source in "$source_dir"/*; do
      [ -e "$source" ] || continue
      link="$target/$category/$(basename "$source")"
      if is_owned_link "$source_dir" "$link"; then
        rm "$link"
        echo "  removed $link"
      fi
    done
  done
  echo "Uninstalled Handoff from $target"
}

list_plugin() {
  target="$1"
  if is_owned_link "$PLUGIN_SOURCE/commands" "$target/commands/handoff.md"; then
    echo "Handoff installed: $target"
  else
    echo "Handoff not installed: $target"
  fi
}

command="${1:-}"
project=false
case "$#" in
  1) ;;
  2) [ "$2" = "--project" ] && project=true || { usage >&2; exit 1; } ;;
  *) usage >&2; exit 1 ;;
esac

case "$command" in
  install|uninstall|list) ;;
  *) usage >&2; exit 1 ;;
esac

target="$GLOBAL_TARGET"
[ "$project" = true ] && target="$PROJECT_TARGET"

case "$command" in
  install) link_plugin "$target" ;;
  uninstall) unlink_plugin "$target" ;;
  list) list_plugin "$target" ;;
esac
