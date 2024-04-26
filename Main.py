import os
import json
import logging
from smb.SMBConnection import SMBConnection

def load_config(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load configuration from {filename}: {e}")
        return {}

def sort_files(nas_ip, nas_share, main_folder, username, password):
    # Connect to the NAS share
    conn = SMBConnection(username, password, "my_name", "remote_name", is_direct_tcp=True)
    try:
        conn.connect(nas_ip, 445)
    except Exception as e:
        logging.error(f"Failed to connect to SMB share: {e}")
        return

    try:
        # Process files and folders in the main folder
        print("Sorting files...")
        process_folder(conn, nas_share, main_folder, main_folder)
    finally:
        print("Finished sorting files.")
        # Disconnect from the NAS share
        conn.close()

def process_folder(conn, nas_share, main_folder, folder_path):
    try:
        # Iterate over files and folders in the folder
        for item in conn.listPath(nas_share, folder_path):
            if item.filename in ('.', '..', '.DS_Store'):
                continue
            item_path = os.path.join(folder_path, item.filename)
            if item.isDirectory:
                if item_path not in (os.path.join(main_folder, "Photos"), os.path.join(main_folder, "Videos"), os.path.join(main_folder, "GIF")):
                    process_folder(conn, nas_share, main_folder, item_path)
                    if item_path != main_folder:
                        print("Need to Delete " + item_path)
                        # DeleteFolder(conn, nas_share, item_path)
                        continue
            else:
                process_file(conn, nas_share, main_folder, item, item_path)
    except Exception as e:
        logging.error(f"Failed to list contents of folder {folder_path}: {e}")

def process_file(conn, nas_share, main_folder, file, item_path):
    print("Processing " + file.filename)
    ext = os.path.splitext(file.filename)[1].lower()

    # Define destination directory based on file extension
    if ext in (".mp4", ".mov", ".avi"):
        dest_dir = "Videos"
    elif ext == ".gif":
        dest_dir = "GIF"
    elif ext in (".jpg", ".jpeg", ".png"):
        dest_dir = "Photos"
    elif ext in (".webp", ".heic"):
        dest_dir = "wirdPhoto"
    else:
        # Skip files with unsupported extensions
        return

    dest_folder_path = os.path.join(main_folder, dest_dir)
    dest_file_path = os.path.join(dest_folder_path, file.filename)

    # Move file to destination directory
    move_file(conn, item_path, dest_folder_path)

def move_file(conn, source_file, target_dir):
    try:
        # Extract file name from the source file path
        file_name = os.path.basename(source_file)

        # Construct the target file path
        target_file = os.path.join(target_dir, file_name)

        existing_files = conn.listPath(nas_share, target_dir)
        existing_file_names = [entry.filename for entry in existing_files]
        if file_name in existing_file_names:
            # If the file exists, generate a new file name by adding a suffix
            base_name, extension = os.path.splitext(file_name)
            count = 1
            while f"{base_name}_{count}{extension}" in existing_file_names:
                count += 1
            target_file = os.path.join(target_dir, f"{base_name}_{count}{extension}")

        # Move the file to the target directory
        conn.rename(nas_share, source_file, target_file)
        print("Moved " + source_file + " to " + target_file)
        return target_file
    except Exception as e:
        print(f"Failed to move file from {source_file} to {target_dir}: {e}")

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    #load config
    config = load_config("config.json")

    # NAS connection details
    nas_ip = config.get("nas_ip")
    nas_share = config.get("nas_share")
    main_folder = config.get("main_folder")
    username = config.get("username")
    password = config.get("password")

    # Sort files
    sort_files(nas_ip, nas_share, main_folder, username, password)
