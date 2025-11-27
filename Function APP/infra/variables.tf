variable "resource_group_name" {
    description = "The name of the Azure Resource Group to create or use for deploying the Function App and related resources."
    type = string
}

variable "location" {
    description = "The Azure region where resources will be deployed (e.g. 'eastus', 'westeurope')"
    type = string
}

variable "environment" {
    description = "The deployment environment (e.g. 'dev', 'prod', 'staging')."
    type = string
}

variable "application" {
    description = "The name of the application for tagging and identification purposes."
    type = string
  
}

variable "app_insights_name" {
    description = "The name of the Application Insights resource to create or use for monitoring."
    type = string
  
}
variable "storage_account_name" {
    description = "The name of the Azure Storage Account to create or use for the Function App (must be globally unique, 3-24 lowercase letters and numbers)."
    type = string
}

variable "app_service_plan_name" {
    description = "The name of the App Service Plan to create or use for the Function App."
    type = string
}

variable "function_app_name" {
    description = "The name of the Azure Function App to create."
    type = string
}

variable "log_analytics_workspace_name" {
    description = "The name of the Log Analytics Workspace to create or use for monitoring."
    type = string
  
}

variable "function_app_application_settings" {
    description = "A map of application settings to configure for the Function App."
    type = map(string)
}

variable "zip_file" {
    description = "The path to the zip file containing the Function App code to deploy."
    type = string
  
}