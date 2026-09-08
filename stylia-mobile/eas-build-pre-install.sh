#!/usr/bin/env bash
# eas-build-pre-install.sh
# Runs on EAS Build servers BEFORE npm install.
# Use this to set up build environment, install system deps, or validate config.

set -euo pipefail

echo "──────────────────────────────────────────"
echo "  STYLIA — EAS Pre-Install"
echo "  Platform : ${EAS_BUILD_PLATFORM:-unknown}"
echo "  Profile  : ${EAS_BUILD_PROFILE:-unknown}"
echo "──────────────────────────────────────────"

# ── Node version check ──────────────────────────
required_node="18"
current_node=$(node -v | cut -d. -f1 | tr -d 'v')
if [ "$current_node" -lt "$required_node" ]; then
  echo "❌ Node $required_node+ required, found $current_node"
  exit 1
fi
echo "✅ Node $(node -v)"

# ── iOS: CocoaPods cache (speeds up builds) ─────
if [ "${EAS_BUILD_PLATFORM:-}" = "ios" ]; then
  echo "🍎 iOS build — checking CocoaPods..."
  if command -v pod &>/dev/null; then
    echo "✅ CocoaPods $(pod --version)"
    # Update repo only on production builds to save time
    if [ "${EAS_BUILD_PROFILE:-}" = "production" ]; then
      pod repo update || true
    fi
  else
    echo "⚠️  CocoaPods not found — EAS will install it"
  fi
fi

# ── Android: Accept licenses ────────────────────
if [ "${EAS_BUILD_PLATFORM:-}" = "android" ]; then
  echo "🤖 Android build — accepting SDK licenses..."
  if [ -n "${ANDROID_HOME:-}" ]; then
    yes | "${ANDROID_HOME}/cmdline-tools/latest/bin/sdkmanager" --licenses 2>/dev/null || true
    echo "✅ SDK licenses accepted"
  fi
fi

# ── Validate required environment variables ─────
# Add any env vars your app needs at build time here.
# Example: API URL for bundling into the app
: "${APP_ENV:=development}"
echo "ℹ️  APP_ENV = $APP_ENV"

# ── Done ─────────────────────────────────────────
echo "✅ Pre-install complete"
