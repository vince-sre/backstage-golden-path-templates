"""Render the python-service skeletons with sample answers and check the output."""

import shutil
import subprocess
import sys

import pytest
import yaml
from conftest import ROOT, load_yaml_docs
from render import render_tree

TEMPLATE = ROOT / "templates/python-service"

CASES = {
    "tier1-with-system": {
        "name": "orders-api",
        "description": 'Order intake API: "fast" path',
        "owner": "group:default/team-orders",
        "system": "commerce",
        "tier": "tier-1",
        "repoSlug": "vince-sre/orders-api",
        "image": "ghcr.io/vince-sre/orders-api",
        "gitopsRepo": "vince-sre/gitops-argocd-platform",
    },
    "tier3-no-system": {
        "name": "report-builder",
        "description": "Nightly report generator",
        "owner": "group:default/platform-team",
        "system": "",
        "tier": "tier-3",
        "repoSlug": "vince-sre/report-builder",
        "image": "ghcr.io/vince-sre/report-builder",
        "gitopsRepo": "vince-sre/gitops-argocd-platform",
    },
}

SERVICE_KEYS = ["name", "description", "owner", "system", "tier", "repoSlug", "image", "gitopsRepo"]
GITOPS_KEYS = ["name", "tier", "gitopsRepo", "image"]


@pytest.fixture(scope="module", params=list(CASES), ids=list(CASES))
def rendered(request, tmp_path_factory):
    answers = CASES[request.param]
    out = tmp_path_factory.mktemp(request.param)
    render_tree(TEMPLATE / "skeleton", out / "service", {k: answers[k] for k in SERVICE_KEYS})
    render_tree(TEMPLATE / "gitops-skeleton", out / "gitops", {k: answers[k] for k in GITOPS_KEYS})
    return answers, out


def test_no_template_syntax_left(rendered):
    _, out = rendered
    for f in out.rglob("*"):
        if f.is_file():
            text = f.read_text(encoding="utf-8")
            assert "values." not in text, f
            assert "{%" not in text, f


def test_all_yaml_parses(rendered):
    _, out = rendered
    files = [*out.rglob("*.yaml"), *out.rglob("*.yml")]
    assert len(files) >= 6
    for f in files:
        load_yaml_docs(f)


def test_catalog_info_is_valid_component(rendered, validator_for):
    answers, out = rendered
    (doc,) = load_yaml_docs(out / "service/catalog-info.yaml")
    errors = [e.message for e in validator_for("ComponentV1alpha1").iter_errors(doc)]
    assert not errors, errors
    assert doc["metadata"]["name"] == answers["name"]
    assert doc["metadata"]["description"] == answers["description"]  # quoting survived
    assert doc["spec"]["owner"] == answers["owner"]
    assert doc["spec"].get("system") == (answers["system"] or None)


def test_codeowners_points_at_github_team(rendered):
    answers, out = rendered
    team = answers["owner"].split("/")[-1]
    assert (out / "service/.github/CODEOWNERS").read_text().strip() == f"* @vince-sre/{team}"


def test_workflow_keeps_github_expressions_and_calls_reusables(rendered):
    answers, out = rendered
    wf = yaml.safe_load((out / "service/.github/workflows/ci.yml").read_text())
    assert wf["jobs"]["image"]["with"]["image-name"] == answers["image"]
    assert wf["jobs"]["image"]["with"]["push"] == "${{ github.event_name == 'push' }}"
    assert wf["jobs"]["deploy-dev"]["with"]["values-file"] == f"workloads/{answers['name']}/values-dev.yaml"
    assert "vince-sre/cicd-pipeline-templates" in wf["jobs"]["image"]["uses"]


@pytest.mark.skipif(not shutil.which("actionlint"), reason="actionlint not installed")
def test_workflow_passes_actionlint(rendered):
    _, out = rendered
    res = subprocess.run(
        ["actionlint", ".github/workflows/ci.yml"], cwd=out / "service", capture_output=True, text=True, check=False
    )
    assert res.returncode == 0, res.stdout + res.stderr


def test_rendered_service_tests_pass(rendered):
    _, out = rendered
    res = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], cwd=out / "service",
                         capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stdout + res.stderr


@pytest.mark.skipif(not shutil.which("ruff"), reason="ruff not installed")
def test_rendered_service_is_ruff_clean(rendered):
    _, out = rendered
    res = subprocess.run(["ruff", "check", "."], cwd=out / "service", capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stdout


def test_gitops_applicationset(rendered):
    answers, out = rendered
    (appset,) = load_yaml_docs(out / f"gitops/apps/workloads/{answers['name']}.yaml")
    tmpl = appset["spec"]["template"]
    assert tmpl["metadata"]["name"] == f"{answers['name']}-{{{{.env}}}}"  # Go template kept literal
    assert tmpl["spec"]["destination"]["namespace"] == f"team-{answers['name']}-{{{{.env}}}}"
    assert tmpl["spec"]["source"]["helm"]["valueFiles"] == [f"../../workloads/{answers['name']}/values-{{{{.env}}}}.yaml"]
    prod = next(e for e in appset["spec"]["generators"][0]["list"]["elements"] if e["env"] == "prod")
    assert prod["replicas"] == ("3" if answers["tier"] == "tier-1" else "2")


def test_gitops_values_files(rendered):
    answers, out = rendered
    for env in ("dev", "prod"):
        (values,) = load_yaml_docs(out / f"gitops/workloads/{answers['name']}/values-{env}.yaml")
        assert values["image"]["repository"] == answers["image"]
    (prod,) = load_yaml_docs(out / f"gitops/workloads/{answers['name']}/values-prod.yaml")
    assert prod["autoscaling"]["maxReplicas"] == (20 if answers["tier"] == "tier-1" else 10)


def test_techdocs_slo_matches_tier(rendered):
    answers, out = rendered
    expected = {"tier-1": "99.9%", "tier-2": "99.5%", "tier-3": "99%"}[answers["tier"]]
    assert f"| SLO | {expected} availability" in (out / "service/docs/index.md").read_text()
    mk = yaml.safe_load((out / "service/mkdocs.yml").read_text())
    assert mk["plugins"] == ["techdocs-core"]
