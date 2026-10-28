#!/usr/bin/env bash
#
# install-local.sh: build Keepresso, sign it with your Apple Development
# certificate, and install it into /Applications.
#
# For running your own build on this Mac only. Every piece of the app (the
# Sparkle framework, the root helper, the widget) must share one Team ID:
# the hardened runtime refuses to load a bundled library from a different
# team, and an ad-hoc build has no team at all, so it crashes at launch.
#
#   KEEPRESSO_TEAM=XXXXXXXXXX ./scripts/install-local.sh              # build, install, launch
#   KEEPRESSO_TEAM=XXXXXXXXXX ./scripts/install-local.sh --no-launch  # build and install only
#
# KEEPRESSO_TEAM is your 10-character Apple Developer Team ID. Find it in the
# OU field of your certificate, or in the parentheses of the output of
#   security find-identity -v -p codesigning
# Export it from your shell profile so you don't have to type it each time.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

TEAM="${KEEPRESSO_TEAM:-}"
BUNDLE_ID="sh.gyorgy.keepresso"
DEST="/Applications/Keepresso.app"
DERIVED="$ROOT_DIR/build/local"
BUILT="$DERIVED/Build/Products/Release/Keepresso.app"
DO_LAUNCH=true

for arg in "$@"; do
  case "$arg" in
    --no-launch) DO_LAUNCH=false ;;
    -h|--help)
      grep '^#' "$0" | grep -v '^#!' | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *)
      echo "Unknown option: $arg (try --help)" >&2
      exit 2 ;;
  esac
done

info() { printf '\033[1;34m==>\033[0m %s\n' "$1"; }
die()  { printf '\033[1;31mError:\033[0m %s\n' "$1" >&2; exit 1; }

# --- Preconditions -----------------------------------------------------------

xcodebuild -version >/dev/null 2>&1 \
  || die "Full Xcode is required (Command Line Tools alone can't build the app)."
command -v xcodegen >/dev/null 2>&1 \
  || die "XcodeGen not found. Install it with: brew install xcodegen"
security find-identity -v -p codesigning | grep -q "Apple Development" \
  || die "No Apple Development certificate found in your keychain."
[[ "$TEAM" =~ ^[A-Z0-9]{10}$ ]] \
  || die "Set KEEPRESSO_TEAM to your 10-character Team ID (see --help)."

# --- Build -------------------------------------------------------------------

info "Generating Keepresso.xcodeproj..."
xcodegen generate --quiet

info "Building Release, signed with team $TEAM..."
rm -rf "$BUILT"
LOG="$DERIVED/build.log"
mkdir -p "$DERIVED"
if ! xcodebuild build \
    -project Keepresso.xcodeproj \
    -scheme Keepresso \
    -configuration Release \
    -destination 'platform=macOS,arch=arm64' \
    -derivedDataPath "$DERIVED" \
    CODE_SIGN_STYLE=Manual \
    DEVELOPMENT_TEAM="$TEAM" \
    CODE_SIGN_IDENTITY="Apple Development" \
    PROVISIONING_PROFILE_SPECIFIER= \
    OTHER_CODE_SIGN_FLAGS=--timestamp=none \
    -quiet >"$LOG" 2>&1; then
  tail -30 "$LOG" >&2
  die "Build failed. Full log: $LOG"
fi

# --- Verify ------------------------------------------------------------------

info "Verifying signatures..."
codesign --verify --deep --strict "$BUILT" || die "Signature check failed."
for part in \
    "$BUILT" \
    "$BUILT/Contents/Frameworks/Sparkle.framework/Versions/B/Sparkle" \
    "$BUILT/Contents/MacOS/keepresso-helper" \
    "$BUILT/Contents/PlugIns/KeepressoWidget.appex"; do
  team="$(codesign -dv "$part" 2>&1 | sed -n 's/^TeamIdentifier=//p')"
  [ "$team" = "$TEAM" ] || die "${part##*/} is signed with team '$team', expected $TEAM."
done

# --- Install -----------------------------------------------------------------

if [ -e "$DEST" ]; then
  existing="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' \
    "$DEST/Contents/Info.plist" 2>/dev/null || true)"
  [ "$existing" = "$BUNDLE_ID" ] \
    || die "$DEST exists but isn't Keepresso ($existing). Not touching it."
fi

if pgrep -x Keepresso >/dev/null; then
  info "Quitting the running Keepresso..."
  osascript -e "tell application id \"$BUNDLE_ID\" to quit" >/dev/null 2>&1 || true
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    pgrep -x Keepresso >/dev/null || break
    sleep 0.5
  done
  pgrep -x Keepresso >/dev/null && pkill -x Keepresso || true
fi

info "Installing to $DEST..."
STAGE="$(mktemp -d /Applications/.keepresso-install.XXXXXX)"
ditto "$BUILT" "$STAGE/Keepresso.app"
rm -rf "$DEST"
mv "$STAGE/Keepresso.app" "$DEST"
rmdir "$STAGE"

# --- Launch ------------------------------------------------------------------

if [ "$DO_LAUNCH" = true ]; then
  info "Launching Keepresso (look for its icon in the menu bar)..."
  open "$DEST"
fi
info "Done."
