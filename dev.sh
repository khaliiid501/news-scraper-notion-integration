#!/bin/bash
# Development helper script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Function to show help
show_help() {
    echo "News Scraper Service Development Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start       Start the service with Docker Compose"
    echo "  stop        Stop the service"
    echo "  restart     Restart the service"
    echo "  logs        Show service logs"
    echo "  build       Build the Docker image"
    echo "  test        Run validation tests"
    echo "  clean       Clean up Docker containers and volumes"
    echo "  db-shell    Connect to PostgreSQL shell"
    echo "  api-shell   Connect to API container shell"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start                # Start all services"
    echo "  $0 logs api            # Show API logs"
    echo "  $0 db-shell            # Connect to database"
}

# Function to start services
start_services() {
    print_status "Starting News Scraper Service..."
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from example..."
        cp .env.example .env
        print_status "Created .env file. You may want to customize it."
    fi
    
    docker compose up -d
    
    print_status "Services started! Waiting for health checks..."
    sleep 10
    
    # Check service status
    if docker compose ps | grep -q "healthy"; then
        print_status "✅ Services are healthy!"
        echo ""
        echo "🌐 Access points:"
        echo "  • API: http://localhost:8000"
        echo "  • API Docs: http://localhost:8000/docs"
        echo "  • Database Admin: http://localhost:8080"
        echo ""
        echo "📋 Useful commands:"
        echo "  • View logs: $0 logs"
        echo "  • Stop services: $0 stop"
        echo "  • Database shell: $0 db-shell"
    else
        print_warning "Services may still be starting. Check logs with: $0 logs"
    fi
}

# Function to stop services
stop_services() {
    print_status "Stopping News Scraper Service..."
    docker compose down
    print_status "Services stopped."
}

# Function to restart services
restart_services() {
    print_status "Restarting News Scraper Service..."
    docker compose restart
    print_status "Services restarted."
}

# Function to show logs
show_logs() {
    if [ -n "$2" ]; then
        docker compose logs -f "$2"
    else
        docker compose logs -f
    fi
}

# Function to build images
build_images() {
    print_status "Building Docker images..."
    docker compose build
    print_status "Build completed."
}

# Function to run tests
run_tests() {
    print_status "Running validation tests..."
    python validate_service.py
}

# Function to clean up
clean_up() {
    print_warning "This will remove all containers, networks, and volumes."
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Cleaning up..."
        docker compose down -v --remove-orphans
        docker system prune -f
        print_status "Cleanup completed."
    else
        print_status "Cleanup cancelled."
    fi
}

# Function to connect to database shell
db_shell() {
    print_status "Connecting to PostgreSQL shell..."
    docker compose exec db psql -U newsuser -d newsdb
}

# Function to connect to API shell
api_shell() {
    print_status "Connecting to API container shell..."
    docker compose exec api bash
}

# Main script logic
case "${1:-help}" in
    "start")
        start_services
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        restart_services
        ;;
    "logs")
        show_logs "$@"
        ;;
    "build")
        build_images
        ;;
    "test")
        run_tests
        ;;
    "clean")
        clean_up
        ;;
    "db-shell")
        db_shell
        ;;
    "api-shell")
        api_shell
        ;;
    "help"|*)
        show_help
        ;;
esac