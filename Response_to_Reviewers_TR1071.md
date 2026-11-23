# Response to Reviewers' Comments (Rebuttal Document)

**Paper ID:** TR1071  
**Original Title:** Zero-Shot Phishing URL Detection via Open Source LLM and Hybrid SOC Triage  
**Revised Title:** Zero-Shot Phishing URL Detection via Open-Source and Frontier Large Language Models with Hybrid SOC Triage  
**Conference:** National Conference on Digital Technology and Engineering (NCDTE-26)  
**Host Institution:** RV Institute of Technology and Management (RVITM), Bengaluru  
**Track:** Cyber Security and Digital Forensics  
**Decision:** Accepted with Minor Revision  
**Authors:**
- Varun V K (`varun.vk@rvitm.edu.in`)
- Chitti P (`chitti.p@rvitm.edu.in`)
- Faculty Research Guide (`faculty.guide@rvitm.edu.in`)

---

### Dear Reviewers and Program Committee Members of NCDTE-26,

We express our sincere gratitude to the reviewers and the Technical Program Committee for their thorough, constructive, and insightful evaluation of our manuscript **TR1071**. 

We have addressed each reviewer comment point-by-point, significantly expanding the experimental evaluation, adding standard baseline models, integrating open-source LLM benchmarking, computing 95% Wilson score confidence intervals, softening prior priority claims, updating author metadata, and preparing the camera-ready manuscript per the conference guidelines.

Below is our detailed, point-by-point response indicating the specific changes incorporated into the revised manuscript.

---

### Detailed Point-by-Point Responses

#### Reviewer Comment 1:
> *"The test set has only 200 URLs, which is small for the claims made. Please evaluate on a larger public set (e.g., several thousand URLs from PhishTank/OpenPhish and Tranco) and report confidence intervals."*

**Authors' Response & Actions Taken:**
1. **Dataset Scale Expansion (6x Increase):**
   - We expanded the test benchmark from the initial 200 URLs to a comprehensive public benchmark of **1,200 balanced ground-truth URLs** (600 phishing and 600 legitimate).
   - **Phishing Sources (600 URLs):** Curated from verified live and active feeds from **PhishTank, OpenPhish, and URLhaus**, specifically reflecting contemporary threat vectors:
     - Cloud PaaS abuse: 160 URLs (`.pages.dev`, `.vercel.app`, `.netlify.app`, `.webflow.io`, `.supabase.co`, `.firebaseapp.com`, `.onrender.com`).
     - Abused authoritative SaaS: 100 URLs (`docs.google.com/forms`, `forms.gle`, `drive.google.com`, `sharepoint.com`, `canva.com/design`).
     - Brand typosquatting and combosquatting: 180 URLs (PayPal, Netflix, Chase, Wells Fargo, DHL, USPS, Apple ID, Microsoft365, MetaMask, Binance).
     - Compromised servers hosting phishing kits: 100 URLs (cPanel webmail, Roundcube, Zimbra, Exchange OWA).
     - Obfuscated IP and shortened URLs: 60 URLs (`http://185.220...`, `bit.ly`, `tinyurl.com`).
   - **Legitimate Sources (600 URLs):** Curated from the **Tranco Top 1M, Alexa Top 1M**, government/academic sites (`.gov`, `.edu`, `.ac.in`), and verified SaaS endpoints. Critically, 150 of these URLs are "hard negative" legitimate links containing security-related tokens (`login`, `verify`, `auth`, `token`, `session`) to rigorously evaluate false alarm rates.
2. **Statistical Confidence Intervals:**
   - In accordance with the reviewer's request, we computed and reported **95% Wilson Score Confidence Intervals** for all primary metrics (Accuracy, Precision, Recall, Specificity, and F1-Score) across all models and baselines.
   - For example, on the expanded benchmark, Google Gemini 3.8 Flash achieved an Accuracy of **95.75% [95% CI: 94.46% – 96.75%]**, Llama-3-8B achieved **94.67% [95% CI: 93.25% – 95.80%]**, and our Hybrid SOC Triage Pipeline achieved **96.58% [95% CI: 95.40% – 97.47%]**.
   - These confidence intervals are presented in Table II and Section IV of the revised manuscript.

---

#### Reviewer Comment 2:
> *"Please compare with standard baselines on the same URLs (e.g., a URL-feature classifier, URLNet [8], or Google Safe Browsing), and avoid calling this the "first rigorous" zero-shot study, since earlier LLM phishing studies exist."*

**Authors' Response & Actions Taken:**
1. **Side-by-Side Standard Baseline Evaluations on Identical URLs:**
   We implemented and evaluated four standard baseline classifiers on the exact same 1,200 benchmark URLs:
   - **Baseline 1: Rule-Based Threat Feed (Google Safe Browsing Style):** Achieved 54.25% Accuracy [51.42% – 57.05% CI], 82.28% Precision, and 10.83% Recall. While having low false alarms (2.33% FPR), it missed 89.17% of modern cloud-hosted phishing kits.
   - **Baseline 2: Linear Lexical Classifier (Logistic Regression):** Evaluated on 18 extracted lexical/structural URL features with 5-fold cross-validation; achieved 94.33% Accuracy [92.88% – 95.51% CI] and 94.26% F1-score.
   - **Baseline 3: Lexical Feature Classifier (Random Forest):** 100-tree ensemble trained on the 18 lexical/structural features (URL length, domain length, Shannon entropy, dot/hyphen counts, digit ratio, IP flag, suspicious TLDs, sensitive keywords); achieved 95.50% Accuracy [94.17% – 96.53% CI], 96.11% Precision, and 94.83% Recall.
   - **Baseline 4: URLNet [8] (Character-Level CNN Deep Learning Baseline):** Character sequence modeling capturing n-gram embeddings without hand-crafted features; achieved 92.08% Accuracy [90.42% – 93.48% CI], 99.61% Precision, and 84.50% Recall.
   - **Proposed Hybrid SOC Triage:** Outperformed all individual models, achieving **96.58% Accuracy [95.40% – 97.47% CI]** and **96.54% F1-score**, while reducing average latency to ~68ms and decreasing LLM API invocation costs by 81.7%.
   The complete comparative matrix has been incorporated into Table II of the revised paper.
2. **Removal of Priority Claims & Literature Contextualization:**
   - We removed all statements characterizing our study as the "first rigorous" zero-shot investigation.
   - We thoroughly expanded Section II (Related Work) to review and cite earlier LLM phishing studies:
     - Al-Dujaili et al. (2023) on prompt-based LLM phishing email classification;
     - Koide et al. (2023) and Heiding et al. (2023) on LLM-driven social engineering and phishing defenses;
     - Roy et al. (2023) on ChatGPT phishing detection benchmarks;
     - Le et al. [8] (URLNet, 2018) on character-level convolutional neural networks for URL detection.
   - We repositioned our paper's core contributions around (i) benchmarking zero-shot LLMs against cloud-native PaaS abuse and authoritative SaaS lures on an expanded 1,200-sample dataset, and (ii) introducing the operational Hybrid SOC Triage framework combining lexical pre-filtering with zero-shot LLM reasoning.

---

#### Reviewer Comment 3:
> *"The title says 'Open Source LLM', but the experiments use Gemini, a closed model. Please correct the title or add an open-source model, and add email IDs for all authors."*

**Authors' Response & Actions Taken:**
1. **Added Open-Source LLM Benchmark (Llama-3-8B-Instruct):**
   - Rather than merely renaming the paper, we added a complete empirical evaluation of the leading open-source model **Meta Llama-3-8B-Instruct** across the entire 1,200-sample benchmark using identical zero-shot cybersecurity prompts.
   - **Key Finding:** Llama-3-8B achieved an outstanding **100.00% Precision (0 False Positives)** and **94.67% Accuracy [93.25% – 95.80% CI]** with an 89.33% Recall. This demonstrates that open-source models can run completely on-premise within air-gapped corporate SOCs, guaranteeing data privacy while delivering enterprise-grade detection fidelity.
2. **Revised Paper Title:**
   - To accurately reflect the dual evaluation of both open-source and frontier models, the title has been updated to:  
     **"Zero-Shot Phishing URL Detection via Open-Source and Frontier Large Language Models with Hybrid SOC Triage"**
3. **Author Affiliations and Email IDs:**
   - Full institutional affiliations and email addresses have been explicitly added for all authors in the paper header:
     - Varun V K (`varun.vk@rvitm.edu.in`)
     - Chitti P (`chitti.p@rvitm.edu.in`)
     - Faculty Research Guide (`faculty.guide@rvitm.edu.in`)
     - Department of Computer Science & Engineering, RV Institute of Technology and Management (RVITM), Bengaluru, Karnataka, India.

---

### Summary of Revision Verification

| Item | NCDTE-26 Requirement | Revision Status | Details in Paper |
|---|---|---|---|
| 1 | Benchmark Dataset Scale | **Completed (1,200 URLs)** | Expanded from 200 to 1,200 URLs (600 Phishing, 600 Safe) |
| 2 | Confidence Intervals | **Completed (95% Wilson CIs)** | Reported for Accuracy, Precision, Recall, Specificity, F1 |
| 3 | Baseline Comparisons | **Completed (4 Baselines)** | Random Forest, Logistic Regression, URLNet [8], Threat Feed |
| 4 | Literature & Tone | **Completed** | "First rigorous" claim removed; prior LLM works cited |
| 5 | Open-Source LLM | **Completed (Llama-3-8B)** | Benchmarked on 1,200 URLs; 94.67% Acc, 100% Precision |
| 6 | Title Correction | **Completed** | Updated to "Open-Source and Frontier Large Language Models" |
| 7 | Author Email IDs | **Completed** | All author institutional emails added to paper header |
| 8 | File Naming Convention | **Completed** | Output saved strictly as `TR1071.pdf` |
| 9 | Similarity / AI Check | **Verified (< 20%)** | Full manuscript passes similarity and originality criteria |

We believe these substantial revisions thoroughly address all concerns raised by the reviewers and make the paper significantly stronger, more statistically sound, and ready for publication and presentation at NCDTE-26.

Respectfully submitted,  
**Authors of Paper TR1071**  
RV Institute of Technology and Management, Bengaluru  
November 23, 2026
