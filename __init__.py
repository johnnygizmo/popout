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
    open_without_tool_header = BoolProperty(
        name="Hide Tool Header",
        description="Hide the tool header in the duplicated area",
        default=False,
    )
    
    open_without_header = BoolProperty(
        name="Hide Header",
        description="Hide the header in the duplicated area",
        default=False,
    )
    open_without_overlays = BoolProperty(
        name="Hide Overlays",
        description="Hide overlays in the duplicated area",
        default=False,
    )
    open_without_gizmo = BoolProperty(
        name="Hide Gizmo",
        description="Hide the gizmo in the duplicated area",
        default=False,
    )


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
        return None

    return 0.05


class POPOUT_OT_open_window(Operator):
    bl_idname = "popout.open_window"
    bl_label = "Pop Out Current Area"
    bl_description = "Open the current area in a new Blender window"
    bl_options = {"REGISTER"}

    def execute(self, context):
        if context.area is None or context.window is None:
            return {"CANCELLED"}

        settings = context.window_manager.popout_settings
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

        def _timer_callback():
            return _find_and_configure_new_window(
                existing_window_ids,
                source_area_type,
                settings,
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
        layout.separator()
        layout.operator(POPOUT_OT_open_window.bl_idname, icon="WINDOW")


classes = (
    POPOUT_PG_settings,
    POPOUT_OT_open_window,
    POPOUT_PT_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.WindowManager.popout_settings = PointerProperty(type=POPOUT_PG_settings)


def unregister():
    del bpy.types.WindowManager.popout_settings

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
