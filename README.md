# FastAPI API Monitoring Demo

A small FastAPI service monitored with Prometheus, Grafana, Blackbox Exporter, and Alertmanager. The project includes endpoints and a traffic script for exercising common failure scenarios.

## How it works

- **FastAPI** serves the sample API and exposes request metrics at `/metrics`.
- **Prometheus** scrapes the API and evaluates the rules in `prometheus/alert_rules.yml`.
- **Blackbox Exporter** probes the API's `/health` endpoint.
- **Grafana** loads the dashboard from `grafana/dashboards/`.
- **Alertmanager** sends notifications for firing alerts.

Docker Compose starts all five services.

## Requirements

- Docker Desktop with Docker Compose
- Python 3.10+ and `pip` to run the failure simulation script from your computer

## Start the project

From the project directory, run:

```bash
docker compose up --build
```

The first build may take a few minutes. Open these pages once the containers are running:

| Service | Address | Sign-in |
|---|---|---|
| FastAPI docs | http://localhost:8000/docs | — |
| Grafana | http://localhost:3000 | `admin` / `admin` |
| Prometheus | http://localhost:9090 | — |
| Alertmanager | http://localhost:9093 | — |

The Grafana credentials are for local demo use only. Change them before exposing Grafana beyond your machine.

### Run the API without Docker

Create and activate a virtual environment, then install the dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

For macOS or Linux, activate the environment with `source .venv/bin/activate` instead.

## API endpoints

| Endpoint | Purpose |
|---|---|
| `GET /health` | Health check used by the Blackbox probe |
| `GET /users`, `GET /products` | Sample API responses |
| `GET /protected` | Example API-key check; returns 401 if the configured key is missing or incorrect |
| `GET /simulate-error` | Deliberately raises an error to produce an HTTP 500 |
| `GET /simulate-timeout` | Waits five seconds by default before responding |
| `GET /simulate-rate-limit` | Deliberately returns HTTP 429 |
| `GET /metrics` | Prometheus metrics |

The protected endpoint expects the `X-API-Key` header. Use the `API_KEY` value configured for your running API; do not put real keys in this README or share them.

## Alert notifications

Alertmanager is configured in `alertmanager/alertmanager.yml`. To enable notifications:

1. Create a Slack incoming webhook and set `slack_api_url` to its URL.
2. For Gmail, enable 2-Step Verification, create an App Password, and set `smtp_auth_username`, `smtp_auth_password`, `smtp_from`, and the receiver's `to` address.
3. Restart Alertmanager with `docker compose restart alertmanager`.

The tracked configuration currently contains credential-like values. Do not use them: revoke or rotate them, then configure your own credentials. Treat these values as secrets and do not commit them to Git.

## Dashboard and alerts

The provisioned Grafana dashboard is named **API Monitoring Dashboard**. It displays the health probe status and uptime, request totals and failures, error trends, and response time by endpoint.

Prometheus evaluates these alerts from `prometheus/alert_rules.yml`:

| Alert | Trigger |
|---|---|
| `ApiDown` | The `/health` probe fails for 30 seconds |
| `ServiceHealthFailure` | Prometheus cannot scrape the API for 30 seconds |
| `HighResponseTime` | An endpoint's average response time exceeds 3 seconds |
| `Http500Errors` | A 5xx response is recorded |
| `HighFailureRate` | 4xx and 5xx responses exceed 10% of requests |
| `AuthenticationFailures` | More than three 401/403 responses occur in a minute |
| `RateLimitExceeded` | More than three 429 responses occur in a minute |

## Exercise the failure scenarios

Install the Python dependencies if you have not already:

```bash
pip install -r requirements.txt
```

Run healthy traffic first, then choose a scenario:

```bash
python tests/simulate_failures.py normal --duration 60
python tests/simulate_failures.py auth
python tests/simulate_failures.py timeout
python tests/simulate_failures.py error
python tests/simulate_failures.py ratelimit
```

The script sends requests to `http://localhost:8000`. Keep the API running while using it. Scenarios run for 90 seconds by default; pass `--duration` to change that. Use `all` to run each failure scenario in sequence.

To test an outage alert, stop and restart the API container:

```bash
docker compose stop api
docker compose start api
```

Check Grafana for metrics, Prometheus at http://localhost:9090/alerts for alert state, and `docker compose logs api` for API logs. Alert rules with a sustained-failure window need time to fire.

## Troubleshooting

- **Prometheus target is down:** Check http://localhost:9090/targets and run `docker compose logs api`.
- **Grafana has no data:** Confirm the containers are running and generate some traffic with the `normal` scenario.
- **An alert is pending:** Keep the condition active until its configured `for` duration has elapsed.
- **No Slack or email notification:** Check `docker compose logs alertmanager` and verify your notification settings.
- **A port is already in use:** Stop the other process or change the host-side port in `docker-compose.yml`.

Useful commands:

```bash
docker compose ps
docker compose logs -f api
docker compose down
```

## Project files

```text
app/main.py                    FastAPI application
prometheus/                    Scrape configuration and alert rules
alertmanager/alertmanager.yml  Notification configuration
blackbox/blackbox.yml          Health-probe configuration
grafana/                       Provisioning and dashboard
tests/simulate_failures.py     Traffic and failure scenarios
docs/RCA_report.md             Notes for recording test results
screenshots/                   Place for screenshots
```