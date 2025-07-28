# Copyr.ai - Multi-Country Copyright Analyzer

A scalable, country-aware Python system that queries reliable APIs to determine public domain status of literary and musical works across different jurisdictions.

## Features

- **🌍 Multi-country support**: Extensible architecture for different copyright jurisdictions
- **📚 Multi-source data gathering**: Queries Library of Congress, HathiTrust, and MusicBrainz APIs
- **⚖️ Country-specific copyright law**: Implements jurisdiction-specific copyright calculations
- **🎵 Literary and Musical works**: Supports both books and musical compositions
- **📊 Normalized output**: Consistent JSON format across all countries and sources
- **🎯 High confidence scoring**: Weighted confidence based on source reliability
- **⚡ Batch processing**: Analyze multiple works efficiently
- **🚀 REST API**: FastAPI-powered endpoints for web integration

## Supported Countries

- **🇺🇸 United States**: Title 17 USC §304 and §305 compliance
- *More countries coming soon...*

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```python
from src.copyright_analyzer import CopyrightAnalyzer

# Initialize analyzer for specific country
analyzer = CopyrightAnalyzer("US")

# Analyze a literary work
result = analyzer.analyze_work("The Great Gatsby", "F. Scott Fitzgerald")
print(f"Status: {result.status}")
print(f"Enters PD: {result.enters_public_domain}")

# Analyze a musical work
result = analyzer.analyze_work("Symphony No. 9", "Beethoven", work_type="musical")
```

### Command Line Interface

```bash
# Analyze a single work
python -m src.copyright_analyzer "Pride and Prejudice" "Jane Austen" --country US --verbose

# List supported countries
python -m src.copyright_analyzer --list-countries

# Musical work analysis
python -m src.copyright_analyzer "Symphony No. 9" "Beethoven" --work-type musical --country US

# Save results to file
python -m src.copyright_analyzer "Dracula" "Bram Stoker" --output results.json --country US
```

### REST API Usage

Start the FastAPI server:
```bash
python main.py
```

Access the interactive API documentation at: **http://localhost:8000/docs**

#### Available Endpoints

- **POST `/api/analyze`** - Analyze single work
- **POST `/api/analyze/batch`** - Batch analysis of multiple works
- **GET `/api/countries`** - List supported countries
- **GET `/api/copyright-info/{country_code}`** - Get country-specific copyright rules
- **GET `/api/examples`** - Get example works for testing
- **GET `/api/status`** - System status

#### Example API Request

```json
{
  "title": "Pride and Prejudice",
  "author": "Jane Austen",
  "work_type": "literary",
  "country": "US",
  "verbose": true
}
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