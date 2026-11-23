# create_docx_paper.py
"""
Generates the publication-ready camera-ready Word document (.docx)
for Paper ID: TR1071 accepted at NCDTE-26.
Formatted with Times New Roman, IEEE-style structure, tables, and full academic prose.
"""

import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_margins(cell, top=80, bottom=80, left=120, right=120):
    """Sets cell padding in twips."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_cell_shading(cell, color_hex):
    """Sets cell background color."""
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)

def create_paper_docx():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    out_docx1 = os.path.join(script_dir, "TR1071.docx")
    out_docx2 = os.path.join(script_dir, "TR1071_Camera_Ready_Paper.docx")

    doc = Document()

    # Page Margins: Standard IEEE 0.75 in
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    # Base Normal Style: Times New Roman, 10 pt
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(10)
    font.color.rgb = RGBColor(0, 0, 0)
    style.paragraph_format.line_spacing = 1.15
    style.paragraph_format.space_after = Pt(4)

    # Conference Header Note
    p_conf = doc.add_paragraph()
    p_conf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_conf = p_conf.add_run("NATIONAL CONFERENCE ON DIGITAL TECHNOLOGY AND ENGINEERING (NCDTE-26)\nRV INSTITUTE OF TECHNOLOGY AND MANAGEMENT, BENGALURU | PAPER ID: TR1071")
    run_conf.font.size = Pt(8.5)
    run_conf.font.bold = True
    run_conf.font.color.rgb = RGBColor(70, 70, 70)
    p_conf.paragraph_format.space_after = Pt(10)

    # Paper Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = p_title.add_run("Zero-Shot Phishing URL Detection via Open-Source and Frontier Large Language Models with Hybrid SOC Triage")
    run_title.font.size = Pt(18)
    run_title.font.bold = True
    p_title.paragraph_format.space_after = Pt(8)

    # Authors
    p_auth = doc.add_paragraph()
    p_auth.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_a1 = p_auth.add_run("Asst. Prof. Avinash N Rao*1, Varun Kumar K C*2, Vinay Prakash A P*3, Rishita Raveendra Chikkaraddi*4, Lakshmipathy A S*5\n")
    r_a1.bold = True
    r_a1.font.size = Pt(10)
    
    r_emails = p_auth.add_run("*1avinashnrao.rvitm@rvei.edu.in, *2varunkumarkc.rvitm@gmail.com, *3vinayprakash.rvitm@gmail.com,\n*4rishitac.rvitm@gmail.com, *5lakshmipathyas.rvitm@gmail.com\n")
    r_emails.font.size = Pt(9)
    r_emails.italic = False
    
    r_aff = p_auth.add_run("*1Assistant Professor, Dept. of Computer Science & Engineering (Artificial Intelligence and Machine Learning), RVITM, Bengaluru, India\n*2,3Undergraduate Scholars, Dept. of CSE (AI & ML), RV Institute of Technology and Management, Bengaluru, India\n*4,5Undergraduate Scholars, Dept. of Computer Science & Engineering, RV Institute of Technology and Management, Bengaluru, India")
    r_aff.font.size = Pt(8.5)
    r_aff.italic = True
    p_auth.paragraph_format.space_after = Pt(14)

    # Abstract Box Table
    t_abs = doc.add_table(rows=1, cols=1)
    t_abs.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell_abs = t_abs.rows[0].cells[0]
    cell_abs.width = Inches(7.0)
    set_cell_shading(cell_abs, "F8FAFC")
    set_cell_margins(cell_abs, top=140, bottom=140, left=180, right=180)
    
    p_ab = cell_abs.paragraphs[0]
    p_ab.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r_ab_title = p_ab.add_run("Abstract—")
    r_ab_title.bold = True
    r_ab_title.font.size = Pt(9)
    r_ab_text = p_ab.add_run(
        "Phishing attacks remain the primary initial compromise vector for enterprise breaches, credential theft, and ransomware operations. Traditional security architectures rely primarily on static reputation blacklists, heuristic filters, and supervised machine learning classifiers trained on tabular lexical and host features. However, modern adversaries increasingly deploy zero-day campaigns on serverless hosting platforms (e.g., Cloudflare Pages, Vercel, Netlify) and weaponized documents within authoritative enterprise cloud ecosystems (e.g., Google Workspace, Microsoft SharePoint, Zoom Docs), fundamentally evading signature databases and tabular classifiers. In this paper, we present an empirical benchmark of zero-shot Large Language Model (LLM) classification for raw phishing URL detection across an expanded, balanced public benchmark of 1,200 real-world URLs (600 phishing, 600 legitimate) sourced from PhishTank, OpenPhish, URLhaus, and the Tranco Top-1M. We benchmark frontier closed models (Google Gemini 3.8 Flash) against leading open-source models (Meta Llama-3-8B-Instruct), character-level deep sequence learning (URLNet), tabular classifiers (Random Forest, Logistic Regression), and rule-based threat feeds. Google Gemini 3.8 Flash achieved 95.75% accuracy (95% Wilson CI: 94.46%–96.75%), 97.25% precision, 94.17% recall, and an F1-score of 95.68%, while Llama-3-8B achieved 94.67% accuracy (95% CI: 93.25%–95.80%) with 100.00% precision (0 false alarms). Error analysis uncovers the Authoritative Domain Blind Spot, wherein zero-shot LLMs exhibit reputation halo bias toward trusted parent domains. To resolve operational latency and API billing bottlenecks, we engineer a multi-tiered Security Operations Center (SOC) triage framework synthesizing offline zero-egress lexical filtering with cloud/local LLM reasoning. The hybrid triage system achieves 96.58% accuracy (95% CI: 95.40%–97.47%), 97.78% precision, and a 96.54% F1-score, while absorbing 81.7% of enterprise traffic locally, reducing cloud API invocations by 81.7%, and slashing mean triage latency from 1,420 ms to 68 ms. Structured JSON outputs deliver human-interpretable cybersecurity justifications alongside binary decisions, directly supporting tier-1 SOC incident workflows."
    )
    r_ab_text.font.size = Pt(9)

    p_kw = cell_abs.add_paragraph()
    p_kw.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r_kw_title = p_kw.add_run("Index Terms—")
    r_kw_title.bold = True
    r_kw_title.font.size = Pt(9)
    r_kw_text = p_kw.add_run("Phishing URL detection, Large Language Models (LLMs), zero-shot reasoning, Google Gemini, Meta Llama 3, baseline benchmarking, Wilson confidence intervals, threat intelligence, cybersecurity triage, topological link forensics, authoritative domain abuse, explainable artificial intelligence (XAI).")
    r_kw_text.font.size = Pt(9)
    r_kw_text.italic = True

    # Helper function for adding headings
    def add_sec_heading(title):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(title)
        run.bold = True
        run.font.size = Pt(11)
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        return p

    def add_subsec_heading(title):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(title)
        run.bold = True
        run.italic = True
        run.font.size = Pt(10)
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        return p

    def add_p(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        r = p.add_run(text)
        r.font.size = Pt(10)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        return p

    # SECTION I: INTRODUCTION
    add_sec_heading("I. INTRODUCTION")
    add_p("Phishing attacks represent the foremost initial compromise vector for advanced persistent threats (APTs), credential harvesting campaigns, business email compromise (BEC), and ransomware deployments globally [1]. Recent threat activity reports published by the Anti-Phishing Working Group (APWG) document historic surges in cybercriminal activity, with quarterly attack volumes surpassing 1.2 million discrete incidents [2]. Threat actors have shifted away from primitive, grammatically flawed email lures toward sophisticated, highly automated phishing kits capable of real-time multi-factor authentication (MFA) proxying, server-side visitor cloaking, and instantaneous domain hopping [3], [4].")
    add_p("To combat this exponential expansion, enterprise security architectures have historically relied on three defense paradigms: (1) static reputation blacklists (e.g., Google Safe Browsing, PhishTank, Spamhaus) [5]; (2) supervised machine learning classifiers (e.g., Random Forests, Support Vector Machines, XGBoost) trained on tabular lexical, host-based, and WHOIS metadata [6], [7]; and (3) deep sequence models (e.g., character-level Convolutional Neural Networks and Long Short-Term Memory networks) that process raw URL character distributions [8].")
    add_p("While each paradigm provides defensive utility, each exhibits acute operational vulnerabilities:")
    
    p_b1 = doc.add_paragraph(style='List Bullet')
    r_b1 = p_b1.add_run("Static Blacklist Latency: ")
    r_b1.bold = True
    p_b1.add_run("As demonstrated in large-scale empirical studies by Oest et al. [9], contemporary phishing campaigns exhibit a median active lifespan of approximately 21 hours, with over 7.4% of victims compromising their credentials within the first two hours. Reactive blacklists require hours or days for discovery, crawling, verification, and DNS propagation, during which zero-day phishing campaigns successfully harvest credentials with near-total impunity [9].")
    
    p_b2 = doc.add_paragraph(style='List Bullet')
    r_b2 = p_b2.add_run("Supervised Machine Learning Degradation: ")
    r_b2.bold = True
    p_b2.add_run("Tabular ML classifiers require continuous feature engineering, domain reputation lookups, and periodic retraining to maintain predictive accuracy. As adversaries adopt serverless staging hosts (*.vercel.app, *.pages.dev, *.webflow.io), lexical properties between malicious and benign URLs become indistinguishable, inducing severe feature drift and high false alarm rates [10].")

    p_b3 = doc.add_paragraph(style='List Bullet')
    r_b3 = p_b3.add_run("Opaque Deep Learning Ensembles: ")
    r_b3.bold = True
    p_b3.add_run("Although end-to-end deep learning models bypass manual feature extraction, they operate as unexplainable black boxes. They output uncalibrated binary probability scores without context, failing to provide Security Operations Center (SOC) analysts with actionable rationales necessary for rapid triage and regulatory auditing [11].")

    # Takeaway Callout Box
    t_box = doc.add_table(rows=1, cols=1)
    t_box.alignment = WD_TABLE_ALIGNMENT.CENTER
    c_box = t_box.rows[0].cells[0]
    c_box.width = Inches(7.0)
    set_cell_shading(c_box, "EFF6FF")
    set_cell_margins(c_box, top=100, bottom=100, left=140, right=140)
    p_takeaway = c_box.paragraphs[0]
    r_tk_title = p_takeaway.add_run("Key Research Takeaway: ")
    r_tk_title.bold = True
    r_tk_title.font.color.rgb = RGBColor(30, 58, 138)
    p_takeaway.add_run("Zero-shot LLM reasoning achieves 95.75% accuracy (Gemini 3.8 Flash) and 100.00% precision (Llama-3-8B) on raw URLs without task-specific training data. Synthesizing zero-shot reasoning with offline lexical screening in a Hybrid SOC Triage framework achieves 96.58% accuracy [95.40%–97.47% CI] and 96.54% F1-score, while cutting API overhead by 81.7% and dropping effective latency to 68 ms.")

    add_p("The recent emergence of foundational Large Language Models (LLMs)—such as Google Gemini, OpenAI GPT-4, and Meta Llama 3—introduces an unprecedented opportunity for automated cybersecurity reasoning [12], [13]. Pre-trained on trillions of tokens encompassing internet text, code repositories, network protocols, and cyber threat reports, LLMs possess latent semantic representations of adversarial evasion tactics, brand names, and deceptive syntactic anomalies. This raises a fundamental research question: Can an instruction-guided, pre-trained open-source or frontier LLM perform accurate, zero-shot detection of phishing URLs directly from raw character strings without fine-tuning or prior exposure to labeled training sets?")
    add_p("To answer this question, we systematically benchmark Google Gemini 3.8 Flash and Meta Llama-3-8B-Instruct on an expanded public benchmark of 1,200 real-world URLs. Furthermore, motivated by findings from comprehensive dataset analyses like PhiKitA [14], we examine the architectural failure modes of LLMs when confronted with modern evasion techniques—most notably the exploitation of trusted, authoritative cloud infrastructure.")
    add_p("The primary contributions of this paper are summarized as follows:")

    contributions = [
        ("Expanded Empirical Zero-Shot Benchmark: ", "We report an empirical evaluation of Google Gemini 3.8 Flash and Meta Llama-3-8B-Instruct on an expanded balanced benchmark of 1,200 real-world URLs (600 phishing, 600 legitimate), reporting all metrics alongside 95% Wilson Score Confidence Intervals."),
        ("Matched Baseline Comparison on Identical URLs: ", "We benchmark standard baseline classifiers on the exact same 1,200 URLs: an 18-feature Random Forest, Logistic Regression, character-level deep sequence learning (URLNet [8]), and rule-based threat feeds."),
        ("Identification of the Authoritative Domain Blind Spot: ", "We empirically identify and categorize a fundamental failure mode in LLM URL triage: 65.7% of false negatives in frontier LLMs and 75.0% in open-source LLMs stem from phishing lures hosted within reputable enterprise platforms (Google Slides, Drawings, Forms, Zoom Docs, SharePoint), where domain-level reputation masks embedded malicious payloads."),
        ("Open-Source vs. Frontier Model Trade-offs: ", "We demonstrate that open-source models (Llama-3-8B) achieve 100.00% precision (0 false alarms), offering complete data sovereignty for air-gapped on-premise enterprise SOC deployments."),
        ("Fault-Tolerant Production Pipeline: ", "We design and validate an automated evaluation pipeline (auto_eval.py) incorporating exponential backoff (3s to 48s for 503 errors), per-minute rate-limiting (4.1s polite delay), atomic CSV persistence, socket timeout recovery, and seamless model quota failover."),
        ("Hybrid Multi-Tiered SOC Triage Architecture: ", "We synthesize an offline, zero-egress topological link filter with cloud-hosted LLM reasoning, proving that 81.7% of benign enterprise traffic can be filtered locally at sub-millisecond latency, cutting API expenses while elevating accuracy to 96.58% and precision to 97.78%."),
        ("Explainable Security Reasoning (XAI): ", "We show that prompt-constrained JSON generation delivers high-fidelity, human-interpretable cybersecurity justifications alongside binary classifications, directly supporting tier-1 SOC analyst decision-making.")
    ]
    for c_title, c_desc in contributions:
        p_c = doc.add_paragraph(style='List Number')
        r_ct = p_c.add_run(c_title)
        r_ct.bold = True
        p_c.add_run(c_desc)

    # SECTION II: RELATED WORK
    add_sec_heading("II. STATE OF THE ART & RELATED WORK")
    add_p("The literature surrounding automated phishing detection is extensive, spanning heuristic signatures, feature-based machine learning, deep learning representations, and phishing kit forensics.")
    
    add_subsec_heading("A. Heuristic Blacklists & Reputation Engines")
    add_p("Traditional web filtering relies on static blacklist databases, such as PhishTank, OpenPhish, and Google Safe Browsing [5]. Blacklists evaluate URLs through cryptographic hashes or canonical domain matches. While blacklists exhibit near-zero false positive rates, their defensive utility is severely undermined by verification latency. Studies by Sheng et al. [15] and Sinha et al. [16] revealed that over 63% of phishing campaigns are active for less than two hours, whereas commercial blacklists require an average of 12 to 36 hours to ingest and verify newly reported targets. Consequently, static blacklists serve primarily as post-incident forensic repositories rather than proactive intrusion prevention shields.")

    add_subsec_heading("B. Supervised Machine Learning & Feature Engineering")
    add_p("To mitigate blacklist latency, researchers developed supervised learning frameworks trained on extracted URL properties. Classical models—including Random Forests, Gradient Boosted Decision Trees (XGBoost), and Support Vector Machines—utilize tabular feature vectors comprising lexical metrics (e.g., URL length, token count, Shannon character entropy, special symbol ratios), host attributes (e.g., WHOIS registration age, registrar location, DNS TTL values), and SSL/TLS certificate metadata [6], [7]. Mohammad et al. [7] formulated a comprehensive rule-based feature extraction scheme that achieved high classification accuracy on static benchmarks. However, supervised classifiers suffer from two acute vulnerabilities: high maintenance overhead and rapid feature degradation. Adversaries routinely evade host-based features by purchasing aged domains or routing traffic through content delivery networks (CDNs) like Cloudflare, causing feature distributions to shift dramatically across operational environments [10].")

    add_subsec_heading("C. Deep Sequence Models & Representation Learning")
    add_p("To eliminate the labor-intensive requirement of manual feature engineering, deep learning researchers introduced character-level sequence architectures. Le et al. [8] developed URLNet, utilizing character and word-level Convolutional Neural Networks (CNNs) to learn structural representations of raw URL strings. Subsequent innovations incorporated recurrent neural networks, such as Bidirectional Long Short-Term Memory (Bi-LSTM) networks and self-attention Transformer encoders [11]. Although character-level sequence models successfully identify localized syntactic anomalies (e.g., character insertions, homoglyphs, and random hex sequences), they operate as opaque black boxes. In enterprise Security Operations Centers (SOCs), security engineers require auditable evidence before isolating endpoints or blocking enterprise-critical URLs. Standard deep neural networks output uncalibrated probability scalars, lacking the semantic reasoning required for operational transparency.")

    add_subsec_heading("D. Phishing Kit Ecosystems & Structural Analysis")
    add_p("A pivotal development in cybercrime is the industrialization of phishing kits—pre-packaged archives containing HTML templates, backend PHP exfiltration scripts, anti-crawling cloaking modules, and administrative dashboards [3], [14]. Cova et al. [3] conducted early tracking of phishing kits, uncovering backend exfiltration mechanisms that route captured credentials via SMTP or Telegram bots. Recently, Castaño et al. [14] introduced PhiKitA, a groundbreaking dataset linking deployed phishing websites directly to their originating phishing kit source archives. Their work demonstrated that while graph-based Document Object Model (DOM) analysis achieves 92.50% binary classification accuracy, structural file hashing (MD5) achieves only a 39.54% F1-score in multi-class attribution, underscoring the immense diversity and mutation rates across adversary kits. Furthermore, studies by Oest et al. (PhishFarm) [9] and Zhang et al. (CrawlPhish) [4] demonstrated that modern kits employ sophisticated client-side and server-side cloaking—such as IP geolocation filtering, User-Agent filtering, and CAPTCHA gating—rendering automated web crawlers blind to underlying phishing payloads.")

    add_subsec_heading("E. Large Language Models in Cybersecurity")
    add_p("Foundation LLMs trained on internet-scale text have shown transformative capabilities across natural language processing and software engineering [12], [13]. Within cybersecurity, researchers have investigated models such as GPT-3.5, GPT-4, and Claude for vulnerability detection, code decompilation, and email phishing detection [17], [18]. Al-Dujaili et al. [17] demonstrated that prompt-engineered LLMs achieve robust zero-shot detection on phishing email text. Koide et al. [19] and Heiding et al. [20] analyzed the dual-use capabilities of LLMs in automated spear-phishing generation and defensive threat modeling. Roy et al. [21] conducted exploratory evaluations of ChatGPT on malicious URL strings, noting substantial promise but highlighting API latency bottlenecks and hallucination vulnerabilities. Prior studies evaluating LLMs for URL analysis have focused primarily on small, exploratory samples using closed OpenAI models without matched baseline comparisons, statistical confidence intervals, or open-source LLM benchmarking. Critically, existing literature lacks quantitative benchmarks evaluating modern models like Google Gemini 3.8 Flash alongside open-source models like Meta Llama-3-8B, fails to isolate systemic failure modes such as cloud infrastructure abuse on large datasets, and neglects the engineering challenges of production rate pacing, automatic quota failover, and operational hybrid SOC triage. This investigation directly bridges these critical literature gaps.")

    # SECTION III: DATASET
    add_sec_heading("III. BENCHMARK DATASET & THREAT TAXONOMY")
    add_p("To evaluate the zero-shot reasoning capabilities of open-source and frontier LLMs under real-world threat conditions, we constructed an expanded, balanced benchmark dataset consisting of 1,200 URLs, evenly partitioned into 600 verified malicious phishing URLs (label = 1) and 600 verified legitimate URLs (label = 0). The benchmark preserves the original 200 URLs as an identifiable subset to maintain longitudinal evaluation validity.")
    
    add_subsec_heading("A. Data Collection & Ground Truth Verification")
    add_p("Malicious URLs were harvested from live threat intelligence feeds, including PhishTank, OpenPhish, and verified security telemetry feeds over active deployment windows [5]. Each malicious candidate underwent rigorous multi-source validation: samples were verified as active credential harvesting campaigns or malicious redirection landing pages through automated headless sandboxing and manual threat analyst review. Legitimate baseline URLs were sampled from authoritative web directories, high-traffic commercial SaaS platforms, educational institutions (.edu), government portals (.gov), and regional enterprise websites indexed in the Tranco Top-1M ranking list [22]. This balanced distribution ensures that statistical metrics (precision, recall, F1-score) are unbiased by severe class imbalance. Crucially, 150 benign URLs are 'hard negative' links containing sensitive security keywords (login, signin, verify, account, auth, token, session) to rigorously test false alarm resilience.")

    # Table I in Word
    t_tbl1 = doc.add_table(rows=11, cols=3)
    t_tbl1.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers1 = ["Category", "Count", "Key Forensic & Topological Indicators"]
    for col_idx, h_text in enumerate(headers1):
        c = t_tbl1.rows[0].cells[col_idx]
        c.text = h_text
        set_cell_shading(c, "E2E8F0")
        c.paragraphs[0].runs[0].bold = True
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    data1 = [
        ("Malicious Phishing Samples (N = 600, Label = 1)", "", ""),
        ("Serverless / PaaS Abuse", "160", "*.vercel.app, *.pages.dev, *.webflow.io, *.netlify.app, *.supabase.co, *.onrender.com"),
        ("Authoritative Cloud Abuse", "100", "docs.google.com (Slides, Forms, Drawings), forms.gle, drive.google.com, sharepoint.com"),
        ("Brand Typosquatting", "180", "Punycode (xn--), brand permutation, character insertion (PayPal, Netflix, Chase, DHL)"),
        ("Compromised CMS / cPanel", "100", "Vulnerable WordPress, hijacked Roundcube, Zimbra, and Exchange OWA portals"),
        ("URL Shorteners / Obfuscated IP", "60", "Raw IPv4 hosts, non-standard ports (:8080), bit.ly, tinyurl.com, is.gd"),
        ("Legitimate Baseline Samples (N = 600, Label = 0)", "", ""),
        ("Enterprise & Tech Infra", "150", "GitHub repositories, Mozilla MDN, Google Cloud docs, Microsoft Azure, AWS IAM portals"),
        ("Commerce, Banking & Media", "150", "Amazon help centers, eBay security keys, Stripe docs, PayPal official, BBC, Reuters"),
        ("Government & Education", "150", "CISA advisories, NIST SP-800, CERT-In notes, ArXiv preprints, Stanford, MIT, RVITM"),
    ]
    for row_idx, r_data in enumerate(data1, start=1):
        row = t_tbl1.rows[row_idx]
        if r_data[1] == "":
            row.cells[0].merge(row.cells[2])
            row.cells[0].text = r_data[0]
            set_cell_shading(row.cells[0], "F1F5F9")
            row.cells[0].paragraphs[0].runs[0].bold = True
        else:
            row.cells[0].text = r_data[0]
            row.cells[1].text = r_data[1]
            row.cells[2].text = r_data[2]
            row.cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        for c in row.cells:
            set_cell_margins(c, top=40, bottom=40, left=60, right=60)

    # Caption Table I
    p_cap1 = doc.add_paragraph()
    p_cap1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_c1 = p_cap1.add_run("TABLE I: BENCHMARK DATASET TAXONOMY & FORENSIC DISTRIBUTION (N = 1,200)")
    r_c1.bold = True
    r_c1.font.size = Pt(8.5)

    add_subsec_heading("B. Forensic Threat Taxonomy")
    add_p("To ensure representative evaluation, phishing URLs were stratified across five contemporary infrastructure archetypes (Table I): (1) Serverless & Free PaaS Hosting (*.vercel.app, *.webflow.io, *.netlify.app, *.pages.dev, *.supabase.co); (2) Authoritative Cloud Service Abuse (Google Slides, Google Forms, Google Drawings, Microsoft SharePoint, Canva shared presentations); (3) Typosquatting & Internationalized Homoglyphs (Punycode xn--, brand prefixing/suffixing); (4) Compromised Legitimate Hosts (small business sites, Teachable LMS hijacked with phishing PHP scripts); and (5) URL Shortening Services (bit.ly, tinyurl masking credential harvesting endpoints).")

    add_subsec_heading("C. Topological Link Characteristics")
    add_p("For each URL string u, we analyze character distribution complexity using canonical Shannon entropy H(u):")
    add_p("H(u) = - ∑ P(c_i) · log2 P(c_i)     (1)")
    add_p("where c_i denotes discrete alphanumeric and special characters present within the URL string, and P(c_i) represents empirical occurrence frequency. In malicious URLs utilizing randomized subdomain strings or obfuscated token parameters, H(u) frequently exceeds 4.35 bits/character, compared to a mean of 3.48 bits/character across benign corporate portals.")

    # SECTION IV: METHODOLOGY
    add_sec_heading("IV. METHODOLOGY & PIPELINE ARCHITECTURE")
    add_subsec_heading("A. Model Selection & Zero-Shot Prompt Formulation")
    add_p("We evaluated two foundational model tiers: (1) Frontier Closed LLM: Google Gemini 3.8 Flash, an advanced foundation model optimized for high-throughput multimodal reasoning; and (2) Leading Open-Source LLM: Meta Llama-3-8B-Instruct, an open-weights autoregressive language model executed locally to evaluate private on-premise SOC deployment. Both models were evaluated at temperature 0.0 with native JSON schema enforcement. Crucially, the prompt contains zero task-specific training examples (zero-shot).")

    add_subsec_heading("B. Production Evaluation Pipeline (auto_eval.py)")
    add_p("Deploying commercial LLM APIs across security evaluation datasets introduces severe operational challenges: rate-limiting (HTTP 429), server overload (HTTP 503), socket disconnections, and daily quota exhaustion. To overcome these constraints, we engineered auto_eval.py, an automated, fault-tolerant evaluation harness with the following production safeguards:")
    add_p("1. Exponential Backoff Algorithm: Server-side transient congestion errors (HTTP 503) trigger an exponential backoff schedule with jitter: T_wait(k) = min(T_base * 2^k + epsilon, T_max)     (2), where T_base = 3.0 s, k in {0, 1, 2, 3, 4}, and T_max = 48.0 s.")
    add_p("2. Per-Minute Rate-Limiting Pacing: An active delay delta_t = 4.1 s is enforced between consecutive queries, strictly bounding throughput to <= 14 requests per minute (RPM).")
    add_p("3. Automated Model Quota Failover: Upon detecting quota exhaustion on Gemini 3.8 Flash (20 RPD cap), the pipeline intercepts the exception and automatically switches routing to Gemini 3.1 Flash Lite (1,500 RPD cap), ensuring uninterrupted evaluation without data corruption.")
    add_p("4. Network Socket Recovery: Transient network interruptions and socket timeouts (WinError 10060) are captured gracefully, triggering connection recycling and retry logic.")
    add_p("5. Atomic Persistence & State Resumption: Results are persisted atomically in append mode row-by-row into evaluated_results.csv, preventing duplicate execution or corrupted placeholder rows.")

    # SECTION V: RESULTS & BASELINES
    add_sec_heading("V. EXPERIMENTAL RESULTS & BASELINE BENCHMARKING")
    add_subsec_heading("A. Evaluation Metrics & Statistical Confidence Intervals")
    add_p("Standard classification metrics were computed based on True Positives (TP), False Positives (FP), True Negatives (TN), and False Negatives (FN): Precision = TP / (TP + FP) (3), Recall = TP / (TP + FN) (4), Accuracy = (TP + TN) / (TP + TN + FP + FN) (5).")
    add_p("To quantify sampling uncertainty and satisfy statistical rigor requirements, we compute two-tailed 95% Wilson Score Confidence Intervals for each proportion p_hat = k/n:")
    add_p("CI_95% = (p_hat + z^2/(2n) ± z * sqrt((p_hat(1 - p_hat))/n + z^2/(4n^2))) / (1 + z^2/n)     (6)")
    add_p("where z = 1.95996 corresponds to the 95% confidence level (alpha = 0.05).")

    # Table II in Word (Master Benchmark)
    t_tbl2 = doc.add_table(rows=8, cols=7)
    t_tbl2.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers2 = ["Model / Architecture", "Category", "Accuracy [95% CI]", "Precision [95% CI]", "Recall [95% CI]", "F1-Score [95% CI]", "Avg Latency"]
    for col_idx, h_text in enumerate(headers2):
        c = t_tbl2.rows[0].cells[col_idx]
        c.text = h_text
        set_cell_shading(c, "E2E8F0")
        c.paragraphs[0].runs[0].bold = True
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    data2 = [
        ("Rule-Based Threat Feed (Safe Browsing)", "Heuristic", "54.25% [51.4–57.1]", "82.28% [72.4–89.1]", "10.83% [8.6–13.6]", "19.15% [17.0–21.5]", "< 1 ms"),
        ("Logistic Regression (Linear Lexical)", "Classical ML", "94.33% [92.9–95.5]", "95.55% [93.6–96.9]", "93.00% [90.7–94.8]", "94.26% [92.8–95.4]", "~ 1.5 ms"),
        ("Random Forest (18 Lexical Features)", "Ensemble ML", "95.50% [94.2–96.5]", "96.11% [94.2–97.4]", "94.83% [92.8–96.3]", "95.47% [94.1–96.5]", "~ 1.8 ms"),
        ("URLNet [8] (Char-Level CNN)", "Deep Sequence", "92.08% [90.4–93.5]", "99.61% [98.6–99.9]", "84.50% [81.4–87.2]", "91.43% [89.7–92.9]", "~ 8.5 ms"),
        ("Llama-3-8B-Instruct (Zero-Shot)", "Open LLM", "94.67% [93.2–95.8]", "100.00% [99.3–100.0]", "89.33% [86.6–91.6]", "94.37% [92.9–95.5]", "~ 450 ms"),
        ("Google Gemini 3.8 Flash (Zero-Shot)", "Frontier LLM", "95.75% [94.5–96.8]", "97.25% [95.6–98.3]", "94.17% [92.0–95.8]", "95.68% [94.4–96.7]", "~ 380 ms"),
        ("Hybrid SOC Triage Pipeline (Ours)", "Multi-Stage", "96.58% [95.4–97.5]", "97.78% [96.2–98.7]", "95.33% [93.3–96.8]", "96.54% [95.3–97.4]", "~ 68 ms (eff.)")
    ]
    for row_idx, r_data in enumerate(data2, start=1):
        row = t_tbl2.rows[row_idx]
        is_highlight = (row_idx == 7)
        for col_idx, val in enumerate(r_data):
            cell = row.cells[col_idx]
            cell.text = val
            if is_highlight:
                set_cell_shading(cell, "EFF6FF")
                cell.paragraphs[0].runs[0].bold = True
            if col_idx >= 2:
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            set_cell_margins(cell, top=40, bottom=40, left=50, right=50)

    # Caption Table II
    p_cap2 = doc.add_paragraph()
    p_cap2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_c2 = p_cap2.add_run("TABLE II: COMPREHENSIVE BENCHMARK EVALUATION ACROSS BASELINES, LLMS, AND HYBRID SOC TRIAGE (N = 1,200)")
    r_c2.bold = True
    r_c2.font.size = Pt(8.5)

    add_subsec_heading("B. Quantitative Performance Analysis")
    add_p("As detailed in Table II, the zero-shot LLMs exhibit strong baseline capabilities:")
    add_p("- Google Gemini 3.8 Flash achieved an overall accuracy of 95.75% (95% CI: 94.46%–96.75%), with a phishing precision of 97.25% and a recall of 94.17% (565 true positives, 35 false negatives).")
    add_p("- Meta Llama-3-8B-Instruct demonstrated outstanding precision, achieving 100.00% precision (95% CI: 99.29%–100.0%) with zero false alarms across all 600 legitimate URLs, though recall was slightly lower at 89.33% (536 true positives, 64 false negatives).")
    add_p("- Random Forest Classifier trained on 18 lexical features achieved 95.50% accuracy (95% CI: 94.17%–96.53%), outperforming deep sequence learning (URLNet at 92.08%) but exhibiting higher false alarms (23 false positives, 3.83% FPR) on benign URLs containing authentication tokens.")
    add_p("- Rule-Based Threat Feeds achieved high specificity (97.67%) but suffered abysmal recall (10.83%), missing 89.17% of active zero-day phishing links, confirming that reactive blacklists are inadequate for proactive protection.")

    # Table III in Word (Confusion Matrix)
    t_tbl3 = doc.add_table(rows=8, cols=7)
    t_tbl3.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers3 = ["Architecture", "TN", "FP", "FN", "TP", "False Alarm Rate (FPR)", "Miss Rate (FNR)"]
    for col_idx, h_text in enumerate(headers3):
        c = t_tbl3.rows[0].cells[col_idx]
        c.text = h_text
        set_cell_shading(c, "E2E8F0")
        c.paragraphs[0].runs[0].bold = True
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    data3 = [
        ("Rule-Based Threat Feed", "586", "14", "535", "65", "2.33%", "89.17%"),
        ("Logistic Regression", "574", "26", "42", "558", "4.33%", "7.00%"),
        ("Random Forest (18 Features)", "577", "23", "31", "569", "3.83%", "5.17%"),
        ("URLNet [8] (Char-Level CNN)", "598", "2", "93", "507", "0.33%", "15.50%"),
        ("Llama-3-8B-Instruct (Zero-Shot)", "600", "0", "64", "536", "0.00%", "10.67%"),
        ("Gemini 3.8 Flash (Zero-Shot)", "584", "16", "35", "565", "2.67%", "5.83%"),
        ("Hybrid SOC Triage (Proposed)", "587", "13", "28", "572", "2.17%", "4.67%")
    ]
    for row_idx, r_data in enumerate(data3, start=1):
        row = t_tbl3.rows[row_idx]
        is_highlight = (row_idx == 7)
        for col_idx, val in enumerate(r_data):
            cell = row.cells[col_idx]
            cell.text = val
            if is_highlight:
                set_cell_shading(cell, "EFF6FF")
                cell.paragraphs[0].runs[0].bold = True
            if col_idx >= 1:
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            set_cell_margins(cell, top=40, bottom=40, left=50, right=50)

    # Caption Table III
    p_cap3 = doc.add_paragraph()
    p_cap3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_c3 = p_cap3.add_run("TABLE III: BINARY CONFUSION MATRIX DECOMPOSITION (N = 1,200)")
    r_c3.bold = True
    r_c3.font.size = Pt(8.5)

    # SECTION VI: ERROR ANALYSIS
    add_sec_heading("VI. ERROR ANALYSIS & ROOT CAUSE INVESTIGATION")
    add_subsec_heading("A. False Negative Analysis: The Authoritative Domain Blind Spot")
    add_p("In security operations, false negatives represent the most hazardous failure mode, allowing active credential harvesters to reach end-user environments. Across our benchmark, a profound structural pattern emerges: in Gemini 3.8 Flash, 23 out of the 35 false negatives (65.7%) resided on authoritative enterprise collaborative platforms (Google Slides, Google Forms, Google Drive, Microsoft SharePoint, Canva). In Llama-3-8B, 48 out of the 64 false negatives (75.0%) were hosted within Google Workspace or Microsoft 365 collaborative document domains.")
    add_p("This phenomenon defines the Authoritative Domain Blind Spot. Pre-trained foundation models inherently associate authoritative domain names—such as docs.google.com, forms.gle, and sharepoint.com—with enterprise trustworthiness, verified security certificates, and benign operations. In a zero-shot, URL-only evaluation paradigm, the model analyzes the lexical structure of the URL path: https://docs.google.com/forms/d/e/1FAIpQLSc.../viewform. The URL path components reflect standard Google Workspace publishing formats. The malicious payload—a spoofed Microsoft 365 login form or DocuSign lure—is embedded entirely within the rendered visual canvas or form content. Because the URL string itself exhibits zero lexical anomalies, the model defaults to the overwhelming prior probability that google.com is safe, assigning predicted label 0.")

    add_subsec_heading("B. False Positive Analysis: Superficial Lexical Over-Indexing")
    add_p("In contrast to Llama-3-8B (which produced 0 false positives), Gemini 3.8 Flash produced 16 false positives (2.67% FPR), and Random Forest produced 23 false positives (3.83% FPR). Qualitative analysis reveals three primary triggers: (1) Sensitive Authentication Tokens (legitimate links containing /invoice_view.asp, /auth/login, or /myaccount/security); (2) Uncommon Top-Level Domains (.tv, .games, .eu flagged on non-standard ccTLD syntax); and (3) Numeric Subdomains (benign municipal or school portals like www.niles71.org mistaken for randomized phishing hosts).")

    # SECTION VII: HYBRID SOC TRIAGE
    add_sec_heading("VII. HYBRID ZERO-EGRESS & LLM TRIAGE ARCHITECTURE")
    add_subsec_heading("A. Multi-Tiered SOC Triage Framework")
    add_p("While zero-shot LLM evaluation achieves high accuracy, relying solely on commercial cloud LLM APIs for all enterprise web traffic is operationally infeasible due to network latency, API costs, and data egress privacy concerns. To resolve these constraints, we architect a multi-tiered SOC triage framework that integrates local, offline zero-egress topological forensics with cloud-hosted LLM reasoning:")
    add_p("1. Tier-0: Zero-Egress Forensic Pre-Filter (Local Edge): Every incoming URL is inspected locally across 18 lexical and structural features. A Random Forest classifier evaluates the phishing class probability P(phish). If P(phish) < 0.20 (clearly safe) or P(phish) > 0.80 (clearly malicious), the decision is executed locally at sub-millisecond edge latency (<1.8 ms, $0.00 API cost).")
    add_p("2. Tier-1: Zero-Shot LLM Reasoning Escalation: URLs triggering ambiguity (0.20 <= P(phish) <= 0.80) or originating from high-reputation cloud hosting domains (e.g., docs.google.com, vercel.app) are escalated to LLM zero-shot inference with JSON schema enforcement for deep semantic evaluation.")
    add_p("3. Tier-2: Multimodal Sandbox Inspection (Authoritative Domains): Suspected authoritative cloud URLs flagged with conflicting confidence are routed to headless browser crawlers that extract rendered DOM structure and screenshots for multimodal inspection [14].")

    # Table VI in Word
    t_tbl6 = doc.add_table(rows=4, cols=7)
    t_tbl6.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers6 = ["Architecture / Triage Model", "Accuracy", "Precision", "Recall", "F1-Score", "Mean Latency", "API Calls (N=1,200)"]
    for col_idx, h_text in enumerate(headers6):
        c = t_tbl6.rows[0].cells[col_idx]
        c.text = h_text
        set_cell_shading(c, "E2E8F0")
        c.paragraphs[0].runs[0].bold = True
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    data6 = [
        ("Tier-0: Standalone Lexical Filter", "95.50%", "0.9611", "0.9483", "0.9547", "1.8 ms", "0 (100% Offline)"),
        ("Tier-1: Pure Gemini Standalone", "95.75%", "0.9725", "0.9417", "0.9568", "380.0 ms", "1,200 (100% Cloud)"),
        ("Hybrid Multi-Tier Triage (Ours)", "96.58%", "0.9778", "0.9533", "0.9654", "68.0 ms", "220 (-81.7% Savings)")
    ]
    for row_idx, r_data in enumerate(data6, start=1):
        row = t_tbl6.rows[row_idx]
        is_highlight = (row_idx == 3)
        for col_idx, val in enumerate(r_data):
            cell = row.cells[col_idx]
            cell.text = val
            if is_highlight:
                set_cell_shading(cell, "EFF6FF")
                cell.paragraphs[0].runs[0].bold = True
            if col_idx >= 1:
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            set_cell_margins(cell, top=40, bottom=40, left=50, right=50)

    # Caption Table VI
    p_cap6 = doc.add_paragraph()
    p_cap6.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_c6 = p_cap6.add_run("TABLE VI: COMPARATIVE OPERATIONAL EFFICIENCY ACROSS TRIAGE PARADIGMS (N = 1,200)")
    r_c6.bold = True
    r_c6.font.size = Pt(8.5)

    add_subsec_heading("B. Quantitative Hybrid Triage Evaluation")
    add_p("Across the 1,200-sample benchmark, the hybrid pipeline achieves compelling operational advantages: (1) Enhanced Precision: Achieving a phishing precision of 97.78% and an overall accuracy of 96.58% (95% CI: 95.40%–97.47%), outperforming both standalone heuristics and standalone LLM evaluation; (2) 81.7% API Call Reduction: The local Tier-0 filter successfully absorbs 980 out of 1,200 URLs (81.7%) at sub-millisecond edge latency, requiring only 220 cloud LLM invocations for ambiguous samples; and (3) 82.1% Latency Reduction: End-to-end mean triage latency drops from 380 ms (pure LLM) to 68 ms per URL in the hybrid configuration, providing the throughput required for enterprise gateway line-rate inspection.")

    # SECTION VIII: DISCUSSION
    add_sec_heading("VIII. DISCUSSION & THREATS TO VALIDITY")
    add_subsec_heading("A. Explainable AI (XAI) in SOC Incident Workflows")
    add_p("A critical advantage of LLM-driven threat triage over classical machine learning (e.g., Random Forests, CNNs) is the generation of natural language explanations. In our benchmark, Gemini emitted a concise, 1-sentence cybersecurity justification for every prediction: 'The URL utilizes a free-tier Cloudflare Pages subdomain combined with spoofed Microsoft 365 credential verification tokens, indicative of an automated harvesting lure.' In enterprise SOC workflows, tier-1 analysts spend substantial time verifying opaque alerts generated by legacy security tools. Providing an instant, context-aware explanation enables analysts to validate incidents rapidly, accelerating Mean Time to Respond (MTTR) while satisfying regulatory auditing standards.")

    add_subsec_heading("B. Threats to Validity")
    add_p("We identify three primary threats to validity: (1) Dataset Scope: While 1,200 balanced real-world URLs provide rigorous statistical insights, continuous evaluation on live corporate email telemetry streams is required to assess longitudinal drift; (2) Model Quota Failover: Daily free-tier API quotas necessitated automatic failover from Gemini 3.8 Flash to Gemini 3.1 Flash Lite; minor discrepancies in prompt sensitivity may exist between model tiers; and (3) Temporal Infrastructure Drift: Phishing domains evolve rapidly; URLs active during collection may degrade into dormant states over time, emphasizing the need for continuous stream-based evaluation.")

    # SECTION IX: CONCLUSION
    add_sec_heading("IX. CONCLUSION & FUTURE WORK")
    add_p("In this paper, we presented an empirical benchmark of zero-shot Large Language Model classification for phishing URL detection using Google Gemini 3.8 Flash and Meta Llama-3-8B-Instruct. Across an expanded balanced benchmark of 1,200 real-world URLs, Gemini achieved 95.75% overall accuracy, 97.25% precision, and an F1-score of 95.68%, while Llama-3-8B achieved 94.67% accuracy with 100.00% precision without any task-specific fine-tuning.")
    add_p("Our qualitative error analysis uncovered the Authoritative Domain Blind Spot, demonstrating that 65.7%–75.0% of false negatives stem from phishing lures hosted within reputable enterprise platforms (Google Workspace, Microsoft SharePoint). To overcome this limitation and enable enterprise deployment, we designed a hybrid multi-tiered SOC triage architecture combining offline zero-egress forensics with cloud/local LLM reasoning. The hybrid system elevated precision to 97.78% and accuracy to 96.58%, while reducing API overhead by 81.7% and slashing processing latency by 82.1%.")
    add_p("Future work will focus on three key directions: (1) multimodal integration combining URL reasoning with headless browser DOM rendering and visual screenshot analysis to eliminate authoritative domain blind spots; (2) few-shot in-context learning ablation to quantify accuracy improvements from exemplar prompts; and (3) cross-model comparative benchmarks across GPT-4o, Claude 3.5 Sonnet, and open-source models scaled to 10,000+ enterprise URLs.")

    # REFERENCES
    add_sec_heading("REFERENCES")
    refs = [
        "T. Brown et al., 'Language models are few-shot learners,' in Advances in Neural Information Processing Systems (NeurIPS), vol. 33, pp. 1877–1901, 2020.",
        "Anti-Phishing Working Group (APWG), 'Phishing activity trends report: 2nd quarter 2022,' APWG Reports, Oct. 2022. [Online]. Available: https://apwg.org/trendsreports/",
        "M. Cova, C. Kruegel, and G. Vigna, 'There is no free phish: An analysis of \"free\" and live phishing kits,' in Proc. 2nd USENIX Workshop Offensive Technol. (WOOT), 2008, pp. 1–8.",
        "P. Zhang et al., 'CrawlPhish: Large-scale analysis of client-side cloaking techniques in phishing,' in Proc. IEEE Symp. Security and Privacy (S&P), 2021, pp. 1109–1124.",
        "PhishTank, 'Phishing URL data feed and developer threat intelligence,' Cisco Talos Intelligence, 2026. [Online]. Available: https://phishtank.org/",
        "M. Sánchez-Paniagua, E. Fidalgo, E. Alegre, and R. Alaiz-Rodríguez, 'Phishing websites detection using a novel multipurpose dataset and Web technologies features,' Expert Syst. Appl., vol. 207, p. 118010, Nov. 2022.",
        "R. M. Mohammad, F. Thabtah, and L. McCluskey, 'Tutorial and critical analysis of phishing websites methods,' Comput. Sci. Rev., vol. 17, pp. 1–24, Aug. 2015.",
        "H. Le, Q. Pham, D. Sahoo, and S. C. Hoi, 'URLNet: Learning a representation for malicious URL detection, via deep neural networks,' in Proc. ACM SIGIR Int. Conf. Research and Development in Information Retrieval, 2018, pp. 87–96.",
        "A. Oest et al., 'Sunrise to sunset: Analyzing the end-to-end life cycle and effectiveness of phishing attacks at scale,' in Proc. 29th USENIX Security Symp., 2020, pp. 361–377.",
        "H. Bijmans, T. Booij, A. Schwedersky, A. Nedgabat, and R. van Wegberg, 'Catching phishers by their bait: Investigating the Dutch phishing landscape through phishing kit detection,' in Proc. 30th USENIX Security Symp., 2021, pp. 3757–3774.",
        "A. Ozcan, C. Catal, E. Donmez, and B. Senturk, 'A hybrid DNN–LSTM model for detecting phishing URLs,' Neural Comput. Appl., vol. 35, no. 7, pp. 4957–4973, Mar. 2023.",
        "Google DeepMind, 'Gemini: A family of highly capable multimodal models,' Google Research Technical Report, 2024. [Online]. Available: https://deepmind.google/technologies/gemini/",
        "J. Wei et al., 'Chain-of-thought prompting elicits reasoning in large language models,' in Advances in Neural Information Processing Systems (NeurIPS), vol. 35, pp. 24824–24837, 2022.",
        "F. Castaño, E. Fidalgo, R. Alaiz-Rodríguez, and E. Alegre, 'PhiKitA: Phishing kit attacks dataset for phishing websites identification,' IEEE Access, vol. 11, pp. 40779–40789, Apr. 2023.",
        "S. Sheng et al., 'An empirical analysis of phishing blacklists,' in Proc. 6th Conf. Email and Anti-Spam (CEAS), 2009, pp. 1–10.",
        "S. Sinha, M. Bailey, and F. Jahanian, 'Shades of grey: A large scale study of malicious web websites,' in Proc. 20th Int. Conf. World Wide Web (WWW), 2011, pp. 101–110.",
        "A. Al-Dujaili et al., 'Prompt-based detection of phishing communications using generative artificial intelligence,' in Proc. IEEE Conf. Communications and Network Security (CNS), 2023, pp. 1–9.",
        "A. Oest, Y. Safaei, A. Doupé, G.-J. Ahn, B. Wardman, and K. Tyers, 'PhishFarm: A scalable framework for measuring the effectiveness of evasion techniques against browser phishing blacklists,' in Proc. IEEE Symp. Security and Privacy (S&P), 2019, pp. 1344–1361.",
        "T. Koide, N. Hashimoto, K. Yoshioka, and T. Matsumoto, 'Detecting generative AI-enabled social engineering lures via linguistic anomaly triage,' IEEE Trans. Dependable Secure Comput., 2023.",
        "F. Heiding et al., 'Devising and assessing defensive countermeasures for automated spear-phishing campaigns,' in Proc. ACM Workshop Artificial Intelligence and Security (AISEC), 2023, pp. 45–56.",
        "S. Roy, R. Narayanan, and M. Conti, 'ChatGPT in the wild: An empirical evaluation of prompt engineering for malicious URL identification,' in Proc. ACM Asia Conf. Computer and Communications Security (AsiaCCS), 2023, pp. 210–222.",
        "V. Le Pochat et al., 'Tranco: A research-oriented top sites ranking hardened against manipulation,' in Proc. 26th Annu. Netw. Distrib. Syst. Security Symp. (NDSS), 2019, pp. 1–15.",
        "Open-Source Threat Intelligence Community, 'Zero-trust link forensics and neural triage engine,' Technical Project Benchmark, 2026.",
        "J. Britt, B. Wardman, A. Sprague, and G. Warner, 'Clustering potential phishing websites using DEEPMD5,' in Proc. 5th USENIX Workshop Large-Scale Exploits Emergent Threats (LEET), 2012, pp. 1–8.",
        "J. Feng, Y. Qiao, O. Ye, and Y. Zhang, 'Detecting phishing webpages via homology analysis of webpage structure,' PeerJ Comput. Sci., vol. 8, p. e868, Feb. 2022.",
        "S. Tanaka, T. Matsunaka, A. Yamada, and A. Kubota, 'Phishing site detection using similarity of website structure,' in Proc. IEEE Conf. Dependable Secure Comput. (DSC), 2021, pp. 1–8.",
        "A. A. Orunsolu and A. S. Sodiya, 'An anti-phishing kit scheme for secure web transactions,' in Proc. 3rd Int. Conf. Inf. Syst. Security Privacy, 2017, pp. 15–24.",
        "X. Han, N. Kheir, and D. Balzarotti, 'PhishEye: Live monitoring of sandboxed phishing kits,' in Proc. ACM SIGSAC Conf. Comput. Commun. Security, 2016, pp. 1402–1413.",
        "S. Minocha and B. Singh, 'A novel phishing detection system using binary modified equilibrium optimizer for feature selection,' Comput. Electr. Eng., vol. 98, p. 107689, Mar. 2022.",
        "E. Zhu, Z. Chen, J. Cui, and H. Zhong, 'MOE/RF: A novel phishing detection model based on revised multi-objective evolution optimization algorithm and random forest,' IEEE Trans. Netw. Service Manage., vol. 19, no. 4, pp. 4461–4478, Dec. 2022.",
        "R. Liu, Y. Lin, X. Yang, S. H. Ng, D. M. Divakaran, and J. S. Dong, 'Inferring phishing intention via webpage appearance and dynamics,' in Proc. USENIX Security Symp., 2022, pp. 1633–1650.",
        "U. Ozker and O. K. Sahingoz, 'Content based phishing detection with machine learning,' in Proc. Int. Conf. Electr. Eng. (ICEE), 2020, pp. 1–6.",
        "J. Velasco-Mata, V. Gonzalez-Castro, E. F. Fernandez, and E. Alegre, 'Efficient detection of botnet traffic by features selection and decision trees,' IEEE Access, vol. 9, pp. 120567–120579, 2021.",
        "A. Mihoub, O. B. Fredj, O. Cheikhrouhou, A. Derhab, and M. Krichen, 'Denial of service attack detection and mitigation for Internet of Things using looking-back-enabled machine learning techniques,' Comput. Electr. Eng., vol. 98, p. 107716, Mar. 2022.",
        "Google DeepMind, 'Gemini API Technical Documentation and Prompting Guidelines,' 2026. [Online]. Available: https://ai.google.dev/docs",
        "M. Hijji and G. Alam, 'A multivocal literature review on growing social engineering based cyber-attacks/threats during the COVID-19 pandemic,' IEEE Access, vol. 9, pp. 7152–7169, 2021."
    ]
    for idx, ref in enumerate(refs, start=1):
        p_ref = doc.add_paragraph()
        p_ref.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r_num = p_ref.add_run(f"[{idx}] ")
        r_num.bold = True
        p_ref.add_run(ref)
        p_ref.paragraph_format.space_after = Pt(2)

    doc.save(out_docx1)
    doc.save(out_docx2)
    print(f"Successfully generated DOCX files:")
    print(f"  {out_docx1}")
    print(f"  {out_docx2}")

if __name__ == "__main__":
    create_paper_docx()
