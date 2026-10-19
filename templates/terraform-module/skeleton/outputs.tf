output "name_prefix" {
  description = "Standard resource name prefix (<name>-<environment>)."
  value       = local.name_prefix
}

output "tags" {
  description = "Standard tags to apply to every resource."
  value       = local.tags
}
{%- if values.provider == 'google' %}

output "labels" {
  description = "Tags normalised to GCP label rules."
  value       = local.labels
}
{%- endif %}
