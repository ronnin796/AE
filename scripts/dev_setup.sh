#!/usr/bin/env bash
# AetherEdge Development Environment Setup
# Verifies toolchain and installs dependencies for all components

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[OK]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# Check if command exists
check_cmd() {
    if command -v "$1" &>/dev/null; then
        log_success "$1: $(command -v "$1")"
        return 0
    else
        log_error "$1: NOT FOUND"
        return 1
    fi
}

# Check version meets minimum
check_version() {
    local cmd="$1"
    local min_version="$2"
    local version_flag="${3:---version}"
    local current_version

    if ! current_version=$($cmd $version_flag 2>&1 | head -1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -1); then
        log_warn "$cmd: could not parse version"
        return 1
    fi

    # Simple version comparison (major.minor)
    local min_major min_minor cur_major cur_minor
    IFS='.' read -r min_major min_minor _ <<< "$min_version"
    IFS='.' read -r cur_major cur_minor _ <<< "$current_version"

    if (( cur_major > min_major || (cur_major == min_major && cur_minor >= min_minor) )); then
        log_success "$cmd: $current_version (>= $min_version)"
        return 0
    else
        log_error "$cmd: $current_version (< $min_version required)"
        return 1
    fi
}

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           AetherEdge Development Environment Setup          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo

# 1. Check core toolchain
log_info "Checking core toolchain..."

check_version rustc "1.75" || exit 1
check_version cargo "1.75" || exit 1
check_version python3 "3.11" || exit 1
check_version node "20" || exit 1
check_version npm "10" || exit 1

# Check optional tools
check_cmd uv || log_warn "uv not found, will use pip (install uv for faster installs: curl -LsSf https://astral.sh/uv/install.sh | sh)"
check_cmd sqlite3 || log_warn "sqlite3 CLI not found (optional, for DB inspection)"

echo
log_info "Checking Rust components..."

# 2. Rust: verify fmt and clippy available
if rustup component list | grep -q "rustfmt (installed)"; then
    log_success "rustfmt: installed"
else
    log_warn "rustfmt not installed: rustup component add rustfmt"
fi

if rustup component list | grep -q "clippy (installed)"; then
    log_success "clippy: installed"
else
    log_warn "clippy not installed: rustup component add clippy"
fi

echo
log_info "Setting up Edge daemon (Rust)..."

cd "$(dirname "$0")/../edge"
if cargo check 2>/dev/null; then
    log_success "Edge crate compiles"
else
    log_warn "Edge crate has compile errors (expected during early development)"
fi

echo
log_info "Setting up FastAPI Server (Python)..."

cd "$(dirname "$0")/../server"
if command -v uv &>/dev/null; then
    uv sync --quiet && log_success "Server dependencies installed (uv)"
else
    pip install -e . --quiet && log_success "Server dependencies installed (pip)"
fi

echo
log_info "Setting up ML Tooling (Python)..."

cd "$(dirname "$0")/../ml"
if command -v uv &>/dev/null; then
    uv sync --quiet && log_success "ML dependencies installed (uv)"
else
    pip install -e . --quiet && log_success "ML dependencies installed (pip)"
fi

echo
log_info "Setting up Dashboard (Node.js)..."

cd "$(dirname "$0")/../dashboard"
if [ -f package-lock.json ] || [ -f pnpm-lock.yaml ]; then
    npm ci --quiet 2>/dev/null && log_success "Dashboard dependencies installed"
else
    npm install --quiet 2>/dev/null && log_success "Dashboard dependencies installed"
fi

echo
log_info "Verifying Linux telemetry access..."

# Check /proc and /sys accessibility
for path in /proc/stat /proc/meminfo /proc/uptime /proc/loadavg /proc/cpuinfo; do
    if [ -r "$path" ]; then
        log_success "Readable: $path"
    else
        log_error "Cannot read: $path (need root or proper permissions)"
    fi
done

# Check thermal zones (may not exist on all systems)
if [ -d /sys/class/thermal ]; then
    thermal_count=$(ls /sys/class/thermal/thermal_zone* 2>/dev/null | wc -l)
    if [ "$thermal_count" -gt 0 ]; then
        log_success "Thermal zones: $thermal_count found"
    else
        log_warn "No thermal zones found (temperature collection will be skipped)"
    fi
else
    log_warn "/sys/class/thermal not found (temperature collection unavailable)"
fi

echo
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    Setup Complete                            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo
log_info "Next steps:"
echo "  1. Start server:    cd server && uv run uvicorn app.main:app --reload"
echo "  2. Start edge node: cd edge && cargo run -- --node-id node-1"
echo "  3. Start dashboard: cd dashboard && npm run dev"
echo