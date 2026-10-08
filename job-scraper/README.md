# Internship Job Scraper

Run the commands below in PowerShell from the workspace root:

```powershell
cd "C:\Users\Dat Le\auto_job"
```

## 1. Set Up Python

Create and activate the workspace virtual environment if it does not already exist:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
python -m pip install -r .\job-scraper\requirements.txt
```

If `.venv` is already active and dependencies are installed, continue to the next step.

## 2. Start Ollama

Install and start Ollama if it is not already running. In a PowerShell terminal, download the model used for local screening:

```powershell
ollama pull tev1:4b
```

Ollama must be available at `http://localhost:11434`. Keep its service running while using local AI.

## 3. Backfill Local AI Results

Try one job first:

```powershell
python .\job-scraper\backfill_ai.py --local --limit 1
```

If that succeeds, evaluate all remaining jobs that do not have a local-AI result:

```powershell
python .\job-scraper\backfill_ai.py --local
```

This step uses Ollama locally and does not call Claude. Jobs with failed local evaluations remain eligible for a later retry.

## 4. Backfill Claude Results (Optional, May Cost Money)

Set your Anthropic API key for the current PowerShell session. Replace the placeholder with your key; do not commit or share the real key:

```powershell
$env:ANTHROPIC_API_KEY = "<your Anthropic API key>"
```

First evaluate at most one job that passed local screening:

```powershell
python .\job-scraper\backfill_ai.py --claude --limit 1
```

The script asks for confirmation before sending jobs to Claude. Enter `y` to proceed or press Enter to cancel. To evaluate all remaining jobs that passed local screening, run:

```powershell
python .\job-scraper\backfill_ai.py --claude
```

Claude results are saved to SQLite. Jobs rejected by local screening are not sent to Claude.

## 5. Sync Excel

Backfill commands refresh the workbook automatically if it already exists. To create or manually refresh it at any time, run:

```powershell
python .\job-scraper\excel_tracker.py
```

Open the tracker here:

```powershell
start .\job-scraper\job_tracker.xlsx
```

SQLite in `job-scraper\jobs.db` remains the source of truth. The Excel sync preserves manual values in `Status`, `Applied Date`, `Interview`, and `Notes` for matching job URLs.

## Scrape New Jobs

To scrape and run the normal local-AI then Claude workflow for new jobs, set `ANTHROPIC_API_KEY`, make sure Ollama is running, and run:

```powershell
python .\job-scraper\scraper.py
python .\job-scraper\excel_tracker.py
```

The scraper needs the API key and the `job-scraper\resume.pdf` file for Claude evaluation. To scrape without AI evaluation, use:

```powershell
python .\job-scraper\scraper.py --no-ai
```

Then use the backfill steps above when you are ready to evaluate saved jobs.
