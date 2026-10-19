variable "name" {
  description = "Workload or component name, e.g. \"orders\"."
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,30}$", var.name))
    error_message = "name must be lowercase alphanumeric/hyphens, 2-31 chars."
  }
}

variable "environment" {
  description = "Deployment environment."
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of dev, staging, prod."
  }
}

variable "owner" {
  description = "Owning team (matches the Backstage group name)."
  type        = string
}

variable "cost_center" {
  description = "Cost allocation code for FinOps reporting."
  type        = string
  default     = "unassigned"
}

variable "extra_tags" {
  description = "Additional tags merged over the standard set (standard keys win)."
  type        = map(string)
  default     = {}
}
