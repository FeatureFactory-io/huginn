# Huginn

Human-AI OODA composite for engineering PMs. Ingests development signals hourly, computes Master Variables (TRANSPARENCY, THROUGHPUT, CYCLE TIME, REWORK, QUALITY, COMPLEXITY, CONTRIBUTION), and produces a daily SitRep at morning planning.

## Quick Start

```bash
make provision   # Install prerequisites & dependencies
make run         # Start all services via Docker Compose
```

Then open http://localhost:8000 in your browser.

## Development

| Command | Description |
|---|---|
| `make provision` | Install all prerequisites |
| `make run` | Start all services (Docker Compose) |
| `make test` | Run all tests |
| `make test-unit` | Run unit tests only |
| `make test-integration` | Run integration tests only |
| `make lint` | Run ruff linter |
| `make format` | Auto-format code with ruff |
| `make shell` | Django shell in web container |
| `make logs` | Tail all container logs |
| `make clean` | Stop containers, remove volumes |
| `make help` | Show all available targets |

## Documentation

- [System Architecture Overview](docs/architecture/SAO.md)
- [Architecture Decision Records](docs/architecture/ADRs/)
