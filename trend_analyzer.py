"""
Autonomous Trend Analyzer
Evaluates historical telemetry snapshots from the memory vault to detect 
gradual 'code rot' (complexity creep or coverage decay) before limits are breached.
Governing Authority: Governing Officer Tarwater
"""

import os
import json
import base64
import logging
import requests

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


def analyze_repository_trends(target_repo: str) -> None:
    """Analyzes historical snapshots to detect degrading trends in complexity or test coverage."""
    headers = get_github_headers()
    filename = f"data/telemetry_{target_repo.replace('/', '_')}.json"
    
    url = f"{GITHUB_API_URL}/repos/{VAULT_REPO}/contents/{filename}"
    resp = requests.get(url, headers=headers, timeout=15)

    if resp.status_code != 200:
        logging.info(f"No historical telemetry found yet for {target_repo}.")
        return

    file_data = resp.json()
    history = json.loads(base64.b64decode(file_data["content"]).decode("utf-8"))

    if len(history) < 3:
        logging.info(f"Insufficient history ({len(history)} snapshots) for trend analysis on {target_repo}.")
        return

    recent = history[-5:] # Look at last 5 data points
    complexities = [s["complexity"] for s in recent]
    coverages = [s["coverage"] for s in recent]

    # Check for steady complexity increase (creep)
    is_complexity_creeping = all(complexities[i] <= complexities[i+1] for i in range(len(complexities)-1)) and (complexities[-1] > complexities[0])
    # Check for steady coverage decline
    is_coverage_declining = all(coverages[i] >= coverages[i+1] for i in range(len(coverages)-1)) and (coverages[0] > coverages[-1])

    if is_complexity_creeping:
        logging.warning(f"⚠️ PROACTIVE ALERT: Complexity creep detected across recent snapshots for {target_repo}!")
    
    if is_coverage_declining:
        logging.warning(f"⚠️ PROACTIVE ALERT: Test coverage decay detected across recent snapshots for {target_repo}!")

    if not is_complexity_creeping and not is_coverage_declining:
        logging.info(f"✅ Telemetry trend stable for {target_repo}. No proactive degradation detected.")


if __name__ == "__main__":
    import sys
    repo = sys.argv[1] if len(sys.argv) > 1 else "Pat333-ux/autonomous-governance-core"
    analyze_repository_trends(repo)
