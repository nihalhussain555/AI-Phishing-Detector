# 🛡️ AI Phishing Detector & Web Trust Analyzer

> **An AI-powered web security and information verification platform that analyzes website URLs, domains, and online claims to identify phishing threats, suspicious domains, and potentially misleading information.**




\

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

### Example

```text
https://example.com/login
```

The system analyzes characteristics such as:

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

### Example Result

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
       WEBSITE ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

URL:
https://example.com/login

Risk Score:
87 / 100

Status:
🚨 HIGH RISK

Detected Indicators:

✓ Suspicious URL structure
✓ Login page detected
✓ Unusual domain
✓ Multiple redirects
✓ Suspicious external resources

Recommendation:

Do not enter passwords,
OTP or financial information.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

# 🌐 2. Website Content Analysis

URL analysis alone is not always sufficient.

The system can inspect the website itself and analyze:

### HTML

* Forms
* Password inputs
* Login fields
* Hidden fields
* External links
* Form actions

### JavaScript

* Suspicious scripts
* Obfuscated code
* External script sources
* Redirect behavior

### Page Structure

* Iframes
* Embedded content
* Suspicious redirects
* Credential collection patterns

This provides deeper analysis than traditional URL-only classifiers.

---

# 🔍 3. Domain Analysis

The domain module analyzes the reputation and structure of a domain.

### Domain Information

```text
Domain:
example.com

HTTPS:
✓ Enabled

SSL:
✓ Valid

Domain Age:
2 Years

Subdomains:
3

Redirects:
1

IP-based URL:
No

Domain Risk:
LOW
```

### Suspicious Domain Detection

The system can identify:

* Newly created-looking domains
* Suspicious TLDs
* Excessive subdomains
* IP-based URLs
* Typosquatting
* Brand impersonation
* Suspicious domain patterns

---

# 🏷️ 4. Brand Impersonation Detection

The system can identify domains that attempt to imitate legitimate brands.

### Example

```text
URL:

paypa1-secure-login.example

Possible Brand:

PayPal

Similarity:

96%

⚠️ BRAND IMPERSONATION DETECTED
```

Possible techniques include:

* String similarity
* Levenshtein distance
* Character substitution detection
* Suspicious keyword analysis
* Domain structure analysis

---

# 📰 5. AI Fact Verification

The platform can analyze claims found in:

* News articles
* Social media
* Blogs
* Messages
* Websites
* User-provided text

### Example

```text
Claim:

"Scientists have confirmed that drinking
coffee completely prevents cancer."
```

The system extracts the claim and searches available fact-checking sources.

Google's Fact Check Tools API provides a Claim Search capability for finding existing fact checks, including claim text, claimant information, publisher, review URL, review date, and textual rating.

### Example Result

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
       FACT VERIFICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Claim:

"Scientists have confirmed that
coffee completely prevents cancer."

AI Assessment:

⚠️ MISLEADING

Confidence:
89%

Evidence:

✓ Existing fact-check found
✓ Claim lacks supporting evidence
✓ Scientific context is missing

Source:
Fact-check publisher

Rating:
Mostly False

Recommendation:

Do not share without additional
credible evidence.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

# 🧠 6. AI Claim Analysis

The system can break a statement into individual claims.

Example:

```text
Input:

"Government has announced free laptops
for every student and registration closes
tomorrow."
```

The AI extracts:

```text
Claim 1:
Government announced free laptops.

Claim 2:
Every student is eligible.

Claim 3:
Registration closes tomorrow.
```

Each claim can then be investigated separately.

---

# 📚 7. Evidence-Based Verification

The system should not rely only on an AI model to determine whether something is true.

The verification pipeline can be:

```text
User Claim
    ↓
Claim Extraction
    ↓
Keyword / Entity Extraction
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

# 📊 8. Unified Trust Score

The system can combine multiple signals into one understandable score.

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

For websites:

```text
URL Safety
Domain Reputation
SSL Security
Website Content
Redirect Behavior
Brand Similarity
```

For claims:

```text
Fact-Check Evidence
Source Reliability
Claim Consistency
Supporting Evidence
Contradicting Evidence
```

---

# 🤖 9. Explainable AI

The system explains **why** it reached a particular conclusion.

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

This makes the prediction more transparent than a simple ML classification.

---

# 📈 10. Security Dashboard

The dashboard provides an overview of all analyses.

```text
┌──────────────────────────────────────┐
│          WEB TRUST DASHBOARD         │
├──────────────────────────────────────┤
│                                      │
│ Total Scans              1,248       │
│ Phishing Detected          327       │
│ Suspicious Domains         184       │
│ Facts Verified              492      │
│ Unverified Claims           106      │
│                                      │
└──────────────────────────────────────┘
```

Dashboard sections:

* URL scans
* Domain scans
* Fact checks
* Threat statistics
* Recent activity
* Risk distribution
* Scan history

---

# 📝 11. Detailed Analysis Report

Each scan generates a structured report.

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

# 🗄️ 12. Scan History

MongoDB can store:

```text
User
    │
    ├── URL Scans
    ├── Domain Scans
    ├── Fact Checks
    └── Threat Reports
```

Users can view:

* Previous URLs
* Previous domain analyses
* Previous claims
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

## External Intelligence

* Fact-checking sources
* Domain information
* SSL information
* Web security intelligence

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
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   └── assets/
│
├── backend/
│   ├── app.py
│   ├── routes/
│   │   ├── url_routes.py
│   │   ├── domain_routes.py
│   │   └── factcheck_routes.py
│   │
│   ├── services/
│   │   ├── url_analyzer.py
│   │   ├── domain_analyzer.py
│   │   ├── website_analyzer.py
│   │   └── factcheck_service.py
│   │
│   ├── models/
│   └── utils/
│
├── ml/
│   ├── train_model.py
│   ├── feature_extractor.py
│   ├── predictor.py
│   └── models/
│       └── phishing_model.pkl
│
├── dataset/
│   └── phishing_dataset.csv
│
├── screenshots/
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

# ⚙️ Installation

## Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/AI-Phishing-Detector.git

cd AI-Phishing-Detector
```

## Create Virtual Environment

```bash
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

## Install Dependencies

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

Keep secrets outside GitHub and never commit your `.env` file.

---

# ▶️ Run the Application

```bash
python app.py
```

Open the application in your browser.

---

# 🔬 Machine Learning Pipeline

```text
Phishing Dataset
       ↓
Data Cleaning
       ↓
Feature Engineering
       ↓
Train/Test Split
       ↓
Model Training
       ↓
Model Evaluation
       ↓
Best Model
       ↓
Joblib Serialization
       ↓
Flask API
       ↓
Real-Time Prediction
```

---

# 📊 Model Evaluation

The project can evaluate models using:

* Accuracy
* Precision
* Recall
* F1 Score
* ROC-AUC
* Confusion Matrix

Example:

```text
Model                  F1 Score

Random Forest            0.94
XGBoost                  0.96
Logistic Regression      0.89
```

> Replace these example values with your actual model results.

---

# 🔄 Fact Verification Workflow

```text
User enters claim
        ↓
AI extracts claim
        ↓
Search fact-check databases
        ↓
Retrieve existing reviews
        ↓
Analyze publisher/source
        ↓
Compare evidence
        ↓
Generate verdict
        ↓
Show supporting sources
```

The Google Fact Check Tools API supports searching fact-checked claims and can return associated ClaimReview information, including publisher, URL, review date, and textual rating.

---

# 🎯 Project Objectives

* Detect phishing websites.
* Analyze suspicious URLs.
* Analyze domain-level risks.
* Identify possible brand impersonation.
* Inspect website security indicators.
* Verify online claims against available fact-check evidence.
* Provide explainable AI results.
* Generate understandable risk scores.
* Maintain scan history.
* Help users make safer decisions online.

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
