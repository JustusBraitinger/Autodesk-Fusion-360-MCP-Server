import os
import shutil


"""
Kopiert den Ordner "fusion_addin" in den AddIns-Ordner von Fusion 360.
"""
source = os.path.join(os.getcwd(), "MCP") # Pfad zum Ordner "fusion_addin" im aktuellen Verzeichnis
dest = os.path.expanduser(r"~\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns")


shutil.copytree(source, dest)
print("Add-In installiert")