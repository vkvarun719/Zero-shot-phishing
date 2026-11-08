# Zero-Shot Phishing Detection via Google Gemini Large Language Models

This repository contains the dataset, scripts, evaluation pipeline, and experimental results for zero-shot detection of phishing URLs using Google Gemini Large Language Models.

---

## 📊 Summary of Evaluation Results

The evaluation was performed across 200 ground-truth URLs (100 legitimate, 100 phishing) in a zero-shot setting.

| Metric | Score | Note |
|---|---|---|
| **Total Evaluated** | **200 / 200** | 100% completion, zero error rows |
| **Accuracy** | **89.50%** | 179 / 200 correctly classified |
| **Precision (Phishing)** | **91.58%** | 87 True Positives / (87 TP + 8 FP) |
| **Recall (Phishing)** | **87.00%** | 87 True Positives / (87 TP + 13 FN) |
| **F1-Score** | **89.23%** | Harmonic mean of Precision and Recall |
| **Specificity (Legitimate)**| **92.00%** | 92 True Negatives / (92 TN + 8 FP) |

### Confusion Matrix

| | Predicted Legitimate (0) | Predicted Phishing (1) | Total |
|---|---|---|---|
| **Actual Legitimate (0)** | **92** (True Negative) | **8** (False Positive) | 100 |
| **Actual Phishing (1)** | **13** (False Negative) | **87** (True Positive) | 100 |
| **Total** | 105 | 95 | 200 |

---

## 🔍 Key Findings & Critical Vulnerabilities

1. **The "Trusted Infrastructure" Blind Spot (False Negatives)**
   - **8 out of the 13 False Negatives** utilized legitimate Google ecosystems (`docs.google.com`, `drive.google.com`, `forms.gle`, `script.google.com`).
   - The LLM's zero-shot reasoning gave disproportionate trust to the authoritative parent domain and failed to flag weaponized credential harvesters hosted on free cloud tiers.
2. **Surface Feature Over-Sensitivity (False Positives)**
   - **8 False Positives** occurred on legitimate websites that exhibited surface patterns typical of phishing (e.g., `.tv` ccTLD, deeply nested paths, words like `invoice` or `login` in URLs).

---

## 📁 Repository Structure

```
.
├── auto_eval.py                          # Resumable, fault-tolerant evaluation auto-pilot script
├── main_eval.py                          # Original evaluation baseline
├── clean_results.py                      # Data cleaning utility
├── phishing_dataset.csv                  # Benchmark dataset (200 URLs: id, content, label)
├── evaluated_results.csv                 # Final full evaluation results (200 evaluated URLs with reasoning)
├── clean_evaluated_results.csv           # Cleaned preliminary output
├── full_report.html                      # Interactive comprehensive HTML report
├── report.html                           # Summary HTML report
├── NCDTE_Phishing_Project_Complete_Report.pdf  # Publication-ready comprehensive PDF report
├── zero_shot_phishing_evaluation_report.pdf    # Initial metrics PDF report
├── .gitignore                            # Excludes venv, .env, cache files
└── README.md                             # Project documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/)

### 2. Installation
Clone the repository and set up a virtual environment:
```bash
git clone https://github.com/vkvarun719/Zero-shot-phishing.git
cd Zero-shot-phishing
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install google-genai pandas python-dotenv
```

### 3. Configure API Key
Create a `.env` file in the project root:
```env
GEMINI_API_KEY="your-gemini-api-key-here"
```

### 4. Run the Evaluation Auto-Pilot
The script automatically detects previous progress and resumes from the exact next uncompleted row:
```bash
python auto_eval.py
```

#### Key Engineering Features of `auto_eval.py`:
- **State Resumption**: Inspects `evaluated_results.csv` on launch and continues seamlessly.
- **Atomic Append**: Writes each evaluated row immediately to disk to protect against mid-run crashes.
- **Exponential Backoff**: Handles HTTP 503 (`UNAVAILABLE`) and transient network disconnects (`WinError 10060`).
- **Quota Safeguards**: Gracefully halts upon `RESOURCE_EXHAUSTED` (HTTP 429) without corrupting output with `-1` error rows.
- **Dynamic Failover**: Automatically switches to lighter models if primary tier quota is depleted.

---

## 📝 Research Paper Roadmap & Next Steps

For collaborators working on drafting the academic research paper:
1. **Single-Model Benchmark**: Re-evaluate the full 200 rows under a unified single model tier (e.g., pure `gemini-2.5-flash` / `gemini-3.8-flash` on Tier-1 pay-as-you-go) to maintain strict model isolation.
2. **Prompt Engineering & Few-Shot Learning**: Introduce few-shot exemplars focusing specifically on cloud-hosted abuse (`docs.google.com`, `sharepoint.com`, `forms.office.com`).
3. **Chain-of-Thought (CoT) & Rule Verification**: Force explicit domain separation: evaluate `Registered Domain` vs. `Subdomain/Path Content` separately before returning classification.
4. **Baseline Comparisons**: Benchmark against traditional lexical ML classifiers (Random Forest, XGBoost, TF-IDF URL features).

---

## 📄 License
This project is for educational and academic research purposes.
