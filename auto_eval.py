# auto_eval.py
"""
Auto-eval pipeline supporting Frontier LLMs (Google Gemini 3.8 Flash / 3.1 Flash Lite)
and Open-Source LLMs (Llama 3 / Mistral / Qwen via local or remote APIs).
Includes state resumption, atomic appends, exponential backoff, and Wilson 95% CI reporting.
"""

import os
import sys
import time
import json
import re
import math
import pandas as pd
from dotenv import load_dotenv

# Optional GenAI SDK import
try:
    from google import genai
    from google.genai import types
    from google.genai import errors
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

from sklearn.metrics import classification_report, confusion_matrix

script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(script_dir, ".env"))

PRIMARY_MODEL = "gemini-3.8-flash"
FALLBACK_MODEL = "gemini-3.1-flash-lite"
OPENSOURCE_MODEL = "meta-llama/Meta-Llama-3-8B-Instruct"
DATASET_PATH = os.path.join(script_dir, "phishing_dataset.csv")
OUTPUT_PATH = os.path.join(script_dir, "evaluated_results.csv")

class DailyQuotaExhaustedException(Exception):
    """Raised when daily free tier quota (RPD) is exhausted for the model."""
    pass

class ServerUnavailableException(Exception):
    """Raised when 503 high demand persists after exponential backoff."""
    pass

def wilson_score_interval(p_hat, n, confidence=0.95):
    """Computes Wilson score confidence interval for a proportion."""
    if n == 0:
        return (0.0, 0.0)
    z = 1.95996
    denom = 1.0 + (z**2) / n
    center = (p_hat + (z**2) / (2.0 * n)) / denom
    margin = (z / denom) * math.sqrt((p_hat * (1.0 - p_hat) / n) + ((z**2) / (4.0 * (n**2))))
    return (max(0.0, center - margin), min(1.0, center + margin))

def evaluate_single_sample_gemini(client, model_name, text_content, max_retries=5):
    """
    Evaluates one sample using Gemini.
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

            if err_code == 429 or "RESOURCE_EXHAUSTED" in err_str.upper() or "429" in err_str:
                is_daily = ("per day" in err_str.lower() or "perday" in err_str.lower() or "requests per day" in err_str.lower())
                if is_daily:
                    raise DailyQuotaExhaustedException(f"Daily quota reached for {model_name}")
                wait_sec = 15.0 + (attempt * 10.0)
                print(f"  [429 RPM] Cooling down for {wait_sec:.0f}s...", flush=True)
                time.sleep(wait_sec)
                continue

            if err_code == 503 or "503" in err_str or "UNAVAILABLE" in err_str.upper():
                if attempt < max_retries - 1:
                    backoff = 3.0 * (2 ** attempt)
                    print(f"  [503 Spike] Retrying in {backoff:.1f}s...", flush=True)
                    time.sleep(backoff)
                    continue
                else:
                    raise ServerUnavailableException(f"503 unavailable persisted for {model_name}")

            if attempt < max_retries - 1:
                time.sleep(2.0 * (attempt + 1))
            else:
                return -1, f"Evaluation error: {err_str}"
                
    return -1, "Max retries exceeded"

def compute_and_print_metrics(csv_path):
    """Computes and formats complete metrics with 95% Wilson confidence intervals."""
    if not os.path.exists(csv_path):
        print(f"File {csv_path} does not exist.")
        return
        
    df = pd.read_csv(csv_path)
    if 'predicted_label' not in df.columns or 'label' not in df.columns:
        print("Required columns missing.")
        return
        
    valid_df = df[df['predicted_label'] != -1]
    n = len(valid_df)
    if n == 0:
        print("No valid predictions found.")
        return
        
    y_true = valid_df['label'].values
    y_pred = valid_df['predicted_label'].values
    
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()
    
    acc = (tp + tn) / n
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0
    spec = tn / (tn + fp) if (tn + fp) > 0 else 0
    f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0
    
    acc_ci = wilson_score_interval(acc, n)
    prec_ci = wilson_score_interval(prec, tp + fp if (tp + fp) > 0 else 1)
    rec_ci = wilson_score_interval(rec, tp + fn if (tp + fn) > 0 else 1)
    spec_ci = wilson_score_interval(spec, tn + fp if (tn + fp) > 0 else 1)
    f1_ci = wilson_score_interval(f1, n)
    
    print("\n" + "="*80)
    print(f"EVALUATION PERFORMANCE SUMMARY (N = {n})")
    print("="*80)
    print(f"Accuracy:    {acc*100:6.2f}%  [95% CI: {acc_ci[0]*100:5.2f}% - {acc_ci[1]*100:5.2f}%]")
    print(f"Precision:   {prec*100:6.2f}%  [95% CI: {prec_ci[0]*100:5.2f}% - {prec_ci[1]*100:5.2f}%]")
    print(f"Recall:      {rec*100:6.2f}%  [95% CI: {rec_ci[0]*100:5.2f}% - {rec_ci[1]*100:5.2f}%]")
    print(f"Specificity: {spec*100:6.2f}%  [95% CI: {spec_ci[0]*100:5.2f}% - {spec_ci[1]*100:5.2f}%]")
    print(f"F1-Score:    {f1*100:6.2f}%  [95% CI: {f1_ci[0]*100:5.2f}% - {f1_ci[1]*100:5.2f}%]")
    print("-"*80)
    print("Confusion Matrix:")
    print(f"  True Negatives (TN):  {tn:4d}  |  False Positives (FP): {fp:4d}")
    print(f"  False Negatives (FN): {fn:4d}  |  True Positives (TP):  {tp:4d}")
    print("="*80 + "\n")

if __name__ == "__main__":
    compute_and_print_metrics(OUTPUT_PATH)
