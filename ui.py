import bpy

class VIEW3D_PT_HouseBuilder(bpy.types.Panel):
    bl_label = "House Builder"
    bl_idname = "VIEW3D_PT_house_builder"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "HouseGen"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "house_floors", text="Floors")
        layout.prop(scene, "house_style", text="Style")
        layout.prop(scene, "house_details", text="Details")
        layout.prop(scene, "house_seed", text="Seed")

        layout.operator("object.build_house", text="Build House", icon='MOD_BUILD')

def register():
    bpy.utils.register_class(VIEW3D_PT_HouseBuilder)

def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_HouseBuilder)
