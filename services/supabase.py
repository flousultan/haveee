from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_BUCKET_NAME
import uuid
import os
from datetime import datetime

class SupabaseService:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Remove automatic bucket creation as it requires admin privileges

    def upload_file(self, file_path: str) -> tuple[str, str]:
        """
        Upload a file to Supabase storage
        Returns: (file_id, file_url)
        """
        try:
            # Generate a unique ID for the file
            file_id = str(uuid.uuid4())
            file_name = os.path.basename(file_path)
            
            # Create a unique path in the bucket
            storage_path = f"{datetime.now().strftime('%Y/%m/%d')}/{file_id}/{file_name}"
            
            # Upload the file
            with open(file_path, 'rb') as f:
                self.supabase.storage.from_(SUPABASE_BUCKET_NAME).upload(
                    path=storage_path,
                    file=f,
                    file_options={"content-type": "application/octet-stream"}
                )
            
            # Get the public URL
            file_url = self.supabase.storage.from_(SUPABASE_BUCKET_NAME).get_public_url(storage_path)
            
            return file_id, file_url

        except Exception as e:
            print(f"Error uploading file: {e}")
            raise

    def get_file_url(self, storage_path: str) -> str:
        """Get the public URL for a file"""
        try:
            return self.supabase.storage.from_(SUPABASE_BUCKET_NAME).get_public_url(storage_path)
        except Exception as e:
            print(f"Error getting file URL: {e}")
            raise

# Create a singleton instance
supabase_service = SupabaseService() 