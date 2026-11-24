"""
auto_eval_revised.py
====================
Revised evaluation harness addressing NCDTE-26 reviewer comments:
  R1 → Supports large datasets (PhishTank/OpenPhish + Tranco); reports 95% CI
  R2 → Adds URL-feature baseline (Random Forest) and Google Safe Browsing stub
  R3 → Adds Mistral 7B via Ollama (open-source LLM) alongside Gemini

Authors:
  Asst. Prof. Avinash N Rao   <avinashrao@rvitm.edu.in>
  Varun Kumar K C             <varunkumarkc.cs22@rvitm.edu.in>
  Vinay Prakash A P           <vinayprakashap.cs22@rvitm.edu.in>
  Rishita Raveendra Chikkaraddi <rishita.cs23@rvitm.edu.in>
  Lakshmipathy A S            <lakshmipathyas.cs23@rvitm.edu.in>
"""

import os
import sys
import time
import json
import re
import math
import requests
import hashlib
import numpy as np
import pandas as pd
from urllib.parse import urlparse
from dotenv import load_dotenv
from scipy import stats

# ── Gemini (closed model, kept for reproducibility) ──────────────────────────
import google.generativeai as genai

# ── Open-source model: Mistral 7B via Ollama ─────────────────────────────────
# Install: `brew install ollama && ollama pull mistral`
OLLAMA_BASE_URL = "http://localhost:11434"
MISTRAL_MODEL   = "mistral"           # open-source, runs locally
GEMINI_PRIMARY  = "gemini-2.0-flash"  # closed, cloud
GEMINI_FALLBACK = "gemini-1.5-flash-lite"

DATASET_PATH    = "phishing_dataset.csv"
OUTPUT_PATH     = "evaluated_results_revised.csv"

# ═════════════════════════════════════════════════════════════════════════════
# SECTION 1 — URL Feature Extraction  (Reviewer #2 baseline)
# ═════════════════════════════════════════════════════════════════════════════

def extract_url_features(url: str) -> dict:
    """Extracts 15 lexical/structural URL features used by the RF baseline."""
    try:
        parsed = urlparse(url if url.startswith("http") else "http://" + url)
        hostname = parsed.hostname or ""
        path     = parsed.path or ""
        query    = parsed.query or ""
        full     = url
    except Exception:
        return {k: 0 for k in _FEATURE_KEYS}

    # Shannon entropy of full URL
    def entropy(s):
        if not s:
            return 0.0
        counts = {}
        for c in s:
            counts[c] = counts.get(c, 0) + 1
        probs = [v / len(s) for v in counts.values()]
        return -sum(p * math.log2(p) for p in probs if p > 0)

    tld = hostname.split(".")[-1] if "." in hostname else ""
    suspicious_tlds = {"xyz","top","club","online","site","info","tk","ml","ga","cf"}
    brand_tokens = {"paypal","amazon","apple","microsoft","google","facebook","netflix","bank","login","secure","verify","account"}

    dots_in_host    = hostname.count(".")
    has_ip          = 1 if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", hostname) else 0
    url_len         = len(full)
    hostname_len    = len(hostname)
    path_len        = len(path)
    digit_ratio     = sum(c.isdigit() for c in full) / max(len(full), 1)
    special_ratio   = sum(not c.isalnum() for c in full) / max(len(full), 1)
    has_at          = 1 if "@" in full else 0
    has_double_slash= 1 if "//" in path else 0
    num_subdomains  = max(dots_in_host - 1, 0)
    suspicious_tld  = 1 if tld in suspicious_tlds else 0
    brand_in_path   = 1 if any(b in (path + query).lower() for b in brand_tokens) else 0
    brand_in_host   = 1 if any(b in hostname.lower() for b in brand_tokens) else 0
    url_entropy     = entropy(full)
    has_https       = 1 if parsed.scheme == "https" else 0

    return {
        "dots_in_host": dots_in_host,
        "has_ip": has_ip,
        "url_len": url_len,
        "hostname_len": hostname_len,
        "path_len": path_len,
        "digit_ratio": digit_ratio,
        "special_ratio": special_ratio,
        "has_at": has_at,
        "has_double_slash": has_double_slash,
        "num_subdomains": num_subdomains,
        "suspicious_tld": suspicious_tld,
        "brand_in_path": brand_in_path,
        "brand_in_host": brand_in_host,
        "url_entropy": url_entropy,
        "has_https": has_https,
    }

_FEATURE_KEYS = list(extract_url_features("http://example.com").keys())


def train_rf_baseline(df: pd.DataFrame):
    """Trains a Random Forest classifier on URL features (Reviewer #2 R2)."""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import cross_val_score

    feats = pd.DataFrame([extract_url_features(u) for u in df["content"]])
    labels = df["label"].values
    clf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
    # 5-fold CV scores (reported in paper)
    cv_scores = cross_val_score(clf, feats, labels, cv=5, scoring="f1")
    print(f"\n[RF Baseline] 5-fold F1: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    clf.fit(feats, labels)
    return clf, feats.columns.tolist()


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Google Safe Browsing Lookup API  (Reviewer #2 baseline)
# ═════════════════════════════════════════════════════════════════════════════

def check_gsb(url: str, api_key: str | None) -> int:
    """
    Returns 1 if GSB flags the URL as unsafe, 0 if safe, -1 if key missing.
    API: https://safebrowsing.googleapis.com/v4/threatMatches:find
    """
    if not api_key:
        return -1  # skip quietly — GSB key is optional
    endpoint = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={api_key}"
    payload = {
        "client": {"clientId": "ncdte26-phishing-eval", "clientVersion": "2.0"},
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}],
        },
    }
    try:
        r = requests.post(endpoint, json=payload, timeout=5)
        if r.status_code == 200:
            return 1 if r.json().get("matches") else 0
    except Exception:
        pass
    return -1


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Open-Source LLM: Mistral 7B via Ollama  (Reviewer #3)
# ═════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = (
    "You are an expert cybersecurity threat analyst specialising in phishing URL detection. "
    "Analyse the provided URL and determine whether it is a phishing attack or safe. "
    "Respond ONLY with a valid JSON object containing exactly two keys:\n"
    "  1. \"prediction\": integer 1 if phishing, 0 if safe.\n"
    "  2. \"reason\": a concise one-sentence justification."
)


def _parse_json_response(raw: str) -> tuple[int, str]:
    raw = raw.strip()
    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    data = json.loads(raw)
    return int(data.get("prediction", 0)), str(data.get("reason", "")).strip()


def evaluate_mistral(url: str, max_retries: int = 3) -> tuple[int, str]:
    """
    Zero-shot classification via local Mistral 7B (open-source).
    Requires Ollama running: `ollama serve` and `ollama pull mistral`.
    """
    payload = {
        "model": MISTRAL_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": f'URL to analyse: "{url}"'},
        ],
        "stream": False,
        "format": "json",
    }
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            raw = resp.json()["message"]["content"]
            return _parse_json_response(raw)
        except Exception as e:
            backoff = 2 ** attempt
            print(f"  [Mistral attempt {attempt+1}] {e}. Retrying in {backoff}s...")
            time.sleep(backoff)
    return -1, "Mistral unavailable after retries"


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Gemini (closed) with quota failover  (unchanged from v1)
# ═════════════════════════════════════════════════════════════════════════════

class DailyQuotaExhaustedException(Exception):
    pass

class ServerUnavailableException(Exception):
    pass


def evaluate_gemini(client, model_name: str, url: str, max_retries: int = 5) -> tuple[int, str]:
    prompt = (
        f"{SYSTEM_PROMPT}\n\nContent to analyse:\n\"\"\"{url}\"\"\""
    )
    model = genai.GenerativeModel(model_name)
    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json"
                ),
            )
            return _parse_json_response(response.text or "")
        except Exception as e:
            err = str(e)
            # Daily quota
            if any(k in err.upper() for k in ("RESOURCE_EXHAUSTED", "429")):
                if any(k in err.lower() for k in ("per day", "perday", "requests per day")):
                    raise DailyQuotaExhaustedException(f"Daily quota: {model_name}")
                wait = 20.0 + attempt * 10.0
                print(f"  [429 RPM] Cooling {wait:.0f}s ...")
                time.sleep(wait)
                continue
            # 503
            if any(k in err.upper() for k in ("503", "UNAVAILABLE", "DEMAND")):
                if attempt < max_retries - 1:
                    backoff = 3.0 * (2 ** attempt)
                    print(f"  [503] {model_name} busy. Retry in {backoff:.1f}s ...")
                    time.sleep(backoff)
                    continue
                raise ServerUnavailableException(f"503 persisted: {model_name}")
            raise
    raise RuntimeError(f"Max retries exceeded: {model_name}")


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Confidence Interval Utility  (Reviewer #1)
# ═════════════════════════════════════════════════════════════════════════════

def wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a proportion (95% CI by default)."""
    if n == 0:
        return 0.0, 0.0
    p_hat = successes / n
    denom = 1 + z**2 / n
    centre = (p_hat + z**2 / (2 * n)) / denom
    spread = z * math.sqrt(p_hat * (1 - p_hat) / n + z**2 / (4 * n**2)) / denom
    return max(0.0, centre - spread), min(1.0, centre + spread)


def report_metrics(df: pd.DataFrame, model_col: str = "predicted_label"):
    """Prints classification report with 95% Wilson CIs on key metrics."""
    from sklearn.metrics import classification_report, confusion_matrix

    valid = df[df[model_col] != -1].copy()
    if len(valid) == 0:
        print("No valid predictions to report.")
        return

    y_true = valid["label"].values
    y_pred = valid[model_col].values
    n = len(y_true)
    tp = int(((y_pred == 1) & (y_true == 1)).sum())
    tn = int(((y_pred == 0) & (y_true == 0)).sum())
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())

    acc    = (tp + tn) / n
    prec   = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1     = 2 * prec * recall / (prec + recall) if (prec + recall) > 0 else 0

    acc_lo,  acc_hi  = wilson_ci(tp + tn, n)
    prec_lo, prec_hi = wilson_ci(tp, tp + fp)
    rec_lo,  rec_hi  = wilson_ci(tp, tp + fn)

    sep = "=" * 60
    print(f"\n{sep}")
    print(f"  PERFORMANCE METRICS  (n={n}, 95% Wilson CI)")
    print(sep)
    print(f"  Accuracy  : {acc:.4f}  [{acc_lo:.4f}, {acc_hi:.4f}]")
    print(f"  Precision : {prec:.4f}  [{prec_lo:.4f}, {prec_hi:.4f}]")
    print(f"  Recall    : {recall:.4f}  [{rec_lo:.4f}, {rec_hi:.4f}]")
    print(f"  F1-Score  : {f1:.4f}")
    print(f"\n  Confusion Matrix (TP={tp}, TN={tn}, FP={fp}, FN={fn})")
    print(confusion_matrix(y_true, y_pred))
    print(sep)


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 6 — MAIN EVALUATION LOOP
# ═════════════════════════════════════════════════════════════════════════════

def main():
    load_dotenv()
    gemini_key = os.getenv("GEMINI_API_KEY")
    gsb_key    = os.getenv("GSB_API_KEY")          # optional

    print("=" * 65)
    print("   ZERO-SHOT PHISHING EVALUATION  —  REVISED v2.0")
    print(f"   Open-source LLM : {MISTRAL_MODEL} (Ollama, local)")
    print(f"   Closed LLM      : {GEMINI_PRIMARY} → fallback {GEMINI_FALLBACK}")
    print(f"   RF Baseline     : scikit-learn RandomForestClassifier")
    print(f"   GSB Baseline    : {'enabled' if gsb_key else 'disabled (set GSB_API_KEY)'}")
    print("=" * 65)

    if not os.path.exists(DATASET_PATH):
        print(f"ERROR: {DATASET_PATH} not found.")
        sys.exit(1)

    df = pd.read_csv(DATASET_PATH)
    df.columns = df.columns.str.strip().str.lower()
    print(f"Loaded {len(df)} samples from {DATASET_PATH}\n")

    # ── 1. Random Forest baseline ────────────────────────────────────────────
    print("[Step 1/3] Training RF URL-feature baseline ...")
    rf_clf, feat_cols = train_rf_baseline(df)
    rf_feats = pd.DataFrame([extract_url_features(u) for u in df["content"]])
    df["rf_pred"] = rf_clf.predict(rf_feats).tolist()

    # ── 2. Google Safe Browsing baseline ────────────────────────────────────
    print("\n[Step 2/3] Running Google Safe Browsing baseline ...")
    gsb_preds = []
    for url in df["content"]:
        gsb_preds.append(check_gsb(url, gsb_key))
        time.sleep(0.05)
    df["gsb_pred"] = gsb_preds

    # ── 3. LLM zero-shot evaluation ─────────────────────────────────────────
    print("\n[Step 3/3] Zero-shot LLM evaluation (Mistral + Gemini) ...")

    if gemini_key:
        genai.configure(api_key=gemini_key)
    gemini_key_valid = bool(gemini_key)
    current_gemini = GEMINI_PRIMARY

    # Resume support
    valid_count = 0
    if os.path.exists(OUTPUT_PATH) and os.path.getsize(OUTPUT_PATH) > 0:
        try:
            prev = pd.read_csv(OUTPUT_PATH)
            valid_count = len(prev[prev["gemini_pred"] != -1])
        except Exception:
            valid_count = 0

    file_has_header = os.path.exists(OUTPUT_PATH) and os.path.getsize(OUTPUT_PATH) > 0
    rows_todo = df.iloc[valid_count:]

    for idx, row in rows_todo.iterrows():
        url   = row["content"]
        label = row["label"]
        rnum  = idx + 1

        # Mistral (open-source)
        m_pred, m_reason = evaluate_mistral(url)

        # Gemini (closed)
        g_pred, g_reason = -1, ""
        if gemini_key_valid:
            while g_pred == -1:
                try:
                    g_pred, g_reason = evaluate_gemini(None, current_gemini, url)
                except DailyQuotaExhaustedException:
                    if current_gemini == GEMINI_PRIMARY:
                        print(f"\n[FAILOVER] Switching to {GEMINI_FALLBACK}")
                        current_gemini = GEMINI_FALLBACK
                    else:
                        g_pred, g_reason = -1, "quota exhausted"
                        break
                except ServerUnavailableException:
                    g_pred, g_reason = -1, "server unavailable"
                    break

        out_row = pd.DataFrame([{
            "id":           row.get("id", idx),
            "content":      url,
            "label":        label,
            "rf_pred":      df.at[idx, "rf_pred"],
            "gsb_pred":     df.at[idx, "gsb_pred"],
            "mistral_pred": m_pred,
            "mistral_reason": m_reason,
            "gemini_pred":  g_pred,
            "gemini_reason": g_reason,
        }])

        out_row.to_csv(OUTPUT_PATH, mode="a", header=not file_has_header, index=False)
        file_has_header = True

        print(
            f"  [{rnum}/{len(df)}] label={label} | "
            f"RF={df.at[idx,'rf_pred']} | "
            f"GSB={df.at[idx,'gsb_pred']} | "
            f"Mistral={m_pred} | "
            f"Gemini={g_pred}"
        )
        time.sleep(4.1)   # ≤ 14 RPM for Gemini free tier

    # ── Final metrics for all models ────────────────────────────────────────
    final = pd.read_csv(OUTPUT_PATH)

    print("\n\n── Random Forest Baseline ──")
    report_metrics(final.rename(columns={"rf_pred": "predicted_label"}))

    print("\n── Mistral 7B (Open-Source, Zero-Shot) ──")
    report_metrics(final.rename(columns={"mistral_pred": "predicted_label"}))

    print("\n── Gemini (Closed, Zero-Shot) ──")
    report_metrics(final.rename(columns={"gemini_pred": "predicted_label"}))

    if gsb_key:
        print("\n── Google Safe Browsing ──")
        report_metrics(final.rename(columns={"gsb_pred": "predicted_label"}))

    print(f"\nAll results saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
