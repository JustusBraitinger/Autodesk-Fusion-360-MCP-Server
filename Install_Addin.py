import os 
import shutil 
import time

userdir = os.path.expanduser('~')
addin_path = os.path.join(userdir, "AppData", "Roaming", "Autodesk", "Autodesk Fusion 360", "API", "AddIns")
source_folder = os.path.join(userdir, "FusionMCP", "MCP")

print(f"Getting the folder from {source_folder}")
print(f"Installing the add-in to {addin_path}")

name = os.path.basename(source_folder)
destination_folder = os.path.join(addin_path, name)

os.makedirs(destination_folder, exist_ok=True)
shutil.copytree(source_folder, destination_folder, dirs_exist_ok=True)

exist = os.path.exists(destination_folder)
if not exist:
    raise Exception(f"Add-in installation failed.\n Please look into the README for manual installation instructions.\n It is important, that you have the repo in the userdir {userdir}\\FusionMCP")
else:
    print("Add-in installed successfully.")
    shutil.rmtree(source_folder)
    time.sleep(2)
    if not os.path.exists(source_folder):
        print("Successfully removed source folder.")
    else:
        print("Warning: Source folder may not have been fully removed.")
