import os
import json
import csv
import requests
from urllib.parse import urlparse

JSDELIVR_PREFIX = 'https://purge.jsdelivr.net/gh/AstralSightStudios/AstroBox-Repo@main/'
CDN_TARGETS = ['banner.json', 'devices.json5', 'index.csv']
RESOURCES_DIR = 'resources'

def purge_jsdelivr(file_path):
    url = JSDELIVR_PREFIX + file_path
    print(f"Purging {url}")
    try:
        resp = requests.get(url)
        resp.raise_for_status()
    except Exception as e:
        print(f"Error purging {url}: {e}")

def purge_jsdelivr_custom(file_path, owner, repo):
    url = f"https://purge.jsdelivr.net/gh/{owner}/{repo}@main/{file_path}"
    print(f"Purging {url}")
    try:
        resp = requests.get(url)
        resp.raise_for_status()
    except Exception as e:
        print(f"Error purging {url}: {e}")

def download_and_purge_repo_files(repo_url):
    """
    访问 repo_url，下载 manifest 和其中引用的资源，然后刷新对应 CDN。
    """
    try:
        parsed = urlparse(repo_url)
        parts = parsed.path.strip("/").split("/")
        if len(parts) < 2:
            print(f"Invalid repo URL: {repo_url}")
            return
        owner, repo = parts[:2]
        base_url = f"https://raw.githubusercontent.com/{owner}/{repo}/refs/heads/main/"

        manifest_url = base_url + "manifest.json"
        r = requests.get(manifest_url)
        r.raise_for_status()
        manifest = r.json()

        purge_jsdelivr_custom(f"manifest.json", owner, repo)

        references = []

        item = manifest.get("item")
        for key in ['icon', 'preview']:
            val = item.get(key)
            if isinstance(val, list):
                references.extend(val)
            elif isinstance(val, str):
                references.append(val)

        downloads = manifest.get("downloads", {})
        if isinstance(downloads, dict):
            for device_data in downloads.values():
                if isinstance(device_data, dict):
                    file_name = device_data.get("file_name")
                    if file_name:
                        references.append(file_name)

        for ref in references:
            purge_jsdelivr_custom(ref, owner, repo)

    except Exception as e:
        print(f"Failed to process repo {repo_url}: {e}")

def process_resources():
    for root, _, files in os.walk(RESOURCES_DIR):
        for filename in files:
            if filename.endswith('.json'):
                path = os.path.join(root, filename)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        repo_url = data.get('repo_url')
                        if repo_url:
                            download_and_purge_repo_files(repo_url)
                except Exception as e:
                    print(f"Failed to process {path}: {e}")

def main():
    for f in CDN_TARGETS:
        purge_jsdelivr(f)

    process_resources()

if __name__ == '__main__':
    main()