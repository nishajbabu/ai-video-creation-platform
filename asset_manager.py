import os
import shutil
import uuid
from typing import List, Dict

class AssetManager:
    """
    Manages user-uploaded media assets (images, videos, audio) for video projects.
    Simulates a cloud storage bucket using isolated local directories.
    """
    
    def __init__(self, base_storage_dir: str = "./project_assets"):
        """
        Initializes the Asset Manager and creates the root storage directory.
        """
        self.base_storage_dir = base_storage_dir
        if not os.path.exists(self.base_storage_dir):
            os.makedirs(self.base_storage_dir)
            print(f"System Storage Initialized at: {self.base_storage_dir}")

    def save_asset(self, project_id: str, source_file_path: str, asset_type: str) -> Dict[str, str]:
        """
        Saves a user's uploaded file into the project's isolated storage folder.
        
        Args:
            project_id (str): The specific video project ID.
            source_file_path (str): The current path of the file being uploaded.
            asset_type (str): The category of the asset (e.g., 'images', 'videos', 'audio').
            
        Returns:
            Dict[str, str]: Metadata about the securely stored asset.
        """
        if not os.path.exists(source_file_path):
            raise FileNotFoundError(f"Cannot find asset to upload: {source_file_path}")
            
        # Create a safe, isolated directory for this specific project and asset type
        project_dir = os.path.join(self.base_storage_dir, project_id, asset_type)
        os.makedirs(project_dir, exist_ok=True)
        
        # Generate a unique secure ID and maintain the original file extension
        asset_id = f"ast_{uuid.uuid4().hex[:8]}"
        file_extension = os.path.splitext(source_file_path)[1]
        safe_filename = f"{asset_id}{file_extension}"
        
        destination_path = os.path.join(project_dir, safe_filename)
        
        # Copy the file to our 'cloud' storage simulation
        shutil.copy2(source_file_path, destination_path)
        
        print(f"Asset successfully uploaded: {asset_id}")
        
        return {
            "asset_id": asset_id,
            "project_id": project_id,
            "type": asset_type,
            "url": destination_path  # In a live API, this would be an HTTP URL
        }

    def list_project_assets(self, project_id: str) -> List[Dict[str, str]]:
        """
        Retrieves all stored assets for a specific project so the Video Editor can use them.
        """
        project_dir = os.path.join(self.base_storage_dir, project_id)
        if not os.path.exists(project_dir):
            return []
            
        assets = []
        # Walk through the directory tree to find all files for this project
        for root, _, files in os.walk(project_dir):
            for file in files:
                asset_type = os.path.basename(root)
                assets.append({
                    "asset_id": os.path.splitext(file)[0],
                    "type": asset_type,
                    "url": os.path.join(root, file)
                })
        return assets

# --- MODULE EXECUTION ---
if __name__ == "__main__":
    test_project_id = "proj_test_001"
    
    # Let's create a dummy image file to simulate a user upload
    dummy_image = "dummy_logo.jpg"
    with open(dummy_image, "w") as f:
        f.write("fake image data")

    try:
        print("Initializing Asset Manager...")
        asset_db = AssetManager()
        
        print("\nSimulating user uploading a company logo...")
        uploaded_asset = asset_db.save_asset(
            project_id=test_project_id, 
            source_file_path=dummy_image, 
            asset_type="images"
        )
        
        print("\nRetrieving all assets for the Video Editor timeline...")
        all_assets = asset_db.list_project_assets(project_id=test_project_id)
        
        for asset in all_assets:
            print(f"- Found {asset['type']}: {asset['url']}")
            
    except Exception as e:
        print(f"Error during execution: {e}")