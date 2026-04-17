# REX - Flow V1 (Blender Utility Toolkit)

A fast Blender utility addon for **FiveM / GTA workflows**: rename tools, UV fixes, vertex colors cleanup, material cleanup, normals tools, merge by distance, and quad/tri conversion.

> DESIGNED WITH INTENT. BUILT TO LAST.

---

## Features

### Rename System
Find & Replace renaming tool that works across multiple Blender datablocks.

Supports renaming:
- Objects
- Mesh datablocks
- Materials
- Armatures
- Bones
- Vertex Groups
- Shape Keys
- Collections
- Images

---

### UV & Vertex Tools

#### Fix UV Maps
- Creates a UV map if missing
- Renames UV layers automatically:
  - `UVMap 0`
  - `UVMap 1`
  - `UVMap 2`

#### Fix Vertex Colors
- Creates vertex color attribute if missing
- Renames vertex colors automatically:
  - `Color 1`
  - `Color 2`
  - `Color 3`
- Option: **Only Selected** (works only on selected meshes)

---

### Cleanup Tools

#### Remove Empty Material Slots
- Removes unused and empty material slots from selected meshes
- Removes unused materials from Blender data (0 users)

---

### Mesh Fix Tools

#### Remove Doubles (Merge by Distance)
- Merge-by-distance tool (Remove Doubles)
- Works only in **Edit Mode**
- Adjustable merge distance slider

#### Add Clean Normals
Automatically adds clean shading modifiers:
- Edge Split Modifier (30° split angle)
- Weighted Normal Modifier (keep sharp enabled)

#### Apply Normals
- Applies Edge Split modifier
- Applies Weighted Normal modifier

---

### Quad / Tri Tools
- Quads → Tris (Triangulate)
- Tris → Quads

---

## Requirements
- Blender **3.0+**
- Recommended Blender **4.0+** for best compatibility

---

## Installation (ZIP)

1. Click **Code**
2. Click **Download ZIP**
3. Open Blender
4. Go to:

   `Edit > Preferences > Add-ons`

5. Click **Install**
6. Select the downloaded `.zip` file (**DO NOT EXTRACT**)
7. Enable the addon

---

## Location

After enabling, find it here:

`View3D > Sidebar (N Panel) > REX FLOW`

---

## Usage Notes

### Remove Doubles
- Select a mesh object
- Enter Edit Mode
- Set distance value
- Click Remove Doubles

### Rename Everything
- Fill **Find** and **Replace**
- Click Apply Rename
- Works case-sensitive

### Vertex Colors
- Enable "Only Selected" if you want to apply only to selected objects
- If disabled, it affects all objects

---

## Tool Version
**V1.0.0**

---

## Support / Contact

If you need any feature or help, please connect with our team on Discord:  
https://discord.gg/qJX72Ghjdn  

Feel free to check the **Discord Product Section** also.

---

## Credits

This addon was built and maintained by **TEAM REXCore.**

- **HYPINIX**
- **NARUTO**
- **DAMN**
- **SHASHI**

---

## License
This project is provided **as-is**.  
You are free to use it for personal and production work.
