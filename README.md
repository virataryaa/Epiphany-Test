# Epiphany Test

Super-basic Streamlit SnD (supply & demand) balance app.

```
Database/snd.csv   <- the only data file (inputs only)
Code/app.py        <- the app (table, charts, slider, edit page)
```

## Update the data
- **In the app:** sidebar -> *Update data* -> edit cells -> *Save*. With `GITHUB_TOKEN` in Streamlit secrets, the save commits `Database/snd.csv` to this repo.
- **By hand:** edit `Database/snd.csv` in Excel/GitHub and push.

CSV rules: `type` is `origin`, `consumption` or `stock` (opening end-stock, first season only).
Production, Balance, End stock, Consumption % and S/U are calculated, never typed.

## Secrets (Streamlit Cloud -> App settings -> Secrets)
```toml
GITHUB_TOKEN = "github_pat_..."     # fine-grained, this repo only, Contents: Read and write
GITHUB_REPO  = "virataryaa/Epiphany-Test"
GITHUB_BRANCH = "main"
```

## Run locally
`pip install -r requirements.txt` then `run.bat` (or `streamlit run Code/app.py`).
