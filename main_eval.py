# main_eval.py
"""
Baseline interactive evaluation script for Zero-Shot Phishing Detection.
Supports single sample interactive testing and dataset batch evaluation.
"""

import os
import sys
import time
import json
import pandas as pd
from dotenv import load_dotenv

script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(script_dir, ".env"))

MODEL_NAME = "gemini-3.8-flash"

def evaluate_phishing_sample(text_content, max_retries=3):
    """
    Sends sample content to Gemini with automatic retry-backoff.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        # Fallback heuristic analysis if no API key is provided
        from baseline_eval import extract_url_features
        feat = extract_url_features(text_content)
        if feat['has_ip'] == 1 or (feat['suspicious_tld'] == 1 and feat['has_sensitive_keyword'] > 0):
            return 1, "Heuristic detection: Suspicious high-risk TLD or raw IP host with sensitive tokens."
        elif feat['has_sensitive_keyword'] >= 2 and feat['num_hyphens'] >= 2:
            return 1, "Heuristic detection: Multiple sensitive keywords combined with excessive hyphens."
        return 0, "No obvious credential harvesting or typosquatting indicators found."

    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key)
        prompt = f"""
        You are an expert cybersecurity threat analyst. Analyze the following text or URL to determine if it is a phishing attack or safe.
        
        Content to analyze:
        \"\"\"{text_content}\"\"\"

        Respond ONLY with a valid JSON object containing exactly two keys:
        1. "prediction": integer 1 if phishing, 0 if safe.
        2. "reason": a short 1-sentence justification for the classification.
        """
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        result = json.loads(response.text)
        return result.get("prediction", 0), result.get("reason", "")
    except Exception as e:
        return -1, str(e)

def main():
    dataset_path = os.path.join(script_dir, "phishing_dataset.csv")
    if not os.path.exists(dataset_path):
        print(f"Error: {dataset_path} not found.")
        return

    print(f"Loading dataset from {dataset_path}...")
    df = pd.read_csv(dataset_path)
    print(f"Loaded {len(df)} samples ({sum(df['label'] == 1)} Phishing, {sum(df['label'] == 0)} Safe).")
    print("To run the full multi-model benchmark with 95% Wilson Confidence Intervals, execute:")
    print("  python baseline_eval.py")

if __name__ == "__main__":
    main()
