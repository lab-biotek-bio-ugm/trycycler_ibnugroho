#!/usr/bin/env python3

import argparse
import json
import logging
import os
import io
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

LOG_DIR = Path("logs")
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

def setup_logging(folder_id: str):
    LOG_DIR.mkdir(exist_ok=True, parents=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"download_{folder_id}_{stamp}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s — %(levelname)s — %(message)s",
        handlers=[logging.FileHandler(LOG_DIR / fname), logging.StreamHandler()],
    )

def md5_of(path: Path) -> str:
    md5 = hashlib.md5()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8 << 20), b""):
            md5.update(chunk)
    return md5.hexdigest()

def build_service(token_path: Path, credentials_path: Optional[Path]):
    if token_path.exists():
        creds = Credentials.from_authorized_user_info(json.loads(token_path.read_text()), SCOPES)
    else:
        if credentials_path is None:
            raise FileNotFoundError("Need credentials.json for first login")
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
        creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())

    return build("drive", "v3", credentials=creds)

def list_folder_contents(service, folder_id, corpora, drive_id=None):
    result = []
    page_token = None
    query = f"'{folder_id}' in parents and trashed = false"
    while True:
        response = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, mimeType, md5Checksum, parents)",
            pageSize=1000,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            corpora=corpora,
            driveId=drive_id if corpora == "drive" else None
        ).execute()

        result.extend(response.get("files", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    return result

def download_file(service, file_id, dest_path):
    os.makedirs(dest_path.parent, exist_ok=True)
    request = service.files().get_media(fileId=file_id)
    with open(dest_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

def recursive_download(service, folder_id, base_local_path: Path, corpora, drive_id=None):
    stack = [(folder_id, base_local_path)]
    metadata_log = {}

    while stack:
        current_id, current_local_path = stack.pop()
        children = list_folder_contents(service, current_id, corpora, drive_id)

        for child in children:
            name = child["name"]
            mime_type = child["mimeType"]
            child_id = child["id"]

            if mime_type == "application/vnd.google-apps.folder":
                new_local_path = current_local_path / name
                stack.append((child_id, new_local_path))
            else:
                target_path = current_local_path / name
                md5_remote = child.get("md5Checksum")

                if target_path.exists():
                    md5_local = md5_of(target_path)
                    if md5_local == md5_remote:
                        logging.info(f"✓ Skipping (unchanged): {target_path}")
                        continue

                logging.info(f"↓ Downloading: {target_path}")
                download_file(service, child_id, target_path)
                metadata_log[str(target_path)] = {
                    "id": child_id,
                    "md5Checksum": md5_remote
                }

    meta_dir = Path("metadata")
    meta_dir.mkdir(exist_ok=True, parents=True)
    report_path = meta_dir / f"{base_local_path.name}_downloaded_metadata.json"
    report_path.write_text(json.dumps(metadata_log, indent=4))
    logging.info("Metadata → %s", report_path)

def cli():
    p = argparse.ArgumentParser(description="Download a Drive folder recursively.")
    excl = p.add_mutually_exclusive_group(required=True)
    excl.add_argument("--shared-drive-id", help="Shared Drive ID")
    excl.add_argument("--root-folder-id", help="Regular Drive Folder ID")
    p.add_argument("--token-path", required=True, help="Path to token.json")
    p.add_argument("--credentials-path", help="Path to credentials.json (for first run)")
    p.add_argument("--output-directory", required=True, help="Local directory to save files")
    args = p.parse_args()

    setup_logging(args.root_folder_id or args.shared_drive_id)

    service = build_service(Path(args.token_path), Path(args.credentials_path) if args.credentials_path else None)
    corpora = "drive" if args.shared_drive_id else "allDrives"
    folder_id = args.shared_drive_id or args.root_folder_id

    base_path = Path(args.output_directory).resolve()
    recursive_download(service, folder_id, base_path, corpora, args.shared_drive_id)

if __name__ == "__main__":
    cli()
