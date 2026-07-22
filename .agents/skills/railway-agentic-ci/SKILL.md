---
name: railway-agentic-ci
description: Agentic CI/CD orchestration and automated error diagnosis using Railway CLI and AI Agent bridge.
---

# Railway Agentic CI/CD Protocol

This skill guides the agent in using `railway` CLI as the primary cloud execution workspace and automated error resolution bridge between GitHub Actions and Railway infrastructure.

## Key Capabilities

1. **Environment Status Inspection**:
   - `railway status`
   - Inspect active services (`Demo_geofeedback`, `geofeedback-worker`, `geofeedback-scheduler`, `PostGIS`, `Redis`, `Loki`, `Tempo`, `Grafana`).

2. **Cloud Executed Tests & Secrets**:
   - `python scripts/qa/railway_agentic_ci.py --check-status`
   - `python scripts/qa/railway_agentic_ci.py --run-tests`
   - `railway run <command>`: Executes commands using secrets and variables from the active Railway project environment.

3. **Log Diagnosis & Extraction**:
   - `railway logs --service <service_name>`
   - `railway logs --service <service_name> --build`
   - `python scripts/qa/railway_agentic_ci.py --fetch-logs <service_name>`

4. **Self-Healing PR Protocol**:
   - When a test or deployment fails on Railway or GitHub:
     1. Extract error traceback via `railway logs` or `gh run view <id> --log-failed`.
     2. Identify exact root cause lines.
     3. Create feature branch `fix/<description>`.
     4. Apply patch and verify locally.
     5. Push branch and open PR via `$env:GITHUB_TOKEN=''; gh pr create`.
     6. Merge PR via `gh pr merge --squash --delete-branch`.
