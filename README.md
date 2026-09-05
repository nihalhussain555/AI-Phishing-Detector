# 🛡️ AI Phishing Detector & Web Trust Analyzer

> **An AI-powered web security and information verification platform that analyzes website URLs, domains, and online claims to identify phishing threats, suspicious domains, and potentially misleading information.**

---

## 📌 Overview

**AI Phishing Detector & Web Trust Analyzer** is an AI-powered cybersecurity and information verification system designed to help users determine whether a website, URL, domain, or online claim should be trusted.

The platform combines:

* 🤖 Machine Learning
* 🔗 URL analysis
* 🌐 Website analysis
* 🔍 Domain intelligence
* 🛡️ Phishing detection
* 📰 Fact verification
* 📊 Risk scoring
* 🧠 Explainable AI

Instead of providing only a simple **"Safe" or "Phishing"** result, the system provides a detailed explanation of the detected risks.

---

## 🚀 Live Demo

🌐 **Try the AI Phishing Detector:**
**[Live Demo](https://ai-phishing-detector-tnlt.onrender.com/)**

### 🔗 Quick Test

Enter a website URL into the analyzer:

```text
https://example.com
```

The system analyzes the URL and provides:

```text
┌──────────────────────────────────────┐
│        AI WEB TRUST ANALYZER         │
├──────────────────────────────────────┤
│                                      │
│ URL: https://example.com             │
│                                      │
│ Risk Score: 12 / 100                 │
│ Status: 🟢 LOW RISK                  │
│                                      │
│ ✓ HTTPS Enabled                      │
│ ✓ Normal URL Structure               │
│ ✓ No Suspicious Indicators           │
│                                      │
└──────────────────────────────────────┘
---

# 🎯 Core Modules

The project is divided into three major intelligence systems:

```text
                    AI WEB TRUST ANALYZER
                            │
             ┌──────────────┼──────────────┐
             │              │              │
             ▼              ▼              ▼
       WEBSITE/URL       DOMAIN        FACT CHECK
        ANALYSIS         ANALYSIS       VERIFICATION
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                    AI RISK ASSESSMENT
                            │
                            ▼
                    TRUST / WARNING
```

---

# 🔗 1. Website URL Analysis

Users can enter any website URL for analysis.

The system analyzes:

* URL length
* HTTPS availability
* Domain structure
* Subdomains
* Special characters
* Suspicious keywords
* IP-based URLs
* URL depth
* Redirects
* Domain similarity
* Login-related paths

---

# 🌐 2. Website Content Analysis

The system can inspect:

* HTML forms
* Password inputs
* Login fields
* Hidden fields
* External links
* Form actions
* JavaScript
* Iframes
* Redirect behavior
* Credential collection patterns

---

# 🔍 3. Domain Analysis

The domain analyzer evaluates:

* Domain structure
* HTTPS
* SSL information
* Domain age
* Subdomains
* Redirects
* IP-based URLs
* Suspicious TLDs
* Typosquatting
* Brand impersonation

---

# 🏷️ 4. Brand Impersonation Detection

Example:

```text
URL:

paypa1-secure-login.example

Possible Brand:

PayPal

Similarity:

96%

⚠️ BRAND IMPERSONATION DETECTED
```

---

# 📰 5. AI Fact Verification

The system can analyze claims from:

* News articles
* Social media
* Blogs
* Messages
* Websites
* User-provided text

The system searches available fact-checking evidence and provides an understandable assessment.

Possible results:

```text
✅ TRUE

🟢 MOSTLY TRUE

🟡 PARTIALLY TRUE

🟠 MISLEADING

🔴 MOSTLY FALSE

🚨 FALSE

⚪ UNVERIFIED
```

---

# 📚 6. Evidence-Based Verification

```text
User Claim
    ↓
Claim Extraction
    ↓
Fact-Check Search
    ↓
Trusted Source Search
    ↓
Evidence Collection
    ↓
Evidence Comparison
    ↓
AI Reasoning
    ↓
Final Assessment
```

---

# 📊 7. Unified Trust Score

The system combines multiple signals into an understandable score.

```text
                    TRUST SCORE
                        78/100
                           │
             ┌─────────────┼─────────────┐
             │             │             │
          URL Risk     Domain Risk    Content
             │             │             │
             85            72            76
```

---

# 🤖 8. Explainable AI

The system explains why a website or claim received a particular result.

Example:

```text
AI EXPLANATION

Risk Score: 91/100

Main Reasons:

1. Suspicious domain structure
2. Brand name similarity detected
3. Login credentials requested
4. Website contains suspicious redirects
5. Domain characteristics indicate elevated risk
```

---

# 📈 9. Security Dashboard

The dashboard displays:

* Total scans
* Phishing detections
* Suspicious domains
* Fact checks
* Unverified claims
* Recent activity
* Risk distribution
* Scan history

---

# 📝 10. Detailed Analysis Reports

### Website Report

```text
Target URL
Classification
Risk Score
Domain Information
Security Indicators
Detected Threats
AI Explanation
Recommended Actions
```

### Fact Verification Report

```text
Claim
Claimant
Verdict
Confidence
Evidence
Fact-check sources
Publication dates
AI explanation
```

---

# 🗄️ 11. Scan History

MongoDB stores analysis history including:

* URLs
* Domains
* Claims
* Results
* Risk scores
* Dates
* Reports

---

# 🛠️ Technology Stack

## Frontend

* HTML5
* CSS3
* JavaScript
* Responsive UI
* Interactive dashboard

## Backend

* Python
* Flask
* REST API
* Requests
* BeautifulSoup

## Machine Learning

* Scikit-learn
* XGBoost
* Pandas
* NumPy
* Joblib

## Database

* MongoDB
* MongoDB Atlas
* PyMongo

## AI / NLP

* Natural Language Processing
* Text classification
* Claim extraction
* Similarity analysis
* Explainable AI

---

# 🏗️ Architecture

```text
                         USER
                           │
                           ▼
                  ┌─────────────────┐
                  │  WEB FRONTEND   │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │    FLASK API    │
                  └────────┬────────┘
                           │
          ┌────────────────┼─────────────────┐
          │                │                 │
          ▼                ▼                 ▼
    ┌───────────┐    ┌───────────┐    ┌────────────┐
    │ URL       │    │ DOMAIN    │    │ FACT       │
    │ ANALYZER  │    │ ANALYZER  │    │ VERIFIER   │
    └─────┬─────┘    └─────┬─────┘    └─────┬──────┘
          │                │                 │
          ▼                ▼                 ▼
    ┌───────────┐    ┌───────────┐    ┌────────────┐
    │ ML MODEL  │    │ THREAT    │    │ EVIDENCE   │
    │           │    │ INTEL     │    │ SEARCH     │
    └─────┬─────┘    └─────┬─────┘    └─────┬──────┘
          │                │                 │
          └────────────────┼─────────────────┘
                           ▼
                  ┌─────────────────┐
                  │ AI RISK ENGINE  │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ RESULT + REPORT │
                  └────────┬────────┘
                           │
                           ▼
                     ┌───────────┐
                     │  MongoDB  │
                     └───────────┘
```

---

# 📂 Project Structure

```text
AI-Phishing-Detector/
│
├── frontend/
├── backend/
├── ml/
├── dataset/
├── screenshots/
│   ├── dashboard.png
│   ├── url-analysis.png
│   ├── domain-analysis.png
│   ├── fact-verification.png
│   └── demo.gif
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

# ⚙️ Installation

```bash
git clone https://github.com/YOUR_USERNAME/AI-Phishing-Detector.git
cd AI-Phishing-Detector

python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# 🔐 Environment Variables

Create a `.env` file:

```env
MONGO_URI=your_mongodb_connection_string
SECRET_KEY=your_secret_key
FACTCHECK_API_KEY=your_api_key
```

**Never commit `.env` to GitHub.**

---

# ▶️ Run the Application

```bash
python app.py
```

Open the application in your browser.

---

# 🚀 Future Enhancements

* [ ] Chrome / Edge browser extension
* [ ] Real-time website protection
* [ ] Screenshot phishing detection
* [ ] Email phishing detection
* [ ] SMS scam detection
* [ ] Multilingual fact verification
* [ ] Image-based misinformation detection
* [ ] AI-generated threat reports
* [ ] PDF report generation
* [ ] Advanced domain reputation scoring
* [ ] WHOIS/RDAP integration
* [ ] DNS analysis
* [ ] SSL certificate analysis
* [ ] Threat intelligence feeds
* [ ] Real-time notifications
* [ ] Deep Learning models
* [ ] Transformer-based claim verification

---

# 🎯 Project Objectives

* Detect phishing websites.
* Analyze suspicious URLs.
* Analyze domain-level risks.
* Identify possible brand impersonation.
* Inspect website security indicators.
* Verify online claims against available evidence.
* Provide explainable AI results.
* Generate understandable risk scores.
* Maintain scan history.
* Help users make safer decisions online.

---

# 🛡️ Security Disclaimer

This project is intended for **educational, research, and defensive cybersecurity purposes**.

Automated AI predictions are not guaranteed to be correct. Fact verification results should be interpreted together with the cited evidence and source information rather than treated as absolute truth.

---

# 👨‍💻 Author

**Nihal Hussain**

Computer Science & Engineering Student

### Interests

* Artificial Intelligence
* Machine Learning
* Cybersecurity
* Full-Stack Development
* Generative AI
* Information Verification

---

# ⭐ Support

If you find this project useful, consider giving the repository a ⭐.

---

# 📜 License

This project is licensed under the **MIT License**.
