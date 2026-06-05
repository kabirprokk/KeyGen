"""
GitHub Storage Handler for KeyGen.ai
Saves collected data directly to GitHub repository
"""
import os
import json
import base64
import urllib.request
import urllib.error

class GitHubStorage:
    def __init__(self, token, repo_owner, repo_name, branch="main"):
        self.token = token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.branch = branch
        self.api_base = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    
    def save_file(self, filepath, content, commit_message="Auto-collected data"):
        """Save a file to GitHub repository."""
        url = f"{self.api_base}/contents/{filepath}"
        
        # Check if file exists
        existing_sha = self._get_file_sha(filepath)
        
        data = {
            "message": commit_message,
            "content": base64.b64encode(content.encode()).decode(),
            "branch": self.branch
        }
        
        if existing_sha:
            data["sha"] = existing_sha
        
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode(),
                headers=headers,
                method="PUT"
            )
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read())
                print(f"✓ Saved to GitHub: {filepath}")
                return result
        except Exception as e:
            print(f"✗ GitHub save error: {e}")
            return None
    
    def _get_file_sha(self, filepath):
        """Get SHA of existing file."""
        url = f"{self.api_base}/contents/{filepath}?ref={self.branch}"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read())
                return data.get("sha")
        except:
            return None
    
    def load_file(self, filepath):
        """Load a file from GitHub."""
        url = f"{self.api_base}/contents/{filepath}?ref={self.branch}"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read())
                content = base64.b64decode(data["content"]).decode()
                return content
        except:
            return None
