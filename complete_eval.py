"""
complete_eval.py
================
Completes the evaluation for remaining URLs, computes final metrics,
and generates a clean final_metrics.json file for paper generation.

Run: python3 complete_eval.py
"""
import os, sys, json, math, time, requests
import pandas as pd
import numpy as np
from urllib.parse import urlparse

# ── Mistral via Ollama ────────────────────────────────────────────────────────
OLLAMA_BASE_URL = "http://localhost:11434"
MISTRAL_MODEL   = "mistral"

DATASET_PATH  = "phishing_dataset.csv"
RESULTS_PATH  = "evaluated_results_revised.csv"
METRICS_PATH  = "final_metrics.json"

SYSTEM_PROMPT = (
    "You are an expert cybersecurity threat analyst specialising in phishing URL detection. "
    "Analyse the provided URL and determine whether it is a phishing attack or safe. "
    "Respond ONLY with a valid JSON object containing exactly two keys:\n"
    "  1. \"prediction\": integer 1 if phishing, 0 if safe.\n"
    "  2. \"reason\": a concise one-sentence justification."
)


def extract_url_features(url: str) -> dict:
    try:
        parsed = urlparse(url if url.startswith("http") else "http://" + url)
        hostname = parsed.hostname or ""
        path     = parsed.path or ""
        query    = parsed.query or ""
    except Exception:
        return {k: 0 for k in [
            "url_len","hostname_len","path_len","query_len","num_dots",
            "num_hyphens","num_underscores","num_slashes","num_at",
            "num_percent","has_ip","subdomain_count","suspicious_tld",
            "brand_in_path","has_https","url_entropy"
        ]}

    def entropy(s):
        if not s: return 0.0
        counts = {}
        for c in s:
            counts[c] = counts.get(c, 0) + 1
        probs = [v / len(s) for v in counts.values()]
        return -sum(p * math.log2(p) for p in probs if p > 0)

    tld = hostname.split(".")[-1] if "." in hostname else ""
    suspicious_tlds = {"xyz","top","club","online","site","info","tk","ml","ga","cf","best","live"}
    brands = ["paypal","apple","amazon","google","microsoft","netflix","facebook","instagram",
              "linkedin","twitter","bank","secure","account","login","verify","update"]
    has_ip = int(all(part.isdigit() for part in hostname.split(".")) and len(hostname.split(".")) == 4)

    return {
        "url_len":           len(url),
        "hostname_len":      len(hostname),
        "path_len":          len(path),
        "query_len":         len(query),
        "num_dots":          url.count("."),
        "num_hyphens":       url.count("-"),
        "num_underscores":   url.count("_"),
        "num_slashes":       url.count("/"),
        "num_at":            url.count("@"),
        "num_percent":       url.count("%"),
        "has_ip":            has_ip,
        "subdomain_count":   max(0, len(hostname.split(".")) - 2),
        "suspicious_tld":    int(tld in suspicious_tlds),
        "brand_in_path":     int(any(b in (path + query).lower() for b in brands)),
        "brand_in_host":     int(any(b in hostname.lower() for b in brands)),
        "url_entropy":       entropy(url),
        "has_https":         int(url.lower().startswith("https")),
    }


def wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple:
    if n == 0: return 0.0, 0.0
    p_hat = successes / n
    denom = 1 + z**2 / n
    centre = (p_hat + z**2 / (2 * n)) / denom
    spread = z * math.sqrt(p_hat * (1 - p_hat) / n + z**2 / (4 * n**2)) / denom
    return max(0.0, centre - spread), min(1.0, centre + spread)


def metrics_dict(y_true, y_pred, name):
    n  = len(y_true)
    tp = int(((y_pred == 1) & (y_true == 1)).sum())
    tn = int(((y_pred == 0) & (y_true == 0)).sum())
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())
    acc    = round((tp + tn) / n, 4)
    prec   = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
    recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
    f1     = round(2 * prec * recall / (prec + recall), 4) if (prec + recall) > 0 else 0.0
    acc_lo,  acc_hi  = [round(x, 4) for x in wilson_ci(tp + tn, n)]
    prec_lo, prec_hi = [round(x, 4) for x in wilson_ci(tp, tp + fp)]
    rec_lo,  rec_hi  = [round(x, 4) for x in wilson_ci(tp, tp + fn)]
    return {
        "model": name, "n": n,
        "accuracy": acc, "accuracy_ci": [acc_lo, acc_hi],
        "precision": prec, "precision_ci": [prec_lo, prec_hi],
        "recall": recall, "recall_ci": [rec_lo, rec_hi],
        "f1": f1, "tp": tp, "tn": tn, "fp": fp, "fn": fn
    }


def evaluate_mistral(url: str, max_retries: int = 3) -> tuple:
    import re
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
            resp = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, timeout=60)
            resp.raise_for_status()
            raw = resp.json()["message"]["content"].strip()
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
            data = json.loads(raw)
            return int(data.get("prediction", 0)), str(data.get("reason", "")).strip()
        except Exception as e:
            backoff = 2 ** attempt
            print(f"  [Mistral attempt {attempt+1}] {e}. Retrying in {backoff}s...")
            time.sleep(backoff)
    return -1, "Mistral unavailable"


def main():
    # Load dataset
    df = pd.read_csv(DATASET_PATH)
    df.columns = df.columns.str.strip().str.lower()
    # Normalize URL column to 'content'
    for c in df.columns:
        if c == "url" and "content" not in df.columns:
            df = df.rename(columns={"url": "content"})
    print(f"Dataset: {len(df)} rows | columns: {df.columns.tolist()}")

    # ── RF Baseline with 5-fold CV ──────────────────────────────────────────
    print("\n[Step 1] Training RF baseline with 5-fold cross-validation...")
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import cross_val_score, StratifiedKFold

    feats = pd.DataFrame([extract_url_features(u) for u in df["content"]])
    labels = df["label"].values
    clf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(clf, feats, labels, cv=cv, scoring="f1")
    cv_acc    = cross_val_score(clf, feats, labels, cv=cv, scoring="accuracy")
    print(f"RF 5-fold F1:       {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    print(f"RF 5-fold Accuracy: {cv_acc.mean():.4f} ± {cv_acc.std():.4f}")

    # Train on full data for prediction column
    clf.fit(feats, labels)
    df["rf_pred"] = clf.predict(feats).tolist()

    # Compute RF metrics using out-of-fold predictions (honest evaluation)
    from sklearn.model_selection import cross_val_predict
    rf_oof = cross_val_predict(clf, feats, labels, cv=cv)
    rf_metrics = metrics_dict(labels, rf_oof, "Random Forest (5-fold OOF)")

    print(f"\nRF OOF Metrics:")
    print(f"  Accuracy:  {rf_metrics['accuracy']} [{rf_metrics['accuracy_ci'][0]}, {rf_metrics['accuracy_ci'][1]}]")
    print(f"  F1:        {rf_metrics['f1']}")
    print(f"  5-fold CV F1 mean: {cv_scores.mean():.4f}")

    rf_metrics["cv_f1_mean"] = round(float(cv_scores.mean()), 4)
    rf_metrics["cv_f1_std"]  = round(float(cv_scores.std()), 4)
    rf_metrics["cv_acc_mean"] = round(float(cv_acc.mean()), 4)

    # ── Complete Mistral evaluation ──────────────────────────────────────────
    print("\n[Step 2] Completing Mistral evaluation for remaining URLs...")

    # Load existing results
    if os.path.exists(RESULTS_PATH) and os.path.getsize(RESULTS_PATH) > 0:
        existing = pd.read_csv(RESULTS_PATH)
        existing.columns = existing.columns.str.strip().str.lower()
        done_ids = set(existing["id"].tolist()) if "id" in existing.columns else set()
        done_count = len(existing[existing.get("mistral_pred", pd.Series([-1]*len(existing))) != -1]) if "mistral_pred" in existing.columns else 0
        print(f"  Already evaluated: {done_count} / {len(df)} rows")
    else:
        existing = pd.DataFrame()
        done_ids = set()
        done_count = 0

    # Find remaining rows
    if "id" in df.columns:
        remaining = df[~df["id"].isin(done_ids)]
    else:
        remaining = df.iloc[done_count:]

    rows_to_add = []
    for idx, row in remaining.iterrows():
        url   = row["content"]
        label = row["label"]
        row_id = row.get("id", idx)
        rnum  = idx + 1

        m_pred, m_reason = evaluate_mistral(url)
        rf_p = int(clf.predict([extract_url_features(url)])[0])
        rows_to_add.append({
            "id": row_id, "content": url, "label": int(label),
            "rf_pred": rf_p, "gsb_pred": -1,
            "mistral_pred": m_pred, "mistral_reason": m_reason,
            "gemini_pred": -1, "gemini_reason": ""
        })
        print(f"  [{rnum}/{len(df)}] label={label} Mistral={m_pred} RF={rf_p}")
        time.sleep(0.5)

    # Combine existing + new results
    if rows_to_add:
        new_df = pd.DataFrame(rows_to_add)
        combined = pd.concat([existing, new_df], ignore_index=True) if not existing.empty else new_df
        combined.to_csv(RESULTS_PATH, index=False)
        print(f"  Saved {len(combined)} rows to {RESULTS_PATH}")
    else:
        combined = existing
        print("  No new rows to add.")

    # ── Compute Final Metrics ───────────────────────────────────────────────
    print("\n[Step 3] Computing final metrics...")
    final = pd.read_csv(RESULTS_PATH)

    # Mistral
    m_valid = final[final["mistral_pred"] != -1]
    m_metrics = metrics_dict(m_valid["label"].values, m_valid["mistral_pred"].values, "Mistral-7B (Open-Source, Zero-Shot)")

    # RF (OOF)
    # We'll use the labels from final df aligned with df
    all_metrics = {
        "dataset_size": len(df),
        "phishing_count": int((df["label"] == 1).sum()),
        "benign_count": int((df["label"] == 0).sum()),
        "models": [rf_metrics, m_metrics]
    }

    print("\n=== FINAL RESULTS ===")
    for m in all_metrics["models"]:
        print(f"\n{m['model']}")
        print(f"  Accuracy:  {m['accuracy']} [{m['accuracy_ci'][0]}, {m['accuracy_ci'][1]}]")
        print(f"  Precision: {m['precision']} [{m['precision_ci'][0]}, {m['precision_ci'][1]}]")
        print(f"  Recall:    {m['recall']} [{m['recall_ci'][0]}, {m['recall_ci'][1]}]")
        print(f"  F1-Score:  {m['f1']}")
        print(f"  TP={m['tp']} TN={m['tn']} FP={m['fp']} FN={m['fn']}")

    with open(METRICS_PATH, "w") as f:
        json.dump(all_metrics, f, indent=2)
    print(f"\nMetrics saved to: {METRICS_PATH}")


if __name__ == "__main__":
    main()
