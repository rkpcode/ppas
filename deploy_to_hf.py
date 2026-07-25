import os
import sys
from huggingface_hub import HfApi, create_repo

def deploy():
    if len(sys.argv) < 2:
        print("Usage: python deploy_to_hf.py <HF_TOKEN>")
        sys.exit(1)
        
    token = sys.argv[1]
    full_repo_id = "rkpcode/ppas-api"
    
    api = HfApi(token=token)
    print(f"Deploying to: {full_repo_id}")
        
    print("Uploading secrets...")
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, val = line.split("=", 1)
                        val = val.strip('"' + "'")
                        try:
                            api.add_space_secret(repo_id=full_repo_id, key=key, value=val)
                        except Exception as e:
                            print(f"Warning: Failed to add secret {key}: {e}")
                            
    print("Uploading files...")
    ignore_patterns = [".venv/*", "__pycache__/*", "*.pyc", ".git/*", ".env"]
    
    try:
        api.upload_folder(
            folder_path=".",
            repo_id=full_repo_id,
            repo_type="space",
            ignore_patterns=ignore_patterns,
            commit_message="Deploying Backend API"
        )
        print(f"Deployed! URL: https://huggingface.co/spaces/{full_repo_id}")
    except Exception as e:
        print(f"Error uploading files: {e}")

if __name__ == "__main__":
    deploy()
