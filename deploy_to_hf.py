import os
import sys
from huggingface_hub import HfApi

def deploy():
    if len(sys.argv) < 2:
        print("Usage: python deploy_to_hf.py <HF_TOKEN>")
        sys.exit(1)
        
    token = sys.argv[1]
    full_repo_id = "rkpcode/pradhan-drug-house"
    
    api = HfApi(token=token)
    print("==================================================")
    print(f"Deploying codebase to Space: {full_repo_id}")
    print("==================================================")
        
    print("\n[1/2] Pushing environment secrets to HF Space Settings...")
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
                            print(f"  [+] Added secret: {key}")
                        except Exception as e:
                            print(f"  [-] Warning: Could not add secret {key}: {e}")
    else:
        print("  [-] No .env file found!")
        
    print("\n[2/2] Replacing remote codebase with local project files...")
    ignore_patterns = [".venv/*", "__pycache__/*", "*.pyc", ".git/*", ".env"]
    
    try:
        api.upload_folder(
            folder_path=".",
            repo_id=full_repo_id,
            repo_type="space",
            delete_patterns="*",  # Overwrites/replaces existing remote files completely
            ignore_patterns=ignore_patterns,
            commit_message="Overwriting Space with fresh backend codebase and configuration"
        )
        print("\nSUCCESS: Codebase replaced & secrets updated successfully!")
        print(f"Live Space URL: https://huggingface.co/spaces/{full_repo_id}")
    except Exception as e:
        print(f"\nError uploading files: {e}")

if __name__ == "__main__":
    deploy()
