# Amine Agent

Local personal agent for browsing, file organization, and email workflows.

## Setup

```bash
cd ~/Desktop/amine-agent
source .venv/bin/activate
pip install -r requirements.txt
playwright install
```

Add your API key to `.env`:
```
OPENAI_API_KEY=sk-...
```

## Usage

```bash
python main.py "Go to example.com and tell me what you see"
```

## Test

```bash
python tests/test_browser.py
```

## Structure

```
agents/      — agent definitions (future: multi-agent orchestration)
browser/     — browser automation via browser-use
email/       — email workflows (phase 3)
files/       — file organization (phase 2)
app/         — shared utilities (logging, etc.)
config/      — settings and safety rules
scripts/     — helper scripts
tests/       — test tasks
logs/        — action logs (auto-generated)
```

## Safety

- Always asks before destructive actions
- Always asks before sending anything
- All actions logged to `logs/`
- Configurable in `config/settings.yaml`
