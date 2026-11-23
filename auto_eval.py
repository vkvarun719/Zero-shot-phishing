import os
import sys
import time
import json
import re
import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai import errors
from sklearn.metrics import classification_report, confusion_matrix

PRIMARY_MODEL = "gemini-3.8-flash"
FALLBACK_MODEL = "gemini-3.1-flash-lite"
DATASET_PATH = "phishing_dataset.csv"
OUTPUT_PATH = "evaluated_results.csv"

class DailyQuotaExhaustedException(Exception):
    """Raised when daily free tier quota (RPD) is exhausted for the model."""
    pass

class ServerUnavailableException(Exception):
    """Raised when 503 high demand persists after exponential backoff."""
    pass

def evaluate_single_sample(client, model_name, text_content, max_retries=5):
    """
    Evaluates one sample using the specified model.
    Handles:
    - 503 Server Unavailable / High Demand with exponential backoff (3s, 6s, 12s, 24s...).
    - 429 Rate Limit Per Minute (RPM) with automatic wait and retry.
    - 429 Daily Limit (RPD) by raising DailyQuotaExhaustedException for failover/safeguard.
    """
    prompt = f"""
    You are an expert cybersecurity threat analyst. Analyze the following text or URL to determine if it is a phishing attack or safe.
    
    Content to analyze:
    \"\"\"{text_content}\"\"\"

    Respond ONLY with a valid JSON object containing exactly two keys:
    1. "prediction": integer 1 if phishing, 0 if safe.
    2. "reason": a short 1-sentence justification for the classification.
    """

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            raw_text = response.text.strip() if response.text else ""
            if raw_text.startswith("```"):
                raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                raw_text = re.sub(r"\s*```$", "", raw_text)

            data = json.loads(raw_text)
            pred = int(data.get("prediction", 0))
            reason = str(data.get("reason", "")).strip()
            return pred, reason

        except Exception as e:
            err_str = str(e)
            err_code = getattr(e, "code", None)

            # Check if this is a 429 RESOURCE_EXHAUSTED
            if err_code == 429 or "RESOURCE_EXHAUSTED" in err_str.upper() or "429" in err_str:
                # Distinguish between Daily Limit and Transient Per-Minute Rate Limit
                is_daily_limit = ("per day" in err_str.lower() or 
                                  "perday" in err_str.lower() or 
                                  "requests per day" in err_str.lower() or
                                  "15h" in err_str or "16h" in err_str or "14h" in err_str)
                
                if is_daily_limit:
                    raise DailyQuotaExhaustedException(f"Daily quota reached for {model_name}")

                # Otherwise it's a per-minute rate limit spike; wait and retry
                wait_sec = 20.0 + (attempt * 10.0)
                print(f"  [429 RPM Rate Limit] Exceeded per-minute requests. Cooling down for {wait_sec:.0f}s...", flush=True)
                time.sleep(wait_sec)
                continue

            # Check for 503 (Server high-demand / unavailable)
            if err_code == 503 or "503" in err_str or "UNAVAILABLE" in err_str.upper() or "DEMAND" in err_str.upper():
                if attempt < max_retries - 1:
                    backoff = 3.0 * (2 ** attempt)  # 3s, 6s, 12s, 24s...
                    print(f"  [503 Spike] Model {model_name} busy. Retrying in {backoff:.1f}s (Attempt {attempt + 1}/{max_retries})...", flush=True)
                    time.sleep(backoff)
                    continue
                else:
                    raise ServerUnavailableException(f"503 unavailable persisted after {max_retries} retries for {model_name}")

            # Check for network connection / timeout glitches (WinError 10060, TimeoutError, etc.)
            is_net_error = ("10060" in err_str or "timed out" in err_str.lower() or 
                            "timeout" in err_str.lower() or "connection" in err_str.lower())
            if is_net_error:
                if attempt < max_retries - 1:
                    backoff = 4.0 * (2 ** attempt)
                    print(f"  [Network Glitch] Transient connection timeout. Retrying in {backoff:.1f}s (Attempt {attempt + 1}/{max_retries})...", flush=True)
                    time.sleep(backoff)
                    continue

            # Any other exception
            raise e

    raise RuntimeError(f"Max retries exceeded for {model_name}")


def display_metrics(df):
    """Calculates and prints confusion matrix and classification report."""
    valid_df = df[df["predicted_label"] != -1]
    if len(valid_df) == 0:
        print("\nNo valid evaluation results found to calculate metrics.", flush=True)
        return

    print("\n" + "=" * 55, flush=True)
    print("             FINAL PERFORMANCE METRICS", flush=True)
    print("=" * 55, flush=True)
    print(f"Total evaluated samples: {len(valid_df)}", flush=True)
    y_true = valid_df["label"]
    y_pred = valid_df["predicted_label"]

    print("\nConfusion Matrix:", flush=True)
    print(confusion_matrix(y_true, y_pred), flush=True)

    print("\nClassification Report:", flush=True)
    print(classification_report(y_true, y_pred, target_names=["Safe (0)", "Phishing (1)"], zero_division=0), flush=True)

    # 95% Wilson Score Confidence Intervals
    import math
    n = len(valid_df)
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()
    acc = (tp + tn) / n
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0
    spec = tn / (tn + fp) if (tn + fp) > 0 else 0
    f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0

    def wilson(p_hat, count):
        if count == 0: return (0.0, 0.0)
        z = 1.95996
        d = 1.0 + z**2 / count
        c = (p_hat + z**2 / (2 * count)) / d
        m = (z / d) * math.sqrt(p_hat * (1 - p_hat) / count + z**2 / (4 * count**2))
        return (max(0.0, c - m) * 100, min(1.0, c + m) * 100)

    acc_ci = wilson(acc, n)
    prec_ci = wilson(prec, tp + fp if (tp + fp) > 0 else 1)
    rec_ci = wilson(rec, tp + fn if (tp + fn) > 0 else 1)
    spec_ci = wilson(spec, tn + fp if (tn + fp) > 0 else 1)
    f1_ci = wilson(f1, n)

    print("\n95% Wilson Confidence Intervals:", flush=True)
    print(f"  Accuracy:    {acc*100:6.2f}%  [95% CI: {acc_ci[0]:5.2f}% - {acc_ci[1]:5.2f}%]", flush=True)
    print(f"  Precision:   {prec*100:6.2f}%  [95% CI: {prec_ci[0]:5.2f}% - {prec_ci[1]:5.2f}%]", flush=True)
    print(f"  Recall:      {rec*100:6.2f}%  [95% CI: {rec_ci[0]:5.2f}% - {rec_ci[1]:5.2f}%]", flush=True)
    print(f"  Specificity: {spec*100:6.2f}%  [95% CI: {spec_ci[0]:5.2f}% - {spec_ci[1]:5.2f}%]", flush=True)
    print(f"  F1-Score:    {f1*100:6.2f}%  [95% CI: {f1_ci[0]:5.2f}% - {f1_ci[1]:5.2f}%]", flush=True)

    print("=" * 55, flush=True)


def main():
    print("=" * 65, flush=True)
    print("   ZERO-SHOT PHISHING EVALUATION AUTO-PILOT")
    print(f"   Primary Model:  {PRIMARY_MODEL}")
    print(f"   Failover Model: {FALLBACK_MODEL}")
    print("=" * 65, flush=True)

    # 1. Initialize API Client
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in .env file!", flush=True)
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # 2. Check Dataset
    if not os.path.exists(DATASET_PATH):
        print(f"Error: Dataset {DATASET_PATH} not found!", flush=True)
        sys.exit(1)

    dataset_df = pd.read_csv(DATASET_PATH)
    total_dataset_rows = len(dataset_df)
    print(f"Loaded dataset: {DATASET_PATH} ({total_dataset_rows} samples total)", flush=True)

    # 3. Check existing evaluated results to resume
    valid_count = 0
    if os.path.exists(OUTPUT_PATH) and os.path.getsize(OUTPUT_PATH) > 0:
        try:
            evaluated_df = pd.read_csv(OUTPUT_PATH)
            if "predicted_label" in evaluated_df.columns:
                valid_evaluated = evaluated_df[evaluated_df["predicted_label"] != -1]
                valid_count = len(valid_evaluated)
                if len(valid_evaluated) < len(evaluated_df):
                    valid_evaluated.to_csv(OUTPUT_PATH, index=False)
                    print(f"Cleaned {len(evaluated_df) - len(valid_evaluated)} error rows from {OUTPUT_PATH}.", flush=True)
        except Exception as e:
            print(f"Warning reading {OUTPUT_PATH}: {e}", flush=True)
            valid_count = 0

    print(f"Found {valid_count} valid completed rows in {OUTPUT_PATH}.", flush=True)

    if valid_count >= total_dataset_rows:
        print("All rows in the dataset have already been evaluated!", flush=True)
        evaluated_df = pd.read_csv(OUTPUT_PATH)
        display_metrics(evaluated_df)
        return

    # Start index is exactly the number of valid rows we already have
    start_index = valid_count
    print(f"Resuming evaluation exactly from row {start_index + 1} (index {start_index})...\n", flush=True)

    file_has_header = os.path.exists(OUTPUT_PATH) and os.path.getsize(OUTPUT_PATH) > 0
    rows_to_evaluate = dataset_df.iloc[start_index:]

    current_model = PRIMARY_MODEL
    halted_reason = None

    for index, row in rows_to_evaluate.iterrows():
        row_num = index + 1
        content = row["content"]
        actual_label = row["label"]

        pred = None
        reason = None

        # Try evaluating with current model (with failover support)
        while pred is None:
            try:
                pred, reason = evaluate_single_sample(client, current_model, content)
            except DailyQuotaExhaustedException as de:
                if current_model == PRIMARY_MODEL:
                    print(f"\n[FAILOVER NOTICE] {PRIMARY_MODEL} daily quota limit reached (20 req/day).", flush=True)
                    print(f"[FAILOVER NOTICE] Automatically switching to active model: {FALLBACK_MODEL} to finish evaluation today!\n", flush=True)
                    current_model = FALLBACK_MODEL
                    continue
                else:
                    halted_reason = f"Daily quota exhausted on {current_model}: {de}"
                    print(f"\n[QUOTA EXHAUSTED] {de}", flush=True)
                    print("[SAFEGUARD] Safely halting execution. NO -1 error rows written.", flush=True)
                    break
            except ServerUnavailableException as se:
                if current_model == PRIMARY_MODEL:
                    print(f"\n[FAILOVER NOTICE] {PRIMARY_MODEL} server unavailable. Switching to {FALLBACK_MODEL}...\n", flush=True)
                    current_model = FALLBACK_MODEL
                    continue
                else:
                    halted_reason = f"Server unavailable after retries on {current_model}: {se}"
                    print(f"\n[SERVER OVERLOAD] {se}", flush=True)
                    print("[SAFEGUARD] Safely halting execution. NO -1 error rows written.", flush=True)
                    break
            except Exception as e:
                halted_reason = f"Unexpected error on {current_model}: {e}"
                print(f"\n[ERROR] {e}", flush=True)
                print("[SAFEGUARD] Safely halting execution. NO -1 error rows written.", flush=True)
                break

        if pred is None:
            # An unrecoverable halt occurred
            break

        # Safely persist valid prediction immediately
        new_row = pd.DataFrame([{
            "id": row["id"],
            "content": content,
            "label": actual_label,
            "predicted_label": pred,
            "reason": reason
        }])

        new_row.to_csv(
            OUTPUT_PATH,
            mode="a",
            header=not file_has_header,
            index=False
        )
        file_has_header = True

        reason_preview = (reason[:50] + "...") if len(reason) > 50 else reason
        print(f"Row {row_num}/{total_dataset_rows} [{current_model}] | Actual: {actual_label} | Pred: {pred} | {reason_preview}", flush=True)

        # 4.1s delay to maintain <= 14 RPM (within Free Tier 15 RPM limit)
        time.sleep(4.1)

    # 4. Summary & Metrics
    print("\n" + "-" * 55, flush=True)
    if halted_reason:
        print(f"Execution halted gracefully: {halted_reason}", flush=True)
    else:
        print("ALL 200 ROWS PROCESSED SUCCESSFULLY!", flush=True)

    if os.path.exists(OUTPUT_PATH):
        final_df = pd.read_csv(OUTPUT_PATH)
        print(f"Total valid rows saved in {OUTPUT_PATH}: {len(final_df)}/{total_dataset_rows}", flush=True)
        display_metrics(final_df)


if __name__ == "__main__":
    main()
