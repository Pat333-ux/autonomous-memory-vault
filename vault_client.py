"""
Autonomous Memory Vault Client
Manages persistent cross-repository state, historical telemetry snapshots,
and executive audit ledgers.
Governing Authority: Governing Officer Tarwater
"""

import os
import json
import base64
import logging
import requests
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

GITHUB_API_URL = "https://api.github.com"
VAULT_REPO = "Pat333-ux/autonomous-memory-vault"


def get_github_headers() -> dict:
    token = os.getenv("GH_PAT") or os.getenv("GITHUB_TOKEN")
    if not token:
        raise EnvironmentError("Missing GH_PAT or GITHUB_TOKEN environment variable.")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }


def record_telemetry_snapshot(target_repo: str, complexity_score: float, coverage_percent: float) -> None:
    """Records a historical telemetry data point for a governed repository into the vault."""
    headers = get_github_headers()
    filename = f"data/telemetry_{target_repo.replace('/', '_')}.json"
    
    # 1. Fetch existing data if present
    url = f"{GITHUB_API_URL}/repos/{VAULT_REPO}/contents/{filename}"
    resp = requests.get(url, headers=headers, timeout=15)
    
    history = []
    file_sha = None

    if resp.status_code == 200:
        file_data = resp.json()
        file_sha = file_data.get("sha")
        decoded = base64.b64decode(file_data["content"]).decode("utf-8")
        try:
            history = json.loads(decoded)
        except json.JSONDecodeError:
            history = []

    # 2. Append new snapshot
    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "complexity": complexity_score,
        "coverage": coverage_percent
    }
    history.append(snapshot)

    # Keep only the last 100 snapshots to prevent bloat
    if len(history) > 100:
        history = history[-100:]

    # 3. Commit updated history back to the vault
    updated_content = json.dumps(history, indent=2)
    commit_payload = {
        "message": f"[MEMORY-VAULT] Update historical telemetry snapshot for {target_repo}",
        "content": base64.b64encode(updated_content.encode("utf-8")).decode("utf-8")
    }
    if file_sha:
        commit_payload["sha"] = file_sha

    put_resp = requests.put(url, headers=headers, json=commit_payload, timeout=30)
    if put_resp.status_code in (200, 201):
        logging.info(f"Successfully recorded telemetry snapshot for {target_repo} in memory vault.")
    else:
        logging.error(f"Failed to record telemetry snapshot: {put_resp.text}")


if __name__ == "__main__":
    import sys
    repo = sys.argv[1] if len(sys.argv) > 1 else "Pat333-ux/autonomous-governance-core"
    comp = float(sys.argv[2]) if len(sys.argv) > 2 else 4.5
    cov = float(sys.argv[3]) if len(sys.argv) > 3 else 92.0
    record_telemetry_snapshot(repo, comp, cov)
