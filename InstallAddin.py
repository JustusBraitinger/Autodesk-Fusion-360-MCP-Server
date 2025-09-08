import os
import shutil

source = os.path.join(os.getcwd(), "MCP")  # Dein Addin-Ordner

dest = os.path.expanduser(
    r"~\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\fusion_addin_mcp"
)

if os.path.exists(dest):
    try:
        shutil.rmtree(dest, ignore_errors=True)
        print("Vorherige Version des Addins entfernt.")
    except PermissionError:
        print("Einige Dateien konnten nicht gelöscht werden. Fusion 360 eventuell schließen und erneut versuchen.")

# Addin kopieren
try:
    shutil.copytree(source, dest)
    print("Add-In installiert!")
except Exception as e:
    print(f"Fehler beim Kopieren des Addins: {e}")

print(f"Addin befindet sich jetzt in: {dest}")

