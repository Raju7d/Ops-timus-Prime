resource_group_name = "rg-test"
location = "eastus2"
application = "ITrms-ops"
environment = "dev"

storage_account_name = "teststorage-123"
app_service_plan_name = "appserviceplantest"
log_analytics_workspace_name = "loganalyticstest"
app_indights_name = "appinsightstest"
function_app_name = "testazurelinuxfunctionapp"
function_app_application_settings = {
  "FUNCTIONS_WORKER_RUNTIME" = "python"
  "WEBSITE_RUN_FROM_PACKAGE" = "1"
}
zip_file = "../function_app_code/function_app_package.zip"