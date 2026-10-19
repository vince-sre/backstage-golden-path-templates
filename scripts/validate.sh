#!/usr/bin/env bash
# Everything CI runs. Needs: python3 + requirements-dev.txt, shellcheck,
# actionlint, kubeconform, terraform, tflint, curl.
set -euo pipefail
cd "$(dirname "$0")/.."

CRDS='https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json'
OUT=.rendered
rm -rf "$OUT"

echo "==> lint"
yamllint -s .
ruff check .
shellcheck scripts/*.sh

echo "==> schemas + template/render tests"
[[ -d .schemas ]] || ./scripts/fetch-schemas.sh
python3 -m pytest -q -p no:cacheprovider tests

echo "==> python-service: render and validate the GitOps manifests"
python3 scripts/render.py templates/python-service/gitops-skeleton "$OUT/python-service-gitops" \
  name=orders-api tier=tier-1 gitopsRepo=vince-sre/gitops-argocd-platform image=ghcr.io/vince-sre/orders-api
kubeconform -strict -summary -schema-location default -schema-location "$CRDS" "$OUT/python-service-gitops/apps"

echo "==> terraform-module: render per provider, then init/validate/tflint/plan"
export TF_PLUGIN_CACHE_DIR=${TF_PLUGIN_CACHE_DIR:-$HOME/.terraform.d/plugin-cache}
mkdir -p "$TF_PLUGIN_CACHE_DIR"
for provider in aws google azurerm; do
  dir="$OUT/terraform-$provider"
  python3 scripts/render.py templates/terraform-module/skeleton "$dir" \
    name=example description="Rendered by validate.sh" owner=group:default/platform-team \
    provider="$provider" repoSlug="vince-sre/terraform-$provider-example" >/dev/null
  (
    cd "$dir"
    terraform fmt -check -recursive
    for d in . examples/basic; do
      terraform -chdir="$d" init -backend=false -input=false >/dev/null
      terraform -chdir="$d" validate >/dev/null
    done
    tflint --init >/dev/null && tflint --recursive
    terraform -chdir=examples/basic plan -input=false >/dev/null
  )
  echo "    ok terraform-$provider"
done
echo "==> all checks passed"
