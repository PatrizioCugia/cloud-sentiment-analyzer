# Cloud Sentiment Analyzer

BERT-based sentiment analysis for Reddit discussions about cloud providers (AWS, Azure, Google Cloud, etc.), categorized by business aspects (cost, performance, security, scalability, support). Exports clean CSVs and includes performance stats.

## 1) Prerequisites

- Python 3.9+ (recommended)
- Git installed
- A GitHub account
- Reddit API credentials:
  - Go to https://www.reddit.com/prefs/apps
  - Click "Create another app..." (type: script)
  - Copy your client_id and client_secret.

## 2) Local setup (noob-friendly)

Open a terminal (PowerShell on Windows, Terminal on macOS/Linux), then:

```bash
# Create and enter a project folder
mkdir cloud-sentiment-analyzer
cd cloud-sentiment-analyzer

# Create a virtual environment
# Windows (PowerShell):
python -m venv .venv
. .venv/Scripts/Activate.ps1

# macOS/Linux:
# python3 -m venv .venv
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 3) Credentials Setup

Copy the example environment file and fill in your Reddit API credentials:

```bash
# Copy the example file
cp .env.example .env
```

Edit the `.env` file with your Reddit API credentials:
- Go to https://www.reddit.com/prefs/apps
- Click "Create another app..." (type: script)
- Copy your `client_id` and `client_secret`
- Update the `.env` file with your actual values

Your `.env` file should look like:
```
REDDIT_CLIENT_ID=your_actual_client_id
REDDIT_CLIENT_SECRET=your_actual_client_secret
REDDIT_USER_AGENT=cloud-analyzer:v1.0 (by u/YourRedditUsername)
```

**Alternative: Environment Variables (if not using .env file)**

You can also set credentials as environment variables directly:

- Windows PowerShell (current session):
```powershell
$env:REDDIT_CLIENT_ID="YOUR_CLIENT_ID"
$env:REDDIT_CLIENT_SECRET="YOUR_CLIENT_SECRET"
$env:REDDIT_USER_AGENT="cloud-analyzer:v1.0 (by u/YourRedditUsername)"
```

- macOS/Linux (current session):
```bash
export REDDIT_CLIENT_ID="YOUR_CLIENT_ID"
export REDDIT_CLIENT_SECRET="YOUR_CLIENT_SECRET"
export REDDIT_USER_AGENT="cloud-analyzer:v1.0 (by u/YourRedditUsername)"
```

Tip: To persist these across sessions, add those export lines to your shell profile (~/.zshrc or ~/.bashrc), or set them before each run.

## 4) Run the analyzer

```bash
python cloud_sentiment_analyzer.py
```

On the first run, the model will download (~100–500MB). That’s normal.

Outputs created:
- sentiment_analysis_results.csv
- performance_metrics.csv
- detailed_sentiment_data.csv

## 5) Create your GitHub repo and push your code

Option A — Using the GitHub website (easiest)
1. Go to https://github.com/new
2. Repository name: cloud-sentiment-analyzer
3. Description: BERT-based sentiment analysis for Reddit cloud discussions
4. Set to Public
5. Don’t add a README (you already have one locally)
6. Click Create repository
7. Follow the “...or push an existing repository from the command line” instructions. Example:

```bash
git init
git add .
git commit -m "Initial commit: BERT Reddit cloud sentiment analyzer"
git branch -M main
git remote add origin https://github.com/YourUsername/cloud-sentiment-analyzer.git
git push -u origin main
```

Option B — Using GitHub CLI (optional)
```bash
gh repo create cloud-sentiment-analyzer --public --source=. --remote=origin --push
```

## 6) Common issues (and fixes)

- Model download is slow: this is expected on first run. Subsequent runs use the cache.
- torch install issues on Windows: ensure you’re using Python 3.9–3.11. If you have a GPU, install torch from https://pytorch.org for your CUDA version.
- Reddit errors or rate limits: reduce num_posts in the script.
- “Module not found”: Ensure your virtual environment is activated before running the script.
- Don’t hardcode secrets: never commit credentials. This repo reads them from environment variables.

## 7) How to update the repo later

```bash
# Make changes to files...
git add .
git commit -m "Describe your change"
git push
```

## License
MIT
