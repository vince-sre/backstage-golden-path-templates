#!/usr/bin/env bash
# Download the official Backstage JSON schemas (pinned release) into .schemas/.
set -euo pipefail
BACKSTAGE_VERSION=${BACKSTAGE_VERSION:-v1.55.3}
base="https://raw.githubusercontent.com/backstage/backstage/${BACKSTAGE_VERSION}"
out="$(dirname "$0")/../.schemas"
mkdir -p "$out"
for p in \
  plugins/scaffolder-common/src/Template.v1beta3.schema.json \
  packages/catalog-model/src/schema/Entity.schema.json \
  packages/catalog-model/src/schema/EntityEnvelope.schema.json \
  packages/catalog-model/src/schema/EntityMeta.schema.json \
  packages/catalog-model/src/schema/shared/common.schema.json \
  packages/catalog-model/src/schema/kinds/Component.v1alpha1.schema.json \
  packages/catalog-model/src/schema/kinds/Group.v1alpha1.schema.json \
  packages/catalog-model/src/schema/kinds/System.v1alpha1.schema.json \
  packages/catalog-model/src/schema/kinds/Location.v1alpha1.schema.json \
  packages/catalog-model/src/schema/kinds/Resource.v1alpha1.schema.json; do
  curl -fsSL -o "$out/$(basename "$p")" "$base/$p"
done
echo "fetched $(find "$out" -name '*.json' | wc -l) schemas (Backstage ${BACKSTAGE_VERSION})"
