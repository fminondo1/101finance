import os
import subprocess
from config.settings import AZURE_APP_SERVICE

def deploy_to_azure():
    resource_group = AZURE_APP_SERVICE["resource_group"]
    app_name = AZURE_APP_SERVICE["default_domain"].split(".")[0]
    location = AZURE_APP_SERVICE["location"]

    print("Starting deployment to Azure...")

    # Login to Azure
    subprocess.run(["az", "login"], check=True)

    # Create resource group if it doesn't exist
    subprocess.run(
        ["az", "group", "create", "--name", resource_group, "--location", location],
        check=True,
    )

    # Deploy the app
    subprocess.run(
        [
            "az", "webapp", "up",
            "--name", app_name,
            "--resource-group", resource_group,
            "--plan", AZURE_APP_SERVICE["app_service_plan"],
        ],
        check=True,
    )

    print(f"Deployment to Azure App Service '{app_name}' completed successfully.")

if __name__ == "__main__":
    deploy_to_azure()
