# Lieferando Ranking API

A FastAPI-based service that tracks restaurant rankings on Lieferando.de. The API provides real-time ranking information and maintains a historical record of rankings for specified restaurants.

## Features

- 🔍 Real-time restaurant ranking lookup via API
- 📊 Automated ranking tracking for specified restaurants
- 📅 Historical ranking data storage
- ⏱️ Configurable scheduling for rank tracking
- 🐳 Easy deployment with Docker

## Prerequisites

- Docker and Docker Compose

That's it! Everything else is handled by the Docker containers.

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/PaulKenntner/LANCH_Case_study.git
cd lieferando-ranking-api
```

2. Start the application:
```bash
docker compose up -d
```

The application will be available at `http://localhost:8080`.

## Usage

### API Endpoint

Get the current ranking for a restaurant:
```bash
http://localhost:8080/rank/{restaurant_slug}
```

Example:
```bash
http://localhost:8080/rank/loco-chicken-i-frechen
```

Response:
```json
{
    "restaurant_slug": "loco-chicken-i-frechen",
    "rank": 2,
    "rating": "4.5"
}
```

### View Historical Rankings

Use the provided script to view ranking history:

```bash
docker exec -it lanch-web-1 python app/services/view_rankings.py --slug loco-chicken-i-frechen --days 7
```

This will output the ranking history for the specified restaurant over the last 7 days.


### Automated Tracking

The application automatically tracks rankings for configured restaurants every hour. To modify the tracked restaurants, edit the `restaurant_slugs` list in `app/utils/scheduler.py`:

```python
self.restaurant_slugs = [
    "loco-chicken-i-frechen",
    "loco-chicken-bielefeld",
    "happy-slice-suedstadt",
    "happy-slice-pizza-i-wandsbek-markt",
    # Add more restaurants as needed
]
```

## Configuration

Key configurations in `app/config.py`:
- `SCRAPING_INTERVAL_MINUTES`: Time between ranking updates (default: 60)
- `DATABASE_URL`: PostgreSQL connection string
- `BASE_LIEFERANDO_URL`: Base URL for scraping

## Database Management

Reset the database:
```bash

docker exec -it lanch-web-1 python scripts/reset_db.py
```


## Important Notes

- The scraper works best with currently open restaurants
- Searching closed restaurants may result in longer processing times
- Restaurant slugs can be found in the Lieferando.de URL for the restaurant


## Troubleshooting

1. If the API returns 404:
   - Verify the restaurant slug is correct
   - Check if the restaurant is currently open

2. If the database is not updating:
   - Check Docker logs: `docker-compose logs -f`
   - Verify the scheduler is running
   - Reset the database if needed

## Development

To modify the scraping interval:
```python
# In app/config.py
SCRAPING_INTERVAL_MINUTES: int = 60
```

## License

MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.