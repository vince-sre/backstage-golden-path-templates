"""Render the terraform-module skeleton for each provider and check the output.

Full `terraform init/validate/plan` per provider runs in scripts/validate.sh
(it downloads providers); here we keep to fast, offline checks.
"""

import shutil
import subprocess

import pytest
import yaml
from conftest import ROOT, load_yaml_docs
from render import render_tree

SKELETON = ROOT / "templates/terraform-module/skeleton"
PROVIDERS = ["aws", "google", "azurerm"]


@pytest.fixture(scope="module", params=PROVIDERS)
def rendered(request, tmp_path_factory):
    values = {
        "name": "s3-bucket",
        "description": "Opinionated bucket with encryption and tags",
        "owner": "group:default/platform-team",
        "provider": request.param,
        "repoSlug": f"vince-sre/terraform-{request.param}-s3-bucket",
    }
    out = tmp_path_factory.mktemp(request.param)
    render_tree(SKELETON, out, values)
    return values, out


def test_no_template_syntax_left(rendered):
    _, out = rendered
    for f in out.rglob("*"):
        if f.is_file():
            text = f.read_text(encoding="utf-8")
            assert "values." not in text and "{%" not in text, f


def test_catalog_info(rendered, validator_for):
    values, out = rendered
    (doc,) = load_yaml_docs(out / "catalog-info.yaml")
    assert not list(validator_for("ComponentV1alpha1").iter_errors(doc))
    assert doc["metadata"]["name"] == f"terraform-{values['provider']}-s3-bucket"
    assert doc["spec"]["type"] == "terraform-module"


def test_only_selected_provider_is_required(rendered):
    values, out = rendered
    versions = (out / "versions.tf").read_text()
    for p in PROVIDERS:
        assert (f'source  = "hashicorp/{p}"' in versions) == (p == values["provider"])


def test_gcp_gets_label_normalisation(rendered):
    values, out = rendered
    has_labels = 'output "labels"' in (out / "outputs.tf").read_text()
    assert has_labels == (values["provider"] == "google")


def test_workflow_yaml_keeps_github_expression(rendered):
    _, out = rendered
    wf = yaml.safe_load((out / ".github/workflows/ci.yml").read_text())
    step = next(s for s in wf["jobs"]["validate"]["steps"] if s.get("run", "").startswith("tflint"))
    assert step["env"]["GITHUB_TOKEN"] == "${{ github.token }}"


@pytest.mark.skipif(not shutil.which("actionlint"), reason="actionlint not installed")
def test_workflow_passes_actionlint(rendered):
    _, out = rendered
    res = subprocess.run(["actionlint", ".github/workflows/ci.yml"], cwd=out, capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stdout + res.stderr


@pytest.mark.skipif(not shutil.which("terraform"), reason="terraform not installed")
def test_terraform_fmt_clean(rendered):
    _, out = rendered
    res = subprocess.run(["terraform", "fmt", "-check", "-recursive", "-diff"], cwd=out, capture_output=True, text=True,
                         check=False)
    assert res.returncode == 0, res.stdout
