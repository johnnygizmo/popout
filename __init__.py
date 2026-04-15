# pyright: reportMissingImports=false

import bpy
from bpy.props import BoolProperty, PointerProperty
from bpy.types import Operator, Panel, PropertyGroup


bl_info = {
    "name": "Popout Window",
    "author": "Johnny Matthews",
    "description": "Duplicate the active area into a new window",
    "blender": (5, 1, 0),
    "version": (1, 0, 0),
    "location": "View3D > Sidebar > Popout",
    "warning": "",
    "category": "Interface",
}


class POPOUT_PG_settings(PropertyGroup):
    open_without_tool_header: BoolProperty(
        name="Hide Tool Header",
        description="Hide the tool header in the duplicated area",
        default=True,
    )#type: ignore

    open_without_header: BoolProperty(
        name="Hide Header",
        description="Hide the header in the duplicated area",
        default=True,
    )#type: ignore
    open_without_overlays: BoolProperty(
        name="Hide Overlays",
        description="Hide overlays in the duplicated area",
        default=True,
    )#type: ignore
    open_without_gizmo: BoolProperty(
        name="Hide Gizmo",
        description="Hide the gizmo in the duplicated area",
        default=True,
    )#type: ignore

    open_unselectable_objects: BoolProperty(
        name="Make Objects Unselectable",
        description="Make all objects unselectable in the duplicated area",
        default=True,
    ) #type: ignore

def _apply_settings_to_space(space, settings, source_camera=None):
    if settings.open_without_tool_header and hasattr(space, "show_region_tool_header"):
        space.show_region_tool_header = False

    if settings.open_without_header and hasattr(space, "show_region_header"):
        space.show_region_header = False

    if settings.open_without_overlays:
        overlay = getattr(space, "overlay", None)
        if overlay is not None and hasattr(overlay, "show_overlays"):
            overlay.show_overlays = False

    if settings.open_without_gizmo and hasattr(space, "show_gizmo"):
        space.show_gizmo = False

    if source_camera is not None and getattr(space, "type", None) == "VIEW_3D":
        space.show_region_ui    = False
        space.show_region_toolbar = False

        if hasattr(space, "use_local_camera"):
            space.use_local_camera = True
        if hasattr(space, "camera"):
            space.camera = source_camera
        region_3d = getattr(space, "region_3d", None)
        if region_3d is not None and hasattr(region_3d, "view_perspective"):
            region_3d.view_perspective = "CAMERA"

        # Set shading type to Material Preview
        if hasattr(space, "shading") and hasattr(space.shading, "type"):
            space.shading.type = 'MATERIAL'
            space.shading.use_scene_lights = False
            space.shading.use_scene_world = False
            space.shading.use_compositor = 'DISABLED'
            space.shading.render_pass = 'COMBINED'

        if settings.open_unselectable_objects:
                space.show_object_select_mesh = False
                space.show_object_select_curve = False
                space.show_object_select_surf = False
                space.show_object_select_meta = False            
                space.show_object_select_font = False
                space.show_object_select_curves = False
                space.show_object_select_pointcloud= False
                space.show_object_select_volume = False            
                space.show_object_select_grease_pencil = False            
                space.show_object_select_armature = False            
                space.show_object_select_lattice = False
                space.show_object_select_empty = False
                space.show_object_select_light = False
                space.show_object_select_light_probe = False
                space.show_object_select_camera = False            
                space.show_object_select_speaker = False
            


def _find_and_configure_new_window(existing_window_ids, source_area_type, settings, source_camera):
    for window in bpy.context.window_manager.windows:
        if window.as_pointer() in existing_window_ids:
            continue

        screen = window.screen
        if screen is None:
            continue

        target_area = None
        for area in screen.areas:
            if area.type == source_area_type:
                target_area = area
                break

        if target_area is None and screen.areas:
            target_area = screen.areas[0]

        if target_area is None:
            continue

        space = target_area.spaces.active
        if space is None:
            continue

        _apply_settings_to_space(space, settings, source_camera=source_camera)

        if source_camera is not None and target_area.type == "VIEW_3D":
            region = next(
                (r for r in target_area.regions if r.type == "WINDOW"), None
            )
            if region is not None:
                with bpy.context.temp_override(
                    window=window,
                    screen=screen,
                    area=target_area,
                    region=region,
                    space_data=space,
                ):
                    bpy.ops.view3d.zoom_camera_1_to_1()
                    region_3d = getattr(space, "region_3d", None)
                    if region_3d is not None and hasattr(region_3d, "lock_rotation"):
                        region_3d.lock_rotation = True

        return None

    return 0.05


class POPOUT_OT_open_window(Operator):
    bl_idname = "popout.open_window"
    bl_label = "Pop Out Current Area"
    bl_description = "Open the current area in a new Blender window"
    bl_options = {"REGISTER"}

    open_without_tool_header: BoolProperty(
        name="Hide Tool Header",
        description="Hide the tool header in the duplicated area",
        default=False,
    )#type: ignore
    open_without_header: BoolProperty(
        name="Hide Header",
        description="Hide the header in the duplicated area",
        default=False,
    )#type: ignore
    open_without_overlays: BoolProperty(
        name="Hide Overlays",
        description="Hide overlays in the duplicated area",
        default=False,
    )#type: ignore
    open_without_gizmo: BoolProperty(
        name="Hide Gizmo",
        description="Hide the gizmo in the duplicated area",
        default=False,
    )#type: ignore
    open_unselectable_objects: BoolProperty(
        name="Make Objects Unselectable",
        description="Make all objects unselectable in the duplicated area",
        default=True
    ) #type: ignore
    def invoke(self, context, event):
        if context.area is None or context.area.type != "VIEW_3D":
            return {"CANCELLED"}

        settings = context.window_manager.popout_settings
        self.open_without_tool_header = settings.open_without_tool_header
        self.open_without_header = settings.open_without_header
        self.open_without_overlays = settings.open_without_overlays
        self.open_without_gizmo = settings.open_without_gizmo
        self.open_unselectable_objects = settings.open_unselectable_objects
        return context.window_manager.invoke_props_dialog(self, title="Pop Out Options")

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "open_without_tool_header")
        layout.prop(self, "open_without_header")
        layout.prop(self, "open_without_overlays")
        layout.prop(self, "open_without_gizmo")
        layout.prop(self, "open_unselectable_objects")

    def execute(self, context):
        if context.area is None or context.window is None:
            return {"CANCELLED"}

        existing_window_ids = {window.as_pointer() for window in context.window_manager.windows}
        source_area_type = context.area.type
        source_camera = None

        if source_area_type == "VIEW_3D":
            active_object = context.active_object
            if active_object is not None and active_object.type == "CAMERA":
                source_camera = active_object
                source_camera.data.passepartout_alpha = 1
                source_camera.data.show_passepartout = True
            # else:
            #     for selected_object in context.selected_objects:
            #         if selected_object.type == "CAMERA":
            #             source_camera = selected_object
            #             break

        result = bpy.ops.screen.area_dupli("INVOKE_DEFAULT")
        if "CANCELLED" in result:
            return {"CANCELLED"}

        op_settings = self

        def _timer_callback():
            return _find_and_configure_new_window(
                existing_window_ids,
                source_area_type,
                op_settings,
                source_camera,
            )

        bpy.app.timers.register(_timer_callback, first_interval=0.05)
        return {"FINISHED"}


class POPOUT_PT_panel(Panel):
    bl_label = "Popout Window"
    bl_idname = "POPOUT_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Popout"

    def draw(self, context):
        layout = self.layout
        settings = context.window_manager.popout_settings

        layout.prop(settings, "open_without_tool_header")
        layout.prop(settings, "open_without_header")
        layout.prop(settings, "open_without_overlays")
        layout.prop(settings, "open_without_gizmo")
        layout.prop(settings, "open_unselectable_objects")
        layout.separator()
        layout.operator(POPOUT_OT_open_window.bl_idname, icon="WINDOW")


classes = (
    POPOUT_PG_settings,
    POPOUT_OT_open_window,
    #POPOUT_PT_panel,
) 


def menu_func(self, context):
    area = getattr(context, "area", None)
    if area is None:
        return

    # Only show the operator in 3D View areas
    if getattr(area, "type", None) != "VIEW_3D":
        return

    self.layout.operator(POPOUT_OT_open_window.bl_idname, icon="WINDOW")


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.WindowManager.popout_settings = PointerProperty(type=POPOUT_PG_settings)

    try:
        bpy.types.INFO_MT_area.append(menu_func)
    except Exception:
        pass


def unregister():
    try:
        bpy.types.INFO_MT_area.remove(menu_func)
    except Exception:
        pass

    if hasattr(bpy.types.WindowManager, "popout_settings"):
        del bpy.types.WindowManager.popout_settings

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
