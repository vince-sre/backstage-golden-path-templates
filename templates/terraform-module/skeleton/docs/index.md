# terraform-${{ values.provider }}-${{ values.name }}

${{ values.description }}

## Usage

```hcl
module "${{ values.name | replace('-', '_') }}" {
  source = "git::https://github.com/${{ values.repoSlug }}.git?ref=v0.1.0"

  name        = "orders"
  environment = "prod"
  owner       = "team-orders"
}
```

## Conventions
- Provider versions are pinned with `~>`; bump them in a dedicated PR.
- Every resource gets `local.tags`{% if values.provider == 'google' %} (as `local.labels`){% endif %}. The standard keys can't be overridden.
- Release with semver tags; consumers pin `?ref=vX.Y.Z`.
