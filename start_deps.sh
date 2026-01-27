#!/bin/bash
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# OS Detection
OS="$(uname -s)"
case "${OS}" in
    Linux*)     OS=Linux;;
    Darwin*)    OS=Mac;;
    *)          OS="UNKNOWN:${OS}"
esac

log "Detected OS: $OS"

check_cmd() {
    command -v "$1" >/dev/null 2>&1
}

install_curl() {
    if check_cmd curl; then
        success "curl is already installed."
        return
    fi
    log "Installing curl..."
    if [ "$OS" == "Linux" ]; then
        if [ -f /etc/debian_version ]; then
            sudo apt-get update && sudo apt-get install -y curl
        elif [ -f /etc/redhat-release ]; then
            sudo yum install -y curl
        else
            error "Unsupported Linux distribution for auto-installing curl."
        fi
    elif [ "$OS" == "Mac" ]; then
        brew install curl
    fi
}

install_docker() {
    if check_cmd docker; then
        success "docker is already installed."
        return
    fi
    log "Installing docker..."
    if [ "$OS" == "Linux" ]; then
        curl -fsSL https://get.docker.com | sh
        sudo groupadd docker || true
        sudo usermod -aG docker $USER || true
        log "Docker installed. You may need to log out and back in for group changes to take effect."
    elif [ "$OS" == "Mac" ]; then
        if ! check_cmd brew; then
            error "Homebrew is required to install Docker on Mac."
        fi
        brew install --cask docker
    fi
}

install_sops() {
    if check_cmd sops; then
        success "sops is already installed."
        return
    fi
    log "Installing sops..."
    if [ "$OS" == "Linux" ]; then
        # Install latest binary from GitHub
        LATEST_URL=$(curl -s "https://api.github.com/repos/getsops/sops/releases/latest" | grep "browser_download_url" | grep "linux.amd64" | cut -d '"' -f 4)
        curl -L "$LATEST_URL" -o sops
        chmod +x sops
        sudo mv sops /usr/local/bin/sops
    elif [ "$OS" == "Mac" ]; then
        brew install sops
    fi
}

# Main
if [ "$OS" == "UNKNOWN" ]; then
    error "Unsupported OS"
fi

install_curl
install_docker
install_sops

success "All dependencies installed!"
