terraform {
  required_version = ">= 1.6"
}

module "this" {
  source = "../.."

  name        = "orders"
  environment = "dev"
  owner       = "team-orders"
  extra_tags  = { "data-classification" = "internal" }
}

output "tags" {
  value = module.this.tags
}
