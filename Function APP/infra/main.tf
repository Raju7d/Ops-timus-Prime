terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "3.103.1"
    }
  }
  backend "azurerm" {}
}

provider "azurerm" {
  features {}
}

resource "azurerm_storage_account" "stg_acc" {
  name                     = var.storage_account_name
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  tags = {
    Environment = var.environment
    Application = var.application
    Location    = var.location
  }
}

resource "azurerm_service_plan" "src_plan" {
  name                = var.app_service_plan_name
  resource_group_name = var.resource_group_name
  location            = var.location
  os_type             = "Linux"
  sku_name            = "Y1"
  tags = {
    Environment = var.environment
    Application = var.application
    Location    = var.location
  }
}

resource "azurerm_log_analytics_workspace" "log_analytics" {
  name                = var.log_analytics_workspace_name
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags = {
    Environment = var.environment
    Application = var.application
    Location    = var.location
  }
}

resource "azurerm_application_insights" "app_insights" {
  name                = var.app_insights_name
  location            = var.location
  resource_group_name = var.resource_group_name
  workspace_id        = azurerm_log_analytics_workspace.log_analytics.id
  application_type    = "web"
  tags = {
    Environment = var.environment
    Application = var.application
    Location    = var.location
  }
}

resource "azurerm_linux_function_app" "evgrid_func" {
  name                        = var.function_app_name
  resource_group_name         = var.resource_group_name
  location                    = var.location
  storage_account_name        = azurerm_storage_account.stg_acc.name
  storage_account_access_key  = azurerm_storage_account.stg_acc.primary_access_key
  service_plan_id             = azurerm_service_plan.src_plan.id
  functions_extension_version = "~4"
  https_only                  = true
  zip_deploy_file             = var.zip_file
  app_settings = merge(var.function_app_application_settings, {
    application_insights_connection_string = azurerm_application_insights.app_insights.connection_string
    application_insights_key               = azurerm_application_insights.app_insights.instrumentation_key
    log_analytics_workspace_id             = azurerm_log_analytics_workspace.log_analytics.id
    FUNCTIONS_WORKER_RUNTIME               = "python"
    WEBSITE_RUN_FROM_PACKAGE               = "1"
  })
  site_config {
    always_on                              = true
    application_insights_connection_string = azurerm_application_insights.app_insights.connection_string
    application_insights_key               = azurerm_application_insights.app_insights.instrumentation_key
    minimum_tls_version                    = 1.2
    application_stack {
      python_version = "3.11"
    }
  }
  tags = {
    Environment = var.environment
    Application = var.application
    Location    = var.location
  }
}

# Zip Deployment
resource "null_resource" "zip_deploy" {
  triggers = {
    always_run = timestamp()
  }
  provisioner "local-exec" {
    when        = create
    interpreter = ["pwsh", "-command"]
    command     = <<EOT
      az functionapp deployment source config-zip -g ${var.resource_group_name} `
      -n ${azurerm_linux_function_app.evgrid_func.name} --src "${var.zip_file}" 
      sleep 30    
    EOT
  }
  depends_on = [azurerm_linux_function_app.evgrid_func]
}