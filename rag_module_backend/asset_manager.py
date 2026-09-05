import os
import shutil
import uuid
from typing import List, Dict

class AssetManager:
    """
    Provides isolated, local filesystem operations to mock cloud bucket storage 
    for multimedia assets (images, audio, video).
    """
    
    def __init__(self, base_storage_dir: str = "./project_assets"):
        """
        Establishes the root directory architecture for the local storage instance.
        """
        self.base_storage_dir = base_storage_dir
        if not os.path.exists(self.base_storage_dir):
            os.makedirs(self.base_storage_dir)

    def save_asset(self, project_id: str, source_file_path: str, asset_type: str) -> Dict[str, str]:
        """
        Ingests a temporary upload and persists it within a project-isolated directory 
        using a secure UUID filename.
        
        Args:
            project_id (str): The isolated workspace identifier.
            source_file_path (str): The temporary system path of the uploaded file.
            asset_type (str): The organizational category ('images', 'videos', 'audio').
            
        Returns:
            Dict[str, str]: A structured payload containing the asset's access URL and metadata.
            
        Raises:
            FileNotFoundError: If the temporary upload path is invalid.
        """
        if not os.path.exists(source_file_path):
            raise FileNotFoundError(f"Upload stream missing at: {source_file_path}")
            
        project_directory = os.path.join(self.base_storage_dir, project_id, asset_type)
        os.makedirs(project_directory, exist_ok=True)
        
        secure_asset_id = f"ast_{uuid.uuid4().hex[:8]}"
        original_extension = os.path.splitext(source_file_path)[1]
        secure_filename = f"{secure_asset_id}{original_extension}"
        
        final_destination = os.path.join(project_directory, secure_filename)
        shutil.copy2(source_file_path, final_destination)
        
        return {
            "asset_id": secure_asset_id,
            "project_id": project_id,
            "type": asset_type,
            "url": final_destination 
        }

    def list_project_assets(self, project_id: str) -> List[Dict[str, str]]:
        """
        Traverses the isolated project directory tree to construct a comprehensive 
        catalog of available media assets.
        
        Args:
            project_id (str): The workspace identifier to scan.
            
        Returns:
            List[Dict[str, str]]: An array of asset metadata dictionaries.
        """
        project_directory = os.path.join(self.base_storage_dir, project_id)
        if not os.path.exists(project_directory):
            return []
            
        asset_catalog = []
        
        for root_path, _, directory_files in os.walk(project_directory):
            for file_name in directory_files:
                category_type = os.path.basename(root_path)
                asset_catalog.append({
                    "asset_id": os.path.splitext(file_name)[0],
                    "type": category_type,
                    "url": os.path.join(root_path, file_name)
                })
                
        return asset_catalog