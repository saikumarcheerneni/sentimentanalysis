# from azure.storage.blob import BlobServiceClient
# from dotenv import load_dotenv
# import os

# # Load environment variables from .env file
# load_dotenv()

# # Retrieve values
# connection_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
# container_name = os.getenv("AZURE_CONTAINER_NAME")

# # Initialize blob service client
# if not connection_str:
#     raise ValueError("AZURE_STORAGE_CONNECTION_STRING is missing. Check your .env file or environment variables.")

# blob_service_client = BlobServiceClient.from_connection_string(connection_str)
# container_client = blob_service_client.get_container_client(container_name)

# # --- Upload file ---
# def upload_file_to_blob(file_path: str, blob_name: str):
#     """Uploads a local file to Azure Blob Storage."""
#     with open(file_path, "rb") as data:
#         container_client.upload_blob(name=blob_name, data=data, overwrite=True)
#     return f"✅ Uploaded {blob_name} to Azure Blob Storage"

# # --- Download file ---
# def download_file_from_blob(blob_name: str, download_path: str):
#     """Downloads a blob from Azure Storage."""
#     blob_client = container_client.get_blob_client(blob_name)
#     with open(download_path, "wb") as file:
#         data = blob_client.download_blob()
#         file.write(data.readall())
#     return f"📥 Downloaded {blob_name} to {download_path}"

# # --- Test connection (optional) ---
# if __name__ == "__main__":
#     print(f"✅ Connected to Azure Storage account: {blob_service_client.account_name}")
# app/blob_service.py

from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas
from dotenv import load_dotenv
from datetime import datetime, timedelta
import os

# Load .env (only used locally — Azure uses App Settings)
load_dotenv()

# Get environment variables
AZURE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_CONTAINER = os.getenv("AZURE_CONTAINER_NAME")

if not AZURE_CONNECTION_STRING:
    raise ValueError("❌ AZURE_STORAGE_CONNECTION_STRING is missing")

# Main blob client
blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(AZURE_CONTAINER)

# --------------------------------------------------------------
#   BASIC UPLOAD & DOWNLOAD
# --------------------------------------------------------------
def upload_bytes(data: bytes, blob_name: str):
    """Upload raw bytes to Azure Blob"""
    container_client.upload_blob(name=blob_name, data=data, overwrite=True)
    return blob_name


def download_bytes(blob_name: str) -> bytes:
    """Download blob and return bytes"""
    blob_client = container_client.get_blob_client(blob_name)
    return blob_client.download_blob().readall()


def delete_blob(blob_name: str):
    """Delete a single blob"""
    blob_client = container_client.get_blob_client(blob_name)
    blob_client.delete_blob()
    return True


def list_user_blobs(prefix: str):
    """List blobs inside a folder"""
    return [b.name for b in container_client.list_blobs(name_starts_with=prefix)]


# --------------------------------------------------------------
#   GENERATE SAS LINK
# --------------------------------------------------------------
def generate_report_sas(blob_name: str, expiry_minutes: int = 60):
    sas = generate_blob_sas(
        account_name=blob_service_client.account_name,
        container_name=AZURE_CONTAINER,
        blob_name=blob_name,
        account_key=blob_service_client.credential.account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(minutes=expiry_minutes),
    )

    return (
        f"https://{blob_service_client.account_name}.blob.core.windows.net/"
        f"{AZURE_CONTAINER}/{blob_name}?{sas}"
    )


# --------------------------------------------------------------
#   DELETE USER FOLDER (NEW FUNCTION)
# --------------------------------------------------------------
def delete_user_folder(username: str):
    """
    Deletes all user files from Azure Blob Storage.
    Example paths removed:
        username/uploads/*
        username/results/*
        username/*
    """
    blobs = container_client.list_blobs(name_starts_with=f"{username}/")

    deleted = 0
    for blob in blobs:
        container_client.delete_blob(blob.name)
        deleted += 1

    return {"deleted_files": deleted, "status": "success"}


# --------------------------------------------------------------
# Optional test (local only)
# --------------------------------------------------------------
if __name__ == "__main__":
    print(f"Connected to Azure Storage: {blob_service_client.account_name}")
