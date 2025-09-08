import os
import shutil

source = os.path.join(os.getcwd(), "MCP")  # Dein Addin-Ordner

dest = os.path.expanduser(
    r"~\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\MCP"
)

if os.path.exists(dest):
    try:
        shutil.rmtree(dest, ignore_errors=True)
        print("Gleiches Addin entfernt")
    except PermissionError:
        print("Schließe Fusion")

# Addin kopieren
try:
    shutil.copytree(source, dest)
    print("Add-In installiert!")
except Exception as e:
    print(f"Fehler beim Kopieren des Addins: {e}")

print(f"Addin befindet sich jetzt in: {dest}")


