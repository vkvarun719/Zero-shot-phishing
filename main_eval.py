import os
import time
import json
import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types
from sklearn.metrics import classification_report, confusion_matrix

# 1. Load environment variables & initialize modern GenAI client
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file!")

client = genai.Client(api_key=api_key)
MODEL_NAME = "gemini-3.5-flash"

def evaluate_phishing_sample(text_content, max_retries=4):
    """Sends sample content to Gemini with automatic retry-backoff for 503 high demand spikes."""
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
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            result = json.loads(response.text)
            return result.get("prediction", 0), result.get("reason", "")
        except Exception as e:
            print(f"API attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                sleep_time = (attempt + 1) * 3
                print(f"Server busy. Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                return -1, str(e)
        
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            result = json.loads(response.text)
            return result.get("prediction", 0), result.get("reason", "")
        except Exception as e:
            print(f"Error during API call: {e}")
            return -1, str(e)
    
def main():
    # 2. Load dataset (limited to 5 rows for fast testing)
    dataset_path = "phishing_dataset.csv"
    if not os.path.exists(dataset_path):
        print(f"Error: {dataset_path} not found. Please place your CSV file in the project folder.")
        return

    print(f"Loading dataset from {dataset_path}...")
    df = pd.read_csv(dataset_path)    
    predictions = []
    reasons = []

    print(f"Starting zero-shot evaluation using {MODEL_NAME}...")
    for index, row in df.iterrows():
        content = row['content']
        actual_label = row['label']
        
        pred, reason = evaluate_phishing_sample(content)
        predictions.append(pred)
        reasons.append(reason)
        
        print(f"Row {index+1}/{len(df)} | Actual: {actual_label} | Predicted: {pred}")
        time.sleep(0.3)

    # 3. Save evaluated results
    df['predicted_label'] = predictions
    df['reason'] = reasons
    output_path = "evaluated_results.csv"
    df.to_csv(output_path, index=False)
    print(f"\nEvaluation complete! Results saved to {output_path}.")

    # 4. Calculate Metrics (Precision, Recall, F1-Score, Confusion Matrix)
    valid_df = df[df['predicted_label'] != -1]
    y_true = valid_df['label']
    y_pred = valid_df['predicted_label']

    print("\n--- PERFORMANCE METRICS ---")
    print(confusion_matrix(y_true, y_pred))
    print("\nClassification Report:")
    print(classification_report(y_true, y_pred, target_names=["Safe (0)", "Phishing (1)"]))

if __name__ == "__main__":
    main()