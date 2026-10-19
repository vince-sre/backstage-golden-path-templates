locals {
  name_prefix = "${var.name}-${var.environment}"

  standard_tags = {
    "app"         = var.name
    "environment" = var.environment
    "owner"       = var.owner
    "cost-center" = var.cost_center
    "managed-by"  = "terraform"
    "module"      = "terraform-${{ values.provider }}-${{ values.name }}"
  }

  # Standard keys are applied last so callers can't override ownership or cost data.
  tags = merge(var.extra_tags, local.standard_tags)
{%- if values.provider == 'google' %}

  # GCP labels: lowercase, max 63 chars, only [a-z0-9_-].
  labels = { for k, v in local.tags : replace(lower(k), "/[^a-z0-9_-]/", "_") => substr(replace(lower(v), "/[^a-z0-9_-]/", "_"), 0, 63) }
{%- endif %}
}
