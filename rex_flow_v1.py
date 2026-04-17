bl_info = {
    "name": "REX - FLOW V1",
    "author": "HYPINIX",
    "version": (1, 0, 1),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > REX - FLOW V1",
    "description": "REX - FLOW V1: Utility + FiveM production tools for Blender.",
    "category": "Object",
}

import bpy
import math


class REX_Props(bpy.types.PropertyGroup):
    old_name: bpy.props.StringProperty(name="Find")
    new_name: bpy.props.StringProperty(name="Replace")
    vertex_only_selected: bpy.props.BoolProperty(name="Only Selected", default=True)
    remove_doubles_distance: bpy.props.FloatProperty(
        name="Distance",
        description="Merge distance for Remove Doubles",
        default=0.0001,
        min=0.0,
        soft_max=1.0,
        step=0.001,
        precision=6
    )
class REX_OT_RemoveDoubles(bpy.types.Operator):
    bl_idname = "rex.remove_doubles"
    bl_label = "Remove Doubles"
    bl_description = "Merge by Distance (Remove Doubles) for selected mesh in Edit Mode."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            show_popup("Please select a mesh object.", icon="ERROR")
            return {'CANCELLED'}
        if context.mode != 'EDIT_MESH':
            show_popup("Remove Doubles works only in Edit Mode.", icon="ERROR")
            return {'CANCELLED'}
        dist = context.scene.rex_props.remove_doubles_distance
        mesh = obj.data
        verts_before = len(mesh.vertices)
        removed = 0
        try:
            bpy.ops.mesh.merge_by_distance(distance=dist)
        except Exception:
            try:
                bpy.ops.mesh.remove_doubles(threshold=dist)
            except Exception:
                show_popup("Remove Doubles operation failed.", icon="ERROR")
                return {'CANCELLED'}
        # Force mesh update to get correct vertex count
        bpy.ops.object.mode_set(mode='OBJECT')
        verts_after = len(mesh.vertices)
        bpy.ops.object.mode_set(mode='EDIT')
        removed = verts_before - verts_after
        self.report({'INFO'}, f"Removed {removed} vertice(s)")
        return {'FINISHED'}


class REX_OT_RenameEverything(bpy.types.Operator):
    bl_idname = "rex.rename_everything"
    bl_label = "Rename Everything"
    bl_description = "Find-and-replace text in object names (case-sensitive)."
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = context.scene.rex_props
        old = props.old_name
        new = props.new_name

        if not old or not new:
            self.report({"ERROR"}, "Fill both fields.")
            return {"CANCELLED"}

        counts = {
            'objects': 0,
            'meshes': 0,
            'materials': 0,
            'bones': 0,
            'collections': 0,
            'images': 0,
            'vgroups': 0,
            'shape_keys': 0,
        }

        # Rename object names and per-object data (vertex groups, shape keys)
        for obj in bpy.data.objects:
            if old in obj.name:
                obj.name = obj.name.replace(old, new)
                counts['objects'] += 1

            # vertex groups
            vgroups = getattr(obj, 'vertex_groups', None)
            if vgroups:
                for vg in vgroups:
                    if old in vg.name:
                        vg.name = vg.name.replace(old, new)
                        counts['vgroups'] += 1

            # shape keys
            if hasattr(obj.data, 'shape_keys') and obj.data.shape_keys:
                for kb in obj.data.shape_keys.key_blocks:
                    if old in kb.name:
                        kb.name = kb.name.replace(old, new)
                        counts['shape_keys'] += 1

        # Rename mesh datablocks
        for mesh in bpy.data.meshes:
            if old in mesh.name:
                mesh.name = mesh.name.replace(old, new)
                counts['meshes'] += 1

        # Rename materials
        for mat in bpy.data.materials:
            if mat and old in mat.name:
                mat.name = mat.name.replace(old, new)
                counts['materials'] += 1

        # Rename armature object names and armature datablock names
        for obj in bpy.data.objects:
            if obj.type == 'ARMATURE' and old in obj.name:
                obj.name = obj.name.replace(old, new)
                counts['objects'] += 1
            # Armature datablock name
            if obj.type == 'ARMATURE' and old in obj.data.name:
                obj.data.name = obj.data.name.replace(old, new)
                counts['meshes'] += 1  # Count as mesh/datablock rename

        # Rename bones in armatures and armature objects safely
        for obj in bpy.data.objects:
            if obj.type != 'ARMATURE':
                continue

            arm = obj.data
            # collect bone renames first to avoid lookup issues while renaming
            renames = []
            for b in arm.bones:
                if old in b.name:
                    renames.append((b.name, b.name.replace(old, new)))

            for old_bname, new_bname in renames:
                try:
                    arm.bones[old_bname].name = new_bname
                    counts['bones'] += 1
                except Exception:
                    continue

                # also rename pose bone if present
                if obj.pose and old_bname in obj.pose.bones:
                    try:
                        obj.pose.bones[old_bname].name = new_bname
                        counts['bones'] += 1
                    except Exception:
                        pass

        # Collections
        for col in bpy.data.collections:
            if old in col.name:
                col.name = col.name.replace(old, new)
                counts['collections'] += 1

        # Images
        for img in bpy.data.images:
            if old in img.name:
                img.name = img.name.replace(old, new)
                counts['images'] += 1

        self.report({"INFO"}, (
            f"Renamed objects:{counts['objects']} meshes:{counts['meshes']} mats:{counts['materials']} "
            f"bones:{counts['bones']} vgroups:{counts['vgroups']} shape_keys:{counts['shape_keys']}"
        ))
        return {"FINISHED"}


class REX_OT_RemoveEmptyMaterialSlots(bpy.types.Operator):
    bl_idname = "rex.remove_empty_slots"
    bl_label = "Remove Empty Materials & Slots"
    bl_description = "Remove materials & slots that are empty from mesh objects."
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        removed_slots = 0
        removed_mats = 0
        selected = [obj for obj in context.selected_objects if obj.type == 'MESH']
        for obj in selected:
            mesh = obj.data
            slots = obj.material_slots
            used_slots = set()
            if hasattr(mesh, "polygons"):
                for poly in mesh.polygons:
                    if poly.material_index < len(slots):
                        used_slots.add(poly.material_index)
            # Remove slots that are empty or unused
            for idx in reversed(range(len(slots))):
                if slots[idx].material is None or idx not in used_slots:
                    obj.active_material_index = idx
                    mesh.materials.pop(index=idx)
                    removed_slots += 1

        # Remove unused materials from bpy.data.materials
        used_mats = set()
        for obj in bpy.data.objects:
            if hasattr(obj.data, "materials"):
                for mat in obj.data.materials:
                    if mat:
                        used_mats.add(mat)
        unused_mats = [mat for mat in bpy.data.materials if mat.users == 0 and mat not in used_mats]
        for mat in unused_mats:
            bpy.data.materials.remove(mat)
            removed_mats += 1

        self.report({"INFO"}, f"Removed {removed_slots} unused slot(s) and {removed_mats} unused material(s).")
        return {"FINISHED"}


class REX_OT_FixUVMaps(bpy.types.Operator):
    bl_idname = "rex.fix_uv_maps"
    bl_label = "Fix UV Maps"
    bl_description = "Ensure selected meshes have at least one UV map and standardize names."
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

            mesh = obj.data

            if not mesh.uv_layers:
                mesh.uv_layers.new(name="UVMap 0")

            for i, uv in enumerate(mesh.uv_layers):
                uv.name = f"UVMap {i}"

        return {"FINISHED"}


class REX_OT_FixVertexColors(bpy.types.Operator):
    bl_idname = "rex.fix_vertex_colors"
    bl_label = "Fix Vertex Colors"
    bl_description = "Add or rename vertex color attributes; can operate on selection only."
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = context.scene.rex_props
        targets = context.selected_objects if props.vertex_only_selected else bpy.data.objects

        created = 0
        renamed = 0

        for obj in targets:
            if obj.type != 'MESH':
                continue

            mesh = obj.data

            # New attribute API (Blender 3.3+)
            if hasattr(mesh, "color_attributes"):
                attrs = mesh.color_attributes
                if not attrs:
                    # try create BYTE_COLOR then fallback to FLOAT_COLOR
                    try:
                        attrs.new(name="Color 1", type='BYTE_COLOR', domain='CORNER')
                    except Exception:
                        attrs.new(name="Color 1", type='FLOAT_COLOR', domain='CORNER')
                    created += 1

                for i, attr in enumerate(attrs):
                    new_name = f"Color {i+1}"
                    if attr.name != new_name:
                        attr.name = new_name
                        renamed += 1

            # Legacy vertex colors API
            elif hasattr(mesh, "vertex_colors"):
                vcols = mesh.vertex_colors
                if not vcols:
                    vcols.new(name="Color 1")
                    created += 1

                for i, vcol in enumerate(vcols):
                    new_name = f"Color {i+1}"
                    if vcol.name != new_name:
                        vcol.name = new_name
                        renamed += 1

            else:
                # No vertex color support on this mesh
                continue

        self.report({"INFO"}, f"Vertex colors created: {created}, renamed: {renamed}")
        return {"FINISHED"}


class REX_OT_AddCleanNormals(bpy.types.Operator):
    bl_idname = "rex.add_clean_normals"
    bl_label = "Add Clean Normals"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

            for mod in list(obj.modifiers):
                if mod.type in {'EDGE_SPLIT', 'WEIGHTED_NORMAL'}:
                    obj.modifiers.remove(mod)

            edge = obj.modifiers.new(name="Edge Split", type='EDGE_SPLIT')
            edge.use_edge_angle = True
            edge.split_angle = math.radians(30)

            wn = obj.modifiers.new(name="Weighted Normal", type='WEIGHTED_NORMAL')
            wn.keep_sharp = True
            wn.weight = 50
            wn.mode = 'FACE_AREA'

        return {"FINISHED"}


class REX_OT_ApplyNormals(bpy.types.Operator):
    bl_idname = "rex.apply_normals"
    bl_label = "Apply Normals"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

            # Apply Edge Split first
            for mod in obj.modifiers:
                if mod.type == 'EDGE_SPLIT':
                    bpy.context.view_layer.objects.active = obj
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                    break

            # Apply Weighted Normal after
            for mod in obj.modifiers:
                if mod.type == 'WEIGHTED_NORMAL':
                    bpy.context.view_layer.objects.active = obj
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                    break

        return {"FINISHED"}




def show_popup(message="", title="REX Tools", icon='INFO'):
    def draw(self, context):
        self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)

class REX_OT_QuadsToTris(bpy.types.Operator):
    bl_idname = "rex.quads_to_tris"
    bl_label = "Quads → Triangulate"
    bl_description = "Convert quads to triangles (Edit Mode only)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            show_popup("Please select a mesh object.", icon="ERROR")
            return {'CANCELLED'}
        if context.mode != 'EDIT_MESH':
            show_popup("This feature works only in Edit Mode.", icon="ERROR")
            return {'CANCELLED'}
        bpy.ops.mesh.quads_convert_to_tris()
        return {'FINISHED'}

class REX_OT_TrisToQuads(bpy.types.Operator):
    bl_idname = "rex.tris_to_quads"
    bl_label = "Triangulate → Quads"
    bl_description = "Convert triangles to quads (Edit Mode only)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            show_popup("Please select a mesh object.", icon="ERROR")
            return {'CANCELLED'}
        if context.mode != 'EDIT_MESH':
            show_popup("This feature works only in Edit Mode.", icon="ERROR")
            return {'CANCELLED'}
        bpy.ops.mesh.tris_convert_to_quads()
        return {'FINISHED'}


class REX_PT_Main(bpy.types.Panel):
    bl_label = "REX - FLOW V1"
    bl_idname = "REX_PT_MAIN"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "REX FLOW"

    def draw(self, context):
        layout = self.layout
        props = context.scene.rex_props


        layout.label(text="DESIGNED WITH INTENT. BUILT TO LAST.")
        layout.separator()

        # Rename
        box = layout.box()
        box.label(text="Rename", icon='FONT_DATA')
        box.prop(props, "old_name", text="Find")
        box.prop(props, "new_name", text="Replace")
        box.operator("rex.rename_everything", text="Apply Rename", icon='FILE_TICK')

        # UV & Vertex
        box = layout.box()
        box.label(text="UV & Vertex", icon='GROUP_UVS')
        row = box.row(align=True)
        row.operator("rex.fix_uv_maps", text="Fix UV Maps", icon='GROUP_UVS')
        row.operator("rex.fix_vertex_colors", text="Fix Vertex Colors", icon='COLOR')
        box.prop(props, "vertex_only_selected")

        # Cleanup
        box = layout.box()
        box.label(text="Cleanup", icon='TRASH')
        box.operator("rex.remove_empty_slots", text="Remove Empty Material Slots", icon='MATERIAL')

        # Normals
        box = layout.box()
        box.label(text="Fix Mesh", icon='MOD_NORMALEDIT')
        # Remove Doubles inside Normals panel
        box.prop(props, "remove_doubles_distance", text="Distance")
        box.operator("rex.remove_doubles", text="Remove Doubles", icon='AUTOMERGE_ON')
        row = box.row(align=True)
        row.operator("rex.add_clean_normals", text="Add Clean Normals", icon='MOD_NORMALEDIT')
        row.operator("rex.apply_normals", text="Apply Normals", icon='CHECKMARK')

        # Quad/Tris Tools
        box = layout.box()
        box.label(text="Quad/Tris Tools", icon='MESH_GRID')
        row = box.row(align=True)
        row.operator("rex.quads_to_tris", text="Quads → Tris", icon='MESH_GRID')
        row.operator("rex.tris_to_quads", text="Tris → Quads", icon='MESH_GRID')
        # box.operator("rex.quad_block", text="QUAD BLOCK", icon='MOD_TRIANGULATE')


classes = (
    REX_Props,
    REX_OT_RenameEverything,
    REX_OT_FixUVMaps,
    REX_OT_FixVertexColors,
    REX_OT_RemoveEmptyMaterialSlots,
    REX_OT_AddCleanNormals,
    REX_OT_ApplyNormals,
    REX_OT_QuadsToTris,
    REX_OT_TrisToQuads,
    REX_OT_RemoveDoubles,
    # REX_OT_QuadBlock,
    REX_PT_Main,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.rex_props = bpy.props.PointerProperty(type=REX_Props)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.rex_props

if __name__ == "__main__":
    register()
