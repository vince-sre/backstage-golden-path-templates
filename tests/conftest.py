import json
import pathlib
import sys

import pytest
import yaml
from jsonschema import Draft7Validator
from referencing import Registry
from referencing.jsonschema import DRAFT7

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / ".schemas"
TEMPLATES = sorted((ROOT / "templates").glob("*/template.yaml"))

sys.path.insert(0, str(ROOT / "scripts"))


def load_yaml_docs(path):
    with open(path, encoding="utf-8") as fh:
        return [d for d in yaml.safe_load_all(fh) if d]


@pytest.fixture(scope="session")
def registry():
    files = sorted(SCHEMAS.glob("*.json"))
    if not files:
        pytest.fail("Backstage schemas missing: run ./scripts/fetch-schemas.sh first", pytrace=False)
    resources = []
    for f in files:
        doc = json.loads(f.read_text(encoding="utf-8"))
        resources.append((doc["$id"], DRAFT7.create_resource(doc)))
    return Registry().with_resources(resources)


@pytest.fixture(scope="session")
def validator_for(registry):
    def _get(kind_schema_id: str) -> Draft7Validator:
        schema = registry.contents(kind_schema_id)
        return Draft7Validator(schema, registry=registry)

    return _get


SCHEMA_FOR_KIND = {
    "Template": "TemplateV1beta3",
    "Component": "ComponentV1alpha1",
    "Group": "GroupV1alpha1",
    "System": "SystemV1alpha1",
    "Location": "LocationV1alpha1",
    "Resource": "ResourceV1alpha1",
}
