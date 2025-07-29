# Copyright Analyzer API

A production-ready FastAPI service for analyzing copyright status of literary and musical works with intelligent caching and background processing.

## Features

- **Multi-source Analysis**: Queries Library of Congress, HathiTrust, and MusicBrainz APIs
- **Intelligent Caching**: Supabase-powered cache with automatic expiration and refresh
- **Background Processing**: Scheduled jobs for cache maintenance and pre-population
- **Batch Processing**: Analyze multiple works efficiently
- **Country Support**: Extensible framework for different copyright jurisdictions (US implemented)

## Quick Start

### Prerequisites

- Python 3.8+
- Supabase account and database
- Environment variables configured

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Supabase credentials

# Run the application
python main.py
```

### Database Setup

1. Create tables in your Supabase dashboard using `sql/create_tables.sql`
2. Ensure your Supabase URL and API key are configured in `.env`

## API Endpoints

### Core Analysis
- `POST /api/analyze` - Analyze single work
- `POST /api/analyze/batch` - Analyze multiple works

### Cache Management
- `GET /api/cache/stats` - View cache statistics
- `DELETE /api/cache/clear` - Clear all cache
- `DELETE /api/cache/clear/works` - Clear work cache only
- `DELETE /api/cache/clear/searches` - Clear search cache only
- `DELETE /api/cache/clear/expired` - Clear expired entries only

### Information
- `GET /api/status` - API health check
- `GET /api/examples` - Sample works for testing
- `GET /api/countries` - Supported countries
- `GET /docs` - Interactive API documentation

## Configuration

### Environment Variables

```bash
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
PYTHON_ENV=production
```

### Cache Settings

- Work cache: 7 days default expiration
- Search cache: 24 hours default expiration
- Background refresh: Every 6 hours
- Cache cleanup: Daily at 2 AM
- Popular search pre-population: Daily at 3 AM

## Architecture

```
User Request → Cache Check → API Analysis → Cache Store → Response
                    ↓
Background Jobs → Cache Refresh → Keep Data Fresh
```

## Output Format

The system outputs a normalized JSON record:

```json
{
  "title": "The Great Novel",
  "author_name": "John Doe",
  "publication_year": 1975,
  "published": true,
  "country": "US",
  "year_of_death": 1980,
  "work_type": "individual",
  "status": "Under Copyright",
  "enters_public_domain": 2071,
  "source_links": {
    "loc": "https://www.loc.gov/books/?q=The Great Novel John Doe",
    "hathitrust": "https://catalog.hathitrust.org/Record/123456"
  },
  "notes": "Published in 1975 by individual author. Term is 95 years under §304; PD Jan 1, 2071 per §305.",
  "confidence_score": 0.85,
  "queried_at": "2024-01-01T12:00:00Z"
}
```

## Data Sources

### United States
- **Library of Congress Search API**: Primary source for literary works metadata
- **HathiTrust Digital Library API**: Rights status and publication details  
- **MusicBrainz API**: Musical works and composer life dates

### Rate Limits
- Library of Congress: 1 req/sec (recommended)
- HathiTrust: 1 req/sec
- MusicBrainz: 1 req/sec (enforced)

## US Copyright Law Implementation

The system implements current US copyright law for public domain calculations:

### Pre-1923 Works
- **Status**: Public Domain
- **Rule**: All works published before 1923 are in the public domain

### 1923-1977 Works
- **Term**: 95 years from publication
- **Rule**: Based on §304 renewal provisions

### 1978+ Works
- **Individual authors**: Life + 70 years
- **Work for hire**: 95 years from publication or 120 years from creation
- **Rule**: Based on 1976 Copyright Act §305

## Architecture

```
src/
├── copyright_analyzer.py      # Country-aware main orchestrator
├── core/                     # Abstract base classes
│   ├── base_analyzer.py
│   ├── base_api_client.py
│   └── base_copyright_calculator.py
├── countries/               # Country-specific implementations
│   ├── __init__.py         # Country registry system
│   └── us/                 # US implementation
│       ├── us_analyzer.py
│       ├── copyright_rules.py
│       ├── config.py
│       └── api_clients/
├── models/                 # Data models
│   └── work_record.py
└── utils/                  # Utilities
    └── metadata_normalizer.py
```

## Testing

```bash
# Run test suite
python tests/test_copyright_analyzer.py

# Run examples
python examples/example_usage.py
```

## Adding New Countries

The architecture is designed for easy expansion:

1. **Create country directory**: `src/countries/{country_code}/`
2. **Implement analyzer**: Extend `BaseCountryAnalyzer`
3. **Add API clients**: Country-specific data sources
4. **Implement copyright rules**: Extend `BaseCopyrightCalculator`
5. **Register country**: Add to `COUNTRY_REGISTRY`

The system will automatically support the new country in CLI, API, and web interfaces.

## Configuration

Country-specific settings are managed in `src/countries/{country}/config.py`:

- API client configurations
- Rate limiting settings
- Confidence scoring weights
- Copyright law parameters

## Error Handling

The system includes comprehensive error handling for:
- Network timeouts and API failures
- Rate limiting and backoff strategies
- Malformed API responses
- Missing metadata scenarios
- Invalid country codes

## Limitations

- **US-focused initially**: Currently optimized for US copyright law
- **API dependencies**: Relies on external API availability
- **Metadata quality**: Results depend on source data accuracy
- **Historical works**: Some pre-1900 works may have uncertain publication dates

## Future Enhancements

- **🇬🇧 UK copyright law** (Life + 70 years, pre-1988 rules)
- **🇨🇦 Canadian copyright law** (Life + 50/70 years transition)
- **🇩🇪 German copyright law** (Life + 70 years, wartime extensions)
- **🗄️ Database storage** (Supabase integration)
- **🔍 Enhanced search** algorithms
- **📊 Analytics dashboard**
- **🔄 Bulk import/export** tools

## Contributing

The system is designed to be modular and extensible. Each country implementation is self-contained and follows the same interface patterns.

## License

Copyright © 2024 Copyr.ai - All rights reserved.

---

**🚀 Ready to scale to any country's copyright jurisdiction while maintaining clean, maintainable code!**