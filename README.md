# News Scraper Service

A production-ready news scraper service that collects articles from RSS feeds, stores them in PostgreSQL, and exposes them via a FastAPI REST API.

## Features

- 🔄 **RSS Feed Scraping**: Automatically scrapes news from configurable RSS sources
- 🗄️ **PostgreSQL Storage**: Stores normalized articles with full-text search capabilities
- 🚀 **FastAPI REST API**: Modern, fast API with automatic documentation
- 🐳 **Docker Support**: Full Docker Compose setup for local development
- 📊 **Structured Logging**: JSON-formatted logging with structlog
- 🧪 **Comprehensive Testing**: Unit tests with pytest and coverage reporting
- 🔍 **Code Quality**: Enforced with ruff, black, and mypy
- 🚦 **CI/CD**: GitHub Actions workflow for automated testing

## Tech Stack

- **Python 3.11+** - Modern Python with type hints
- **FastAPI** - High-performance web framework
- **SQLAlchemy 2.x** - Modern ORM with async support
- **PostgreSQL 14+** - Robust relational database
- **Alembic** - Database migration management
- **Pydantic** - Data validation and serialization
- **httpx** - Modern HTTP client for scraping
- **feedparser** - RSS feed parsing
- **beautifulsoup4** - HTML content extraction
- **structlog** - Structured logging
- **Docker & Docker Compose** - Containerization

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### Using Docker Compose (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/khaliiid501/news-scraper-notion-integration.git
   cd news-scraper-notion-integration
   ```

2. **Start the services**:
   ```bash
   docker-compose up -d
   ```

3. **Access the API**:
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Database Admin (Adminer): http://localhost:8080

### Local Development Setup

1. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start PostgreSQL** (using Docker):
   ```bash
   docker-compose up -d db
   ```

5. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

6. **Start the application**:
   ```bash
   python main.py
   ```

## Configuration

Environment variables can be set in `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://newsuser:newspass@localhost:5432/newsdb` |
| `API_HOST` | API server host | `0.0.0.0` |
| `API_PORT` | API server port | `8000` |
| `DEBUG` | Debug mode | `false` |
| `NEWS_SOURCES` | Comma-separated RSS feed URLs | BBC and CNN feeds |
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_FORMAT` | Logging format (`json` or `console`) | `json` |
| `SCRAPE_INTERVAL` | Scraping interval in seconds | `3600` |
| `MAX_ARTICLES_PER_SOURCE` | Max articles per source | `50` |

## API Endpoints

### Health Check
- `GET /api/v1/health` - Service health status

### Articles
- `GET /api/v1/articles` - List articles with pagination and filtering
- `GET /api/v1/articles/{id}` - Get specific article
- `POST /api/v1/articles` - Create new article
- `PUT /api/v1/articles/{id}` - Update article
- `DELETE /api/v1/articles/{id}` - Delete article

### Metadata
- `GET /api/v1/sources` - List all unique sources
- `GET /api/v1/categories` - List all unique categories
- `GET /api/v1/stats` - Database statistics

### Query Parameters for Articles

| Parameter | Description | Example |
|-----------|-------------|---------|
| `page` | Page number (default: 1) | `?page=2` |
| `size` | Page size (default: 10, max: 100) | `?size=20` |
| `source` | Filter by source | `?source=BBC` |
| `category` | Filter by category | `?category=Technology` |
| `author` | Filter by author | `?author=John` |
| `search` | Search in title/content | `?search=climate` |
| `from_date` | Filter from date | `?from_date=2024-01-01T00:00:00Z` |
| `to_date` | Filter to date | `?to_date=2024-12-31T23:59:59Z` |

## Database Schema

### Articles Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Primary key |
| `title` | String(500) | Article title |
| `url` | String(1000) | Article URL (unique) |
| `content` | Text | Full article content |
| `summary` | Text | Article summary |
| `author` | String(200) | Article author |
| `source` | String(200) | News source |
| `category` | String(100) | Article category |
| `published_at` | DateTime | Publication timestamp |
| `scraped_at` | DateTime | Scraping timestamp |

## News Scraping

The service automatically scrapes news from configured RSS sources:

1. **RSS Parsing**: Uses `feedparser` to parse RSS feeds
2. **Content Enhancement**: Attempts to scrape full article content from source URLs
3. **Data Normalization**: Extracts and normalizes article metadata
4. **Duplicate Prevention**: Uses URL uniqueness to prevent duplicates
5. **Error Handling**: Robust error handling with structured logging

### Adding News Sources

Edit the `NEWS_SOURCES` environment variable:

```bash
NEWS_SOURCES=https://feeds.bbci.co.uk/news/rss.xml,https://rss.cnn.com/rss/edition.rss,https://feeds.reuters.com/reuters/topNews
```

## Development

### Code Quality

The project enforces code quality with:

- **ruff**: Fast Python linter
- **black**: Code formatter
- **mypy**: Static type checker

Run quality checks:
```bash
# Linting
ruff check .

# Formatting
black .

# Type checking
mypy app/
```

### Testing

Run tests with coverage:
```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html
```

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

## Production Deployment

### Environment Setup

1. Set production environment variables
2. Use a managed PostgreSQL service
3. Configure proper logging aggregation
4. Set up monitoring and health checks
5. Use a reverse proxy (nginx) for HTTPS

### Security Considerations

- Set `DEBUG=false` in production
- Use strong database credentials
- Configure CORS appropriately
- Implement rate limiting
- Use HTTPS in production

## Monitoring

### Health Checks

- Application: `GET /api/v1/health`
- Database: Built into Docker Compose health checks

### Logging

The service uses structured JSON logging with the following fields:

- `timestamp`: ISO 8601 timestamp
- `level`: Log level (INFO, ERROR, etc.)
- `logger`: Logger name
- `message`: Log message
- Additional context fields

### Metrics

Basic statistics available at `/api/v1/stats`:

- Total articles count
- Articles by source
- Recent articles (last 24 hours)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Ensure code quality checks pass
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/khaliiid501/news-scraper-notion-integration/issues)
- Documentation: Check the `/docs` endpoint when running the service
