import os 
import shutil 
import platform

userdir = os.path.expanduser('~')
# Cross-platform path handling
if platform.system() == "Windows":
    addin_path = os.path.join(userdir, "AppData", "Roaming", "Autodesk", "Autodesk Fusion 360", "API", "AddIns")
else:  # macOS
    addin_path = os.path.join(userdir, "Library", "Application Support", "Autodesk", "Autodesk Fusion 360", "API", "AddIns")

# Use current directory instead of hardcoded path
current_dir = os.path.dirname(os.path.abspath(__file__))
source_folder = os.path.join(current_dir, "FusionMCPBridge")

print(f"Getting the folder from {source_folder}")
print(f"Installing the add-in to {addin_path}")

name = os.path.basename(source_folder)
destination_folder = os.path.join(addin_path, name)

os.makedirs(destination_folder, exist_ok=True)
shutil.copytree(source_folder, destination_folder, dirs_exist_ok=True)

exist = os.path.exists(destination_folder)
if not exist:
    raise Exception(f"Add-in installation failed.\n Please look into the README for manual installation instructions.\n Current directory: {current_dir}")
else:
    print("Add-in installed successfully.")
    print(f"Installed to: {destination_folder}")
