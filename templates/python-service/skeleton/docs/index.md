# ${{ values.name }}

${{ values.description }}

| | |
|---|---|
| Owner | `${{ values.owner }}` |
| Tier | `${{ values.tier }}` |
| SLO | {% if values.tier == 'tier-1' %}99.9%{% elif values.tier == 'tier-2' %}99.5%{% else %}99%{% endif %} availability (30 days) |
| Repo | [${{ values.repoSlug }}](https://github.com/${{ values.repoSlug }}) |

## Local development

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
pytest -q
python -m app.main   # http://localhost:8080/healthz
```

## How it ships

1. A PR runs tests plus an image build and scan (no push).
2. A merge to `main` builds, scans, signs (cosign keyless) and pushes `${{ values.image }}:<sha>`.
3. CI opens and auto-merges a tag bump in `${{ values.gitopsRepo }}` for **dev**; Argo CD syncs it.
4. Prod is promoted by a reviewed PR that changes `values-prod.yaml`.
