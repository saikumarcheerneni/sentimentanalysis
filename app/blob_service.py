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


# -------------------------------------------------------------------
# --- EXISTING FUNCTIONS (YOUR CODE, UNTOUCHED)
# -------------------------------------------------------------------

def upload_file_to_blob(file_path: str, blob_name: str):
    """Uploads a local file to Azure Blob Storage."""
    with open(file_path, "rb") as data:
        container_client.upload_blob(name=blob_name, data=data, overwrite=True)
    return f"✅ Uploaded {blob_name} to Azure Blob Storage"


def download_file_from_blob(blob_name: str, download_path: str):
    """Downloads a blob from Azure Storage."""
    blob_client = container_client.get_blob_client(blob_name)
    with open(download_path, "wb") as file:
        data = blob_client.download_blob()
        file.write(data.readall())
    return f"📥 Downloaded {blob_name} to {download_path}"


# -------------------------------------------------------------------
# --- NEW FUNCTIONS (NEEDED FOR API)
# -------------------------------------------------------------------

def upload_bytes(data: bytes, blob_name: str):
    """Uploads raw bytes sent from FastAPI (UploadFile)"""
    container_client.upload_blob(name=blob_name, data=data, overwrite=True)
    return blob_name


def delete_blob(blob_name: str):
    """Delete a blob from Azure Storage."""
    blob_client = container_client.get_blob_client(blob_name)
    blob_client.delete_blob()
    return True


def download_bytes(blob_name: str) -> bytes:
    """Return blob content as bytes (for API download endpoint)."""
    blob_client = container_client.get_blob_client(blob_name)
    stream = blob_client.download_blob()
    return stream.readall()


def list_user_blobs(prefix: str):
    """
    List blobs under a folder. Example:
    prefix = 'saikumar/uploads/'
    """
    return [blob.name for blob in container_client.list_blobs(name_starts_with=prefix)]


# -------------------------------------------------------------------
# --- Optional connection test
# -------------------------------------------------------------------

if __name__ == "__main__":
    print(f"✅ Connected to Azure Storage account: {blob_service_client.account_name}")
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta

def generate_report_sas(blob_name: str, expiry_minutes: int = 60):
    sas = generate_blob_sas(
        account_name=blob_service_client.account_name,
        container_name=container_name,
        blob_name=blob_name,
        account_key=blob_service_client.credential.account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(minutes=expiry_minutes)
    )
    return f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas}"
