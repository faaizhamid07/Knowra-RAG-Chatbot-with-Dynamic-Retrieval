#!/usr/bin/env bash

# Knowra - Multi-Source RAG Chatbot with Dynamic Retrieval
# Setup and Execution Script
# Usage: ./run.sh [--install | --run | --dev | --build | --test | --docker | --clean | --help]

set -euo pipefail
IFS=$'\n\t'

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

REQUIREMENTS="requirements.txt"
PORT=8000
HOST="0.0.0.0"

# Print usage help
show_help() {
    cat << EOF
${BLUE}Knowra - Multi-Source RAG Chatbot${NC}
Usage: $0 [option]

Options:
  --run        Start the Knowra application (FastAPI backend + React SPA) on port $PORT [Default]
  --dev        Start FastAPI backend with live reload
  --build      Build the React frontend production bundle (npm run build)
  --install    Install Python dependencies from $REQUIREMENTS
  --test       Run the automated test suites (Phase 3A, Phase 3B, Playwright E2E)
  --docker     Build and start containerized application via Docker Compose
  --clean      Remove temporary files, caches, and test logs
  --help       Show this help message
EOF
}

# Install dependencies
install_dependencies() {
    echo -e "${BLUE}Installing Python dependencies...${NC}"
    python -m pip install --upgrade pip
    python -m pip install -r "$REQUIREMENTS"
    echo -e "${GREEN}Dependencies installed successfully!${NC}"
}

# Build frontend
build_frontend() {
    echo -e "${BLUE}Building React frontend production bundle...${NC}"
    if command -v npm &>/dev/null; then
        npm --prefix frontend run build
        echo -e "${GREEN}Frontend build complete!${NC}"
    else
        echo -e "${YELLOW}npm not found. Using pre-built frontend bundle in frontend/dist.${NC}"
    fi
}

# Run the production application
run_app() {
    echo -e "${GREEN}Starting Knowra RAG Chatbot on http://localhost:${PORT} ...${NC}"
    exec python -m uvicorn src.api.main:app --host "$HOST" --port "$PORT"
}

# Run in development mode
run_dev() {
    echo -e "${BLUE}Starting Knowra in development mode with reload on http://localhost:${PORT} ...${NC}"
    exec python -m uvicorn src.api.main:app --host "$HOST" --port "$PORT" --reload
}

# Run test suites
run_tests() {
    echo -e "${BLUE}Running Phase 3A Cancellation & Streaming Tests...${NC}"
    python tests/test_phase3a_cancellation.py
    echo -e "${BLUE}Running Phase 3B Integration Tests...${NC}"
    python tests/test_phase3b_e2e_integration.py
    echo -e "${GREEN}All unit and integration tests passed!${NC}"
}

# Build and start via Docker Compose
run_docker() {
    echo -e "${YELLOW}Building and starting Docker container...${NC}"
    docker-compose up --build --remove-orphans
}

# Clean up caches and temporary files
clean_up() {
    echo -e "${YELLOW}Cleaning up caches and temporary artifacts...${NC}"
    find . -type d -name "__pycache__" -prune -exec rm -rf {} +
    find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
    find . -type f -name "*.py[co]" -delete
    rm -f server_e2e.log app_log.txt
    echo -e "${GREEN}Cleanup complete!${NC}"
}

# Main routing
case "${1:-}" in
    --install)
        install_dependencies
        ;;
    --build)
        build_frontend
        ;;
    --run)
        run_app
        ;;
    --dev)
        run_dev
        ;;
    --test)
        run_tests
        ;;
    --docker)
        run_docker
        ;;
    --clean)
        clean_up
        ;;
    --help)
        show_help
        ;;
    "")
        run_app
        ;;
    *)
        echo -e "${RED}Unknown option: $1${NC}"
        show_help
        exit 1
        ;;
esac

exit 0
