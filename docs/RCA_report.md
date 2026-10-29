# Failure Testing & Root Cause Analysis Report


## Scenario 1: Invalid API authentication
- Command run: python tests/simulate_failures.py auth --duration 120
- Time started / alert fired: 10:05 / 10:07
- Detection (metric/panel): Error Trend panel showed 401 spike; Prometheus status="401" count increased
- Alert received (Slack/Email screenshot): see s1-slack.png, s1-email.png
- Root cause: Client sent wrong X-API-Key header to /protected, API returned 401
- Resolution: Use the correct API key

## Scenario 2: API timeout
- Command run: python tests/simulate_failures.py timeout --duration 120
- Time started / alert fired: 10:10 / 10:12
- Detection: Avg Response Time by Endpoint panel showed ~5s for /simulate-timeout (threshold 3s)
- Alert received: see s2-email.png
- Root cause: Endpoint intentionally delays response by 5 seconds
- Resolution: Optimize the slow dependency, add caching and client-side timeouts

## Scenario 3: Server error (HTTP 500)
- Command run: python tests/simulate_failures.py error --duration 120
- Time started / alert fired: 10:13 / 10:15
- Detection: 500 status spike in Error Trend
- Alert received: see s3-slack.png, s3-email.png
- Root cause: Unhandled RuntimeError
- Resolution: Fix the failing code path, add error handling

## Scenario 4: Rate limit exceeded (HTTP 429)
- Command run: python tests/simulate_failures.py ratelimit --duration 120
- Time started / alert fired: 10:20 / 10:22
- Detection: RateLimitExceeded and HighFailureRate fired
- Alert received: see s4-slack.png, s4-email.png
- Root cause: Client sent requests faster than the allowed limit
- Resolution: Add backoff/retry logic in client, reduce request frequency or raise the limit

## Scenario 5: API downtime
- Command run (`docker compose stop api`):
- Alert received: see s5-email-1.png
- Resolution (`docker compose start api`):
