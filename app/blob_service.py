from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Retrieve values
connection_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
container_name = os.getenv("AZURE_CONTAINER_NAME")

# Initialize blob service client
if not connection_str:
    raise ValueError("AZURE_STORAGE_CONNECTION_STRING is missing. Check your .env file or environment variables.")

blob_service_client = BlobServiceClient.from_connection_string(connection_str)
container_client = blob_service_client.get_container_client(container_name)

# --- Upload file ---
def upload_file_to_blob(file_path: str, blob_name: str):
    """Uploads a local file to Azure Blob Storage."""
    with open(file_path, "rb") as data:
        container_client.upload_blob(name=blob_name, data=data, overwrite=True)
    return f"✅ Uploaded {blob_name} to Azure Blob Storage"

# --- Download file ---
def download_file_from_blob(blob_name: str, download_path: str):
    """Downloads a blob from Azure Storage."""
    blob_client = container_client.get_blob_client(blob_name)
    with open(download_path, "wb") as file:
        data = blob_client.download_blob()
        file.write(data.readall())
    return f"📥 Downloaded {blob_name} to {download_path}"

# --- Test connection (optional) ---
if __name__ == "__main__":
    print(f"✅ Connected to Azure Storage account: {blob_service_client.account_name}")
