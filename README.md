# Security Champion Dashboard 🛡

> **Vulnerability Remediation Dashboard** — Upload any Polaris, Checkmarx, Veracode, SonarQube or other SAST/SCA Excel export and instantly get CWE remediation guidance, code fix examples, effort estimates, and sprint action plans.

**Powered by IBM Bob · Watsonx AI (ibm/granite-3-8b-instruct) · Polaris Remediation MCP · IBM ICA Agent**

---

## 🚀 Live Demo

**GitHub Pages (always live):**
```
https://sowndharya123-dev.github.io/watsonsec/
```

**IBM Cloud Foundry (after CF deploy):**
```
https://security-champion-dashboard.<your-cf-domain>.mybluemix.net
```

> Open the dashboard, upload any `.xlsx` vulnerability export, and get an instant remediation report — no login required.

---

## 📁 Project Structure

```
security-champion-dashboard/
├── public/
│   └── index.html              # Main dashboard (self-contained HTML + SheetJS)
├── server/
│   └── app.js                  # Express static server (IBM Cloud entry point)
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions CI/CD → IBM Cloud auto-deploy
├── Dockerfile                  # Docker build for IBM Code Engine / IKS
├── manifest.yml                # IBM Cloud Foundry deployment manifest
├── .cfignore                   # Files excluded from CF push
├── .dockerignore               # Files excluded from Docker build
├── .gitignore                  # Files excluded from Git
├── package.json                # Node.js dependencies
└── README.md                   # This file
```

---

## ⚡ Quick Start — Local

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/security-champion-dashboard.git
cd security-champion-dashboard

# 2. Install dependencies
npm install

# 3. Start the server
npm start

# 4. Open in browser
open http://localhost:3000
```

---

## 🌐 Deploy to IBM Cloud

### Option A — IBM Cloud Foundry (Recommended — Simplest)

**Prerequisites:**
- [IBM Cloud account](https://cloud.ibm.com/registration)
- [IBM Cloud CLI](https://cloud.ibm.com/docs/cli) installed

```bash
# 1. Login to IBM Cloud
ibmcloud login --apikey YOUR_API_KEY -r us-south

# 2. Install CF plugin (first time only)
ibmcloud cf install

# 3. Target your org and space
ibmcloud target -o YOUR_ORG -s YOUR_SPACE

# 4. Deploy
ibmcloud cf push

# 5. Get your app URL
ibmcloud cf app security-champion-dashboard
```

Your dashboard will be live at: `https://security-champion-dashboard.<region>.mybluemix.net`

---

### Option B — Docker + IBM Code Engine

```bash
# 1. Login to IBM Container Registry
ibmcloud login --apikey YOUR_API_KEY -r us-south
ibmcloud cr login
ibmcloud cr namespace-add YOUR_NAMESPACE

# 2. Build and push Docker image
docker build -t us.icr.io/YOUR_NAMESPACE/security-champion-dashboard:latest .
docker push us.icr.io/YOUR_NAMESPACE/security-champion-dashboard:latest

# 3. Deploy to IBM Code Engine
ibmcloud ce application create \
  --name security-champion-dashboard \
  --image us.icr.io/YOUR_NAMESPACE/security-champion-dashboard:latest \
  --registry-secret YOUR_REGISTRY_SECRET \
  --port 3000 \
  --min-scale 1 \
  --max-scale 3

# 4. Get URL
ibmcloud ce application get --name security-champion-dashboard --output url
```

---

## 🤖 GitHub Actions Auto-Deploy (CI/CD)

Every push to `main` automatically deploys to IBM Cloud.

### Setup — Add These GitHub Secrets

Go to your repository → **Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Value | Where to Find |
|---|---|---|
| `IBM_CLOUD_API_KEY` | Your IBM Cloud API key | [IBM Cloud → Manage → API Keys](https://cloud.ibm.com/iam/apikeys) |
| `IBM_CLOUD_REGION` | e.g. `us-south` or `eu-gb` | Your IBM Cloud region |
| `IBM_CLOUD_RESOURCE_GROUP` | e.g. `Default` | IBM Cloud → Resource groups |
| `IBM_CF_ORG` | Your CF organisation name | `ibmcloud cf orgs` |
| `IBM_CF_SPACE` | Your CF space name | `ibmcloud cf spaces` |

Once secrets are added, push to `main` → GitHub Actions runs → IBM Cloud is updated automatically.

---

## 📊 How the Dashboard Works

1. **Upload** any vulnerability export (`.xlsx` or `.csv`) from Polaris, Checkmarx, Veracode, SonarQube, Snyk, etc.
2. **Auto-parse** — SheetJS reads the file in-browser, auto-detects column names
3. **Dashboard renders** — KPI cards, bar charts, findings table with filters
4. **Remediation tab** — CWE-specific guidance with vulnerable vs fixed code examples
5. **Effort & Action Plan** — sprint priority, effort estimate, per-finding owner assignment
6. **Export** — filtered CSV export for Jira / ServiceNow import

### Supported CWEs (Built-in Library)
- CWE-404 — Improper Resource Shutdown (IDisposable / C# WPF)
- CWE-284 — Improper Access Control (Jenkins/Kubernetes YAML)
- CWE-89  — SQL Injection (6 languages)
- CWE-79  — Cross-Site Scripting / XSS (6 languages)
- CWE-22  — Path Traversal (4 languages)
- CWE-798 — Hardcoded Credentials (6 languages)
- **Any other CWE** — auto-generated generic guidance

### Supported Vulnerability Tools
Polaris · Checkmarx · Veracode · SonarQube · Snyk · Fortify · GitHub Advanced Security · CodeQL · Semgrep · Bandit · OWASP ZAP · Burp Suite · Trivy · Grype · Manual pentest reports

---

## 🔧 Adding New CWEs

Edit `public/index.html` and add an entry to the `CWE_LIBRARY` object:

```javascript
CWE_LIBRARY['CWE-78'] = {
  title: 'OS Command Injection',
  tech: 'Any / Shell',
  what: 'User-controlled input is passed to OS command execution APIs...',
  impact: 'Remote Code Execution — complete system compromise.',
  effort: '2–4 hrs per occurrence',
  risk: 'Low — use allowlists and avoid shell APIs',
  sprint: 'Immediate',
  steps: [
    'Replace shell execution with direct API calls',
    'Use allowlists for permitted commands',
    ...
  ],
  vuln: `// BAD: subprocess.call("ping " + userInput, shell=True)`,
  fix:  `// GOOD: subprocess.run(["ping", userInput], shell=False)`
};
```

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Pure HTML + CSS + JavaScript (no framework) |
| Excel Parsing | [SheetJS](https://sheetjs.com/) (in-browser) |
| Server | Node.js + Express (static file server) |
| Deployment | IBM Cloud Foundry / Docker + IBM Code Engine |
| CI/CD | GitHub Actions |
| AI Engine | IBM Bob + Watsonx AI + Polaris Remediation MCP |

---

## 📜 License

MIT — free to use, modify, and deploy.

---

*Built with ❤️ using IBM Bob & Watsonx AI — Security Champion Dashboard*
