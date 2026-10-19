"""Static checks on every template.yaml and on the catalog entities."""

import re

import pytest
from conftest import ROOT, SCHEMA_FOR_KIND, TEMPLATES, load_yaml_docs

# Backstage's own entity-name rule (enforced in code, not in the JSON schema).
NAME_RE = re.compile(r"^[a-zA-Z0-9]+([-_.][a-zA-Z0-9]+)*$")
PARAM_REF = re.compile(r"parameters\.([A-Za-z_]\w*)")
VALUE_REF = re.compile(r"values\.([A-Za-z_]\w*)")

CATALOG_FILES = sorted((ROOT / "catalog").glob("*.yaml"))


def template_ids():
    return [t.parent.name for t in TEMPLATES]


def declared_parameters(template):
    names = set()
    for page in template["spec"]["parameters"]:
        names.update(page.get("properties", {}))
    return names


def test_templates_exist():
    assert {t.parent.name for t in TEMPLATES} == {"python-service", "terraform-module"}


@pytest.mark.parametrize("path", TEMPLATES, ids=template_ids())
def test_template_matches_backstage_schema(path, validator_for):
    (doc,) = load_yaml_docs(path)
    errors = [f"{list(e.path)}: {e.message}" for e in validator_for("TemplateV1beta3").iter_errors(doc)]
    assert not errors, errors
    assert NAME_RE.match(doc["metadata"]["name"]) and len(doc["metadata"]["name"]) <= 63


@pytest.mark.parametrize("path", TEMPLATES, ids=template_ids())
def test_every_parameter_reference_is_declared(path):
    (doc,) = load_yaml_docs(path)
    used = set(PARAM_REF.findall(path.read_text(encoding="utf-8")))
    missing = used - declared_parameters(doc)
    assert not missing, f"steps reference undeclared parameters: {sorted(missing)}"


@pytest.mark.parametrize("path", TEMPLATES, ids=template_ids())
def test_required_parameters_exist(path):
    (doc,) = load_yaml_docs(path)
    for page in doc["spec"]["parameters"]:
        for req in page.get("required", []):
            assert req in page["properties"], f"{req} is required but not defined on page {page['title']!r}"


@pytest.mark.parametrize("path", TEMPLATES, ids=template_ids())
def test_skeleton_values_are_supplied(path):
    """Every values.x a skeleton uses must be passed by its fetch:template step."""
    (doc,) = load_yaml_docs(path)
    fetches = [s for s in doc["spec"]["steps"] if s["action"] == "fetch:template"]
    assert fetches
    for step in fetches:
        skeleton = path.parent / step["input"]["url"]
        assert skeleton.is_dir(), f"{step['id']}: {skeleton} not found"
        used = set()
        for f in skeleton.rglob("*"):
            used.update(VALUE_REF.findall(str(f.relative_to(skeleton))))
            if f.is_file():
                used.update(VALUE_REF.findall(f.read_text(encoding="utf-8")))
        supplied = set(step["input"]["values"])
        assert used <= supplied, f"{step['id']}: skeleton uses {sorted(used - supplied)} but step does not pass them"
        assert supplied <= used, f"{step['id']}: passes unused values {sorted(supplied - used)}"


@pytest.mark.parametrize("path", TEMPLATES, ids=template_ids())
def test_step_ids_unique_and_outputs_reference_real_steps(path):
    (doc,) = load_yaml_docs(path)
    ids = [s["id"] for s in doc["spec"]["steps"]]
    assert len(ids) == len(set(ids))
    referenced = set(re.findall(r"steps\['([^']+)'\]", path.read_text(encoding="utf-8")))
    assert referenced <= set(ids), f"unknown step ids: {referenced - set(ids)}"


def test_python_service_name_pattern():
    (doc,) = load_yaml_docs(ROOT / "templates/python-service/template.yaml")
    pattern = re.compile(doc["spec"]["parameters"][0]["properties"]["name"]["pattern"])
    for ok in ["orders", "payments-api", "a1b"]:
        assert pattern.match(ok), ok
    for bad in ["Orders", "-orders", "orders-", "o", "orders_api", "a" * 41]:
        assert not pattern.match(bad), bad


@pytest.mark.parametrize("path", CATALOG_FILES, ids=[p.name for p in CATALOG_FILES])
def test_catalog_entities_match_schema(path, validator_for):
    for doc in load_yaml_docs(path):
        v = validator_for(SCHEMA_FOR_KIND[doc["kind"]])
        errors = [f"{doc['metadata']['name']} {list(e.path)}: {e.message}" for e in v.iter_errors(doc)]
        assert not errors, errors


def test_location_targets_exist():
    (loc,) = load_yaml_docs(ROOT / "catalog/all.yaml")
    for target in loc["spec"]["targets"]:
        assert (ROOT / "catalog" / target).resolve().is_file(), target
