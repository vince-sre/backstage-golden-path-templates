terraform {
  required_version = ">= 1.6"

  required_providers {
{%- if values.provider == 'aws' %}
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.70"
    }
{%- elif values.provider == 'google' %}
    google = {
      source  = "hashicorp/google"
      version = "~> 6.6"
    }
{%- else %}
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.5"
    }
{%- endif %}
  }
}
