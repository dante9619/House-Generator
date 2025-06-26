bl_info = {
    "name": "House Generator",
    "blender": (2, 2, 8),
    "author" : "Pazuhina V.V.",
    "category": "Object",
}

import bpy
from . import generator, ui, object_helpers, asset_loader

def register():
    register_properties()
    asset_loader.register()
    generator.register()
    ui.register()
    object_helpers.register()


def unregister():
    unregister_properties()
    asset_loader.unregister()
    ui.unregister()
    generator.unregister()
    object_helpers.unregister()


def update_house_style(self, context):
    max_floors_per_style = {
        "Khrushchev": 9,
        "Brezhnev": 15,
        "Japanese": 5,
        "Stalinist": 12,
        "test": 5
    }

    scene = context.scene
    scene_props = scene.bl_rna.properties
    if 'house_floors' in scene_props:
        scene_props['house_floors'].hard_max = max_floors_per_style[self.house_style]
    
    if scene.house_floors > max_floors_per_style[self.house_style]:
        scene.house_floors = max_floors_per_style[self.house_style]


def register_properties():
    bpy.types.Scene.house_floors = bpy.props.IntProperty(
        name="Height (floors)",
        default=1,
        min=1,
        max=5
    )
    bpy.types.Scene.house_style = bpy.props.EnumProperty(
        name="Style",
        items=[
            ("Khrushchev", "Khrushchev", ""),
            ("Brezhnev", "Brezhnev", ""),
            ("Japanese", "Japanese", ""),
            ("Stalinist", "Stalinist", ""),
            ("test", "test", "")
        ], default = "test",
        update=update_house_style
    )
    bpy.types.Scene.house_details = bpy.props.EnumProperty(
        name="Details",
        items=[
            ("Low", "Low", ""),
            ("Medium", "Medium", ""),
            ("High", "High", ""),
        ], default = "Low"
    )
    bpy.types.Scene.house_seed = bpy.props.IntProperty(name="Seed", default=101, min=1, max=999999999)

def unregister_properties():
    del bpy.types.Scene.house_floors
    del bpy.types.Scene.house_style
    del bpy.types.Scene.house_details
    del bpy.types.Scene.house_seed