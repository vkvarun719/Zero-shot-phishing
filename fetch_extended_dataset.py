# fetch_extended_dataset.py
"""Utility script to generate a balanced 5,000‑URL benchmark for phishing detection.

The script performs three actions:
1. Download recent phishing URLs from PhishTank and OpenPhish.
2. Sample benign URLs from the Tranco top‑1M list.
3. Combine, shuffle, and write a CSV file (`phishing_dataset.csv`) with columns:
   `id,url,label` where `label` is `1` for phishing and `0` for benign.

The script uses only the Python standard library and the optional ``requests``
package. If ``requests`` is unavailable, it falls back to ``urllib.request``.

Run the script with::
    python fetch_extended_dataset.py

The resulting CSV will be placed in the repository root.
"""

import argparse
import csv
import os
import random
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Helper for downloading data (requests preferred, urllib fallback)
# ---------------------------------------------------------------------------
def _download(url: str) -> bytes:
    """Download content from *url* and return as bytes."""
    try:
        import requests
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.content
    except Exception:
        from urllib.request import urlopen
        with urlopen(url, timeout=30) as f:
            return f.read()

# ---------------------------------------------------------------------------
# 1. Phishing URLs – PhishTank and OpenPhish
# ---------------------------------------------------------------------------
PHISHTANK_URL = "https://data.phishtank.com/data/online-valid.csv"
OPENPHISH_URL = "https://openphish.com/feed.txt"

def _load_phishtank(limit: int) -> list[str]:
    print("[PhishTank] Downloading CSV…")
    data = _download(PHISHTANK_URL).decode("utf-8", errors="ignore")
    rows = []
    for line in data.splitlines()[1:]:  # skip header
        parts = line.split(",")
        if len(parts) < 2:
            continue
        url = parts[1].strip().strip('"')
        rows.append(url)
        if len(rows) >= limit:
            break
    return rows


def _load_openphish(limit: int) -> list[str]:
    print("[OpenPhish] Downloading feed…")
    data = _download(OPENPHISH_URL).decode("utf-8", errors="ignore")
    urls = [ln.strip() for ln in data.splitlines() if ln.strip().startswith("http")]
    random.shuffle(urls)
    return urls[:limit]

# ---------------------------------------------------------------------------
# 2. Benign URLs – Tranco top‑1M list (plain CSV hosted on GitHub)
# ---------------------------------------------------------------------------
TRUCO_URL = "https://tranco-list.eu/download/daily/top-1m.csv.zip"

def _load_tranco(limit: int) -> list[str]:
    print("[Tranco] Downloading top‑1M list…")
    raw = _download(TRUCO_URL)
    # If the URL points to a zip, extract the CSV inside
    if TRUCO_URL.lower().endswith('.zip'):
        import zipfile, io as _io
        with zipfile.ZipFile(_io.BytesIO(raw)) as z:
            # Choose the first .csv file inside the zip
            csv_name = next((n for n in z.namelist() if n.lower().endswith('.csv')), None)
            if csv_name is None:
                raise RuntimeError('No CSV found in Tranco zip')
            data = z.read(csv_name).decode('utf-8', errors='ignore')
    else:
        data = raw.decode('utf-8', errors='ignore')
    rows = []
    for line in data.splitlines():
        domain = line.split(',')[0]
        rows.append(f"https://{domain}")
        if len(rows) >= limit:
            break
    return rows

# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------
def build_dataset(phish_per_class: int = 2500, legit_per_class: int = 2500, out: str = "phishing_dataset.csv"):
    random.seed(42)
    # Phishing URLs – split equally between the two sources if possible
    half = phish_per_class // 2
    phish = _load_phishtank(half) + _load_openphish(phish_per_class - len(_load_phishtank(half)))
    # Ensure we have the requested count
    if len(phish) < phish_per_class:
        phish += _load_openphish(phish_per_class - len(phish))
    phish = phish[:phish_per_class]

    legit = _load_tranco(legit_per_class)
    if len(legit) < legit_per_class:
        # Fallback: repeat entries to reach the target (unlikely)
        while len(legit) < legit_per_class:
            legit.append(random.choice(legit))
    legit = legit[:legit_per_class]

    dataset = []
    for i, url in enumerate(phish, start=1):
        dataset.append({"id": i, "url": url, "label": 1})
    offset = len(dataset)
    for i, url in enumerate(legit, start=1):
        dataset.append({"id": offset + i, "url": url, "label": 0})

    random.shuffle(dataset)
    out_path = Path(out)
    print(f"Writing {len(dataset)} records to {out_path}")
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "url", "label"])
        writer.writeheader()
        writer.writerows(dataset)
    print("Dataset generation complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate phishing/benign benchmark CSV.")
    parser.add_argument("--phish", type=int, default=2500, help="Number of phishing URLs")
    parser.add_argument("--legit", type=int, default=2500, help="Number of legitimate URLs")
    parser.add_argument("--out", type=str, default="phishing_dataset.csv", help="Output CSV file")
    args = parser.parse_args()
    build_dataset(args.phish, args.legit, args.out)
