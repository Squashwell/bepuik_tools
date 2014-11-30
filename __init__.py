# ====================== BEGIN GPL LICENSE BLOCK ======================
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
#  The Original Code is Copyright (C) 2013 by: 
#  Harrison Nordby and Ross Nordby
#  All rights reserved.
#
#  The Original Code is: all of this file
#  
#  Contributor(s): none yet.
#
#
#======================= END GPL LICENSE BLOCK ========================
import bpy
import math

from . import riggenerator
from .riggenerator import WIDGET_CUBE
from mathutils import Vector, Matrix

from bpy.props import FloatProperty, FloatVectorProperty, BoolProperty, StringProperty, IntProperty, BoolVectorProperty, \
    PointerProperty

import keyingsets_builtins

bl_info = {
    "name": "BEPUik Tools",
    "author": "Harrison Nordby, Ross Nordby",
    "version": (0, 4, 1),
    "blender": (2, 72, 0),
    "description": "Automatically create humanoid BEPUik rigs and other rigging knickknacks.",
    "location": "View3D > Tool Shelf > BEPUik and View3D > Properties Shelf",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/User:Squashwell",
    "tracker_url": "https://github.com/Squashwell/bepuik_tools/issues",
    "category": "Rigging"}


def get_armature_ob(context):
    if context.object:
        if context.object.type == 'ARMATURE':
            return context.object
        else:
            return context.object.find_armature()

    return None


class BEPUikAutoRigOperator():
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if get_armature_ob(context):
            return True

        return False


import re


def get_toes(pchans, suffix):
    p = re.compile(r"toe[0-9]+-[0-9]+")
    toes = []
    for pchan in pchans:
        if pchan.name.endswith(suffix) and p.match(pchan.name):
            toes.append(pchan)

    return toes


def get_finger_rotators(pchans, suffix):
    p = re.compile(r"finger[0-9]+-[0-9]+ rot")
    finger_rotators = []
    for pchan in pchans:
        if pchan.name.endswith(suffix) and p.match(pchan.name):
            finger_rotators.append(pchan)

    return finger_rotators


def get_fingers(pchans, suffix):
    p = re.compile(r"finger[0-9]+-[0-9]+")
    fingers = []
    for pchan in pchans:
        if pchan.name.endswith(suffix) and p.match(pchan.name):
            fingers.append(pchan)

    return fingers


def get_palm_bones(pchans, suffix):
    p_rot = re.compile(r"finger[0-9]+-[0-9]+ rot")
    p = re.compile(r"finger[0-9]+-1")
    palm_bones = []
    for pchan in pchans:
        if pchan.name.endswith(suffix) and p.match(pchan.name) and not p_rot.match(pchan.name):
            palm_bones.append(pchan)

    return palm_bones


def get_bone(pchans, name, suffix):
    bone_name = "%s%s" % (name, suffix)

    if bone_name in pchans:
        return pchans[bone_name]

    return None


def clear_pchan_control_rigidities(pchan):
    for constraint in pchan.constraints:
        if constraint.type == 'BEPUIK_CONTROL':
            constraint.bepuik_rigidity = 0
            constraint.orientation_rigidity = 0
            constraint.use_hard_rigidity = 0


def clear_rigidities_and_selection(pchans, foot, toes):
    clear_pchan_control_rigidities(foot)

    for toe in toes:
        clear_pchan_control_rigidities(toe)

    for pchan in pchans:
        pchan.bone.select = False


def find_control_with_target(pchan, target_name):
    for constraint in pchan.constraints:
        if constraint.type == 'BEPUIK_CONTROL' and constraint.connection_subtarget == target_name:
            return constraint

    return None


class BEPUikAutoRigTweakFingers(BEPUikAutoRigOperator, bpy.types.Operator):
    bl_idname = "bepuik_tools.autorig_tweak_fingers"
    bl_label = "Fingers Tweak"
    bl_description = "Setup pose rigidities so the fingers are easily tweakable"

    suffix = StringProperty(name="Suffix", description="Suffix of the foot bone, (.L,.R,...)", default=".L")

    def execute(self, context):
        ob = get_armature_ob(context)

        pchans = ob.pose.bones

        hand = get_bone(pchans, "hand", self.suffix)
        fingers = get_fingers(pchans, self.suffix)

        palm_bones = get_palm_bones(pchans, self.suffix)

        for pchan in fingers:
            pchan.bone.select = False
            clear_pchan_control_rigidities(pchan)

        for pchan in palm_bones:
            con = find_control_with_target(pchan, riggenerator.split_suffix(pchan.name)[0] + " rot%s" % self.suffix)
            if con:
                con.orientation_rigidity = 1.0

        if hand:
            con = find_control_with_target(hand, "hand target%s" % self.suffix)
            if con:
                con.bepuik_rigidity = 0
                con.orientation_rigidity = 0
                con.use_hard_rigidity = True

        return {'FINISHED'}


class BEPUikAutoRigPivotHeel(BEPUikAutoRigOperator, bpy.types.Operator):
    bl_idname = "bepuik_tools.autorig_pivot_heel"
    bl_label = "Heel Pivot"
    bl_description = "Setup the pose so the foot pivots on the heel"

    suffix = StringProperty(name="Suffix", description="Suffix of the foot bone, (.L,.R,...)", default=".L")

    def execute(self, context):
        ob = get_armature_ob(context)

        pchans = ob.pose.bones

        foot = get_bone(pchans, "foot", self.suffix)
        foot_target = get_bone(pchans, "foot target", self.suffix)
        toes = get_toes(pchans, self.suffix)

        if foot and foot_target and toes:
            pass
        else:
            return {'CANCELLED'}

        clear_rigidities_and_selection(pchans, foot, toes)

        constraint = find_control_with_target(foot, foot_target.name)
        constraint.use_hard_rigidity = True

        foot_target.bone.select = True
        ob.data.bones.active = foot_target.bone

        floor_target = get_bone(pchans, "foot floor target", self.suffix)

        if floor_target:
            floor = get_bone(pchans, "floor", self.suffix)

            if floor:
                constraint = find_control_with_target(floor, floor_target.name)
                constraint.use_hard_rigidity = True

        return {'FINISHED'}


class BEPUikAutoRigPivotToes(BEPUikAutoRigOperator, bpy.types.Operator):
    bl_idname = "bepuik_tools.autorig_pivot_toes"
    bl_label = "Toes Pivot"
    bl_description = "Setup the pose so the foot pivots on the toes"

    suffix = StringProperty(name="Suffix", description="Suffix of the foot bone, (.L,.R,...)", default=".L")

    def execute(self, context):
        ob = get_armature_ob(context)

        pchans = ob.pose.bones

        foot = get_bone(pchans, "foot", self.suffix)
        toes_target = get_bone(pchans, "toes target", self.suffix)
        foot_ball_target = get_bone(pchans, "foot ball target", self.suffix)
        toes = get_toes(pchans, self.suffix)

        if foot and foot_ball_target and toes_target and toes:
            pass
        else:
            return {'CANCELLED'}

        clear_rigidities_and_selection(pchans, foot, toes)

        constraint = find_control_with_target(foot, foot_ball_target.name)
        constraint.orientation_rigidity = 1

        for toe in toes:
            constraint = find_control_with_target(toe, toes_target.name)
            if constraint:
                constraint.use_hard_rigidity = True

        foot_ball_target.bone.select = True
        ob.data.bones.active = foot_ball_target.bone


        floor_target = get_bone(pchans, "foot floor target", self.suffix)
        if floor_target:
            floor = get_bone(pchans, "floor", self.suffix)

            if floor:
                constraint = find_control_with_target(floor, floor_target.name)
                constraint.use_hard_rigidity = True

        return {'FINISHED'}


class BEPUikAutoRigLayers(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "BEPUik Auto Rig"

    @classmethod
    def poll(cls, context):
        return context.object and (context.object.type == 'ARMATURE' or context.object.find_armature())

    def draw(self, context):
        if context.object.type == 'ARMATURE':
            ob = context.object
        else:
            ob = context.object.find_armature()

        layout = self.layout

        middle = layout.row()

        col = middle.column(align=True)
        col.label("Left")
        col.operator(BEPUikAutoRigTweakFingers.bl_idname).suffix = ".L"
        col.operator(BEPUikAutoRigPivotHeel.bl_idname).suffix = ".L"
        col.operator(BEPUikAutoRigPivotToes.bl_idname).suffix = ".L"

        col = middle.column(align=True)
        col.label("Right")
        col.operator(BEPUikAutoRigTweakFingers.bl_idname).suffix = ".R"
        col.operator(BEPUikAutoRigPivotHeel.bl_idname).suffix = ".R"
        col.operator(BEPUikAutoRigPivotToes.bl_idname).suffix = ".R"

        riggenerator.layout_rig_layers(self.layout, ob)


class BEPUikTools(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label = "BEPUik Rigging Tools"
    bl_category = "BEPUik"

    def draw(self, context):
        col = self.layout.column(align=True)
        col.label("Meta Armature Presets:")
        op = col.operator(CreateFullBodyMetaArmature.bl_idname, text="Biped")
        op.use_thumb = True
        op.num_fingers = 5
        op.num_tail_bones = 0
        op.use_ears = False

        op.spine_pitch = 0
        op.head_pitch = 0

        op.arm_yaw = -1.570796
        op.arm_pitch = -.048869
        op.arm_roll = math.radians(0)

        op.wrist_yaw = 0
        op.wrist_pitch = 0
        op.wrist_roll = 0

        op.elbow_vec = Vector((-0.027, 0.26))
        op.wrist_vec = Vector((0, 0.56925))

        op = col.operator(CreateFullBodyMetaArmature.bl_idname, text="Quadruped")
        op.num_fingers = 5
        op.use_thumb = False
        op.num_tail_bones = 3
        op.use_ears = True

        op.spine_pitch = math.radians(90)
        op.head_pitch = math.radians(-90)

        op.arm_yaw = math.radians(-180)
        op.arm_pitch = math.radians(0)
        op.arm_roll = math.radians(-90)

        op.wrist_yaw = math.radians(-90)
        op.wrist_pitch = math.radians(0)
        op.wrist_roll = math.radians(90)

        op.elbow_vec = Vector((-0.045,0.413))
        op.wrist_vec = Vector((0,0.91))

        col.separator()

        col.operator(CreateFullBodyRig.bl_idname, text="Generate Rig")
        col.separator()
        col.label("Create Control with Target:")

        op = col.operator(CreateControl.bl_idname, text="Position and Orientation")
        op.head_tail = 0
        op.lock_rotation = (False, False, False)
        op.lock_rotation_w = False
        op.lock_rotations_4d = False
        op.scale = .1
        op.widget_name = WIDGET_CUBE
        op.create_empties = False

        op = col.operator(CreateControl.bl_idname, text="Tail Position Only")
        op.head_tail = 1
        op.lock_rotation = (True, True, True)
        op.lock_rotation_w = True
        op.lock_rotations_4d = True
        op.scale = .1
        op.widget_name = WIDGET_CUBE
        op.create_empties = False

        op = col.operator(CreateControl.bl_idname, text="Empty")
        op.head_tail = 0
        op.lock_rotation = (False, False, False)
        op.lock_rotation_w = False
        op.lock_rotations_4d = False
        op.create_empties = True


class CreateFullBodyMetaArmature(bpy.types.Operator):
    """Create Full Body Meta Armature"""
    bl_idname = "bepuik_tools.create_full_body_meta_armature"
    bl_label = "Create Full Body Meta Armature"
    bl_description = "Create an armature with the required meta bones that define a full body BEPUik rig"
    bl_options = {'REGISTER', 'UNDO'}

    num_fingers = IntProperty(name="Number of Fingers",
                              description="The number of fingers on each hand, including the thumb",
                              default=5, min=1, max=5)
    num_toes = IntProperty(name="Number of Toes",
                           description="The number of toes the character has on one foot", default=1, min=1,
                           max=5)
    use_simple_toe = BoolProperty(name="Simple Toe", description="Approximate each toe as a single bone",
                                  default=True)
    use_thumb = BoolProperty(name="Thumb", description="The first finger will be a thumb", default=True)

    use_simple_hand = BoolProperty(name="Simple Hand", description="Simpler hand with fewer bones", default=False)

    use_ears = BoolProperty(name="Ears", description="Create ears", default=False)


    use_bepuik_tail = BoolProperty(name="Rig Tail with BEPUik", description="Rig tail with BEPUik Constraints", default=True)

    num_tail_bones = IntProperty(name="Number of Tail Bones",
                           description="The number of tail bones in the character's tail", default=0, min=0,
                           max=20)

    tail_length = FloatProperty(name="Tail Length", description="Length of the tail", default=1.0, min=.1)



    use_belly = BoolProperty(name="Belly", description="Create belly bone", default=False)

    spine_pitch = FloatProperty(name="Spine Pitch", description="The pitch angle of the character's spine",
                                default=0, subtype='ANGLE')

    head_pitch = FloatProperty(name="Head Pitch", description="The pitch angle of the character's head",
                              default=0, subtype='ANGLE')

    arm_yaw = FloatProperty(name="Arm Yaw", description="The yaw angle of the character's arm",
                              default=-1.570796, subtype='ANGLE')
    arm_pitch = FloatProperty(name="Arm Pitch", description="The pitch angle of the character's arm",
                                default=-.048869, subtype='ANGLE')
    arm_roll = FloatProperty(name="Arm Roll", description="The roll angle of the character's arm",
                               default=0, subtype='ANGLE')

    wrist_yaw = FloatProperty(name="Wrist Yaw", description="The yaw angle of the character's wrist",
                              default=0, subtype='ANGLE')
    wrist_pitch = FloatProperty(name="Wrist Pitch", description="The pitch angle of the character's wrist",
                                default=0, subtype='ANGLE')
    wrist_roll = FloatProperty(name="Wrist Roll", description="The roll angle of the character's wrist",
                               default=0, subtype='ANGLE')

    wrist_width = FloatProperty(name="Wrist Width", description="The width of the character's wrist",
                                default=.05)

    finger_splay = FloatProperty(name="Finger Splay",
                                 description="The amount the fingers are splayed out by default",
                                 default=math.radians(-43.1), subtype='ANGLE')
    finger_curl = FloatProperty(name="Finger Curl", description="The default curl of the fingers",
                                default=math.radians(-8.5), subtype='ANGLE')
    thumb_splay = FloatProperty(name="Thumb Splay", description="The extra splay of the thumb",
                                default=math.radians(27.3), subtype='ANGLE')
    thumb_tilt = FloatProperty(name="Thumb Tilt", description="The tilt of the thumb",
                               default=math.radians(-23), subtype='ANGLE')

    foot_width = FloatProperty(name="Foot Width", description="The width of the character's foot",
                               default=.08)
    toe_curl = FloatProperty(name="Toe Curl", description="The default curl of the toes",
                             default=math.radians(-4), subtype='ANGLE')

    shoulder_head_vec = FloatVectorProperty(name="Shoulder Head", description="Position of the shoulder head",
                                            default=(0.02, 0.0, 0.55965), subtype='TRANSLATION')
    shoulder_tail_vec = FloatVectorProperty(name="Shoulder Tail", description="Position of the shoulder tail",
                                            default=(0.1302, 0, 0), subtype='TRANSLATION')
    elbow_vec = FloatVectorProperty(name="Elbow", description="Position of the Elbow", default=(-0.027, 0.26),
                                    size=2, subtype='TRANSLATION')
    wrist_vec = FloatVectorProperty(name="Wrist", description="Position of the Wrist",size=2,
                                    default=(0, 0.56925), subtype='TRANSLATION')

    spine_start_vec = FloatVectorProperty(name="Spine Start",
                                          description="Bottom starting point of the spine",
                                          default=(0, 0, 0.93), subtype='TRANSLATION')
    spine_lengths = FloatVectorProperty(name="Spine Lengths",
                                        description="Lengths of each spine segment, from hips to head",
                                        default=(.15, .16, .30, .11), size=4)

    upleg_vec = FloatVectorProperty(name="Upleg", description="Position of the start of the upper leg",
                                    default=(.09, 0, .96), subtype='TRANSLATION')
    knee_vec = FloatVectorProperty(name="Knee", description="Position of the knee", default=(0.08, 0, 0.5),
                                   subtype='TRANSLATION')
    ankle_vec = FloatVectorProperty(name="Ankle", description="Position of the ankle",
                                    default=(0.07, 0.04, 0.1), subtype='TRANSLATION')
    toe_vec = FloatVectorProperty(name="Toe", description="Position of the start of the toes",
                                  default=(0.07, -0.08, 0.01), subtype='TRANSLATION')

    head_length = FloatProperty(name="Head Length", description="Length of the head", default=.17)

    eye_center = FloatVectorProperty(name="Eye Center", description="Position of the center of the eye",
                                     default=(0.03075, -0.09405, 0.0648), subtype='TRANSLATION')
    eye_radius = FloatProperty(name="Eye Radius", description="Radius of the eye", default=0.0166)
    chin_vec = FloatVectorProperty(name="Chin", description="Position of the chin", default=(0, -0.12, -0.03025),
                                   subtype='TRANSLATION')
    jaw_vec = FloatVectorProperty(name="Jaw", description="Position of the head of the jaw",
                                  default=(0, -0.03, 0.0196), subtype='TRANSLATION')






    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')
        data = bpy.data.armatures.new(name="MetaBones")
        ob = bpy.data.objects.new(name="Meta Armature", object_data=data)
        bpy.context.scene.objects.link(ob)
        context.scene.objects.active = ob
        bpy.ops.object.mode_set(mode='EDIT')

        riggenerator.meta_create_full_body(ob, self.num_fingers, self.num_toes, self.foot_width, self.wrist_width, self.wrist_yaw, self.wrist_pitch, self.wrist_roll,
                          self.use_thumb, self.finger_curl, self.toe_curl, self.finger_splay, self.thumb_splay, self.thumb_tilt, self.arm_yaw, self.arm_pitch, self.arm_roll, self.shoulder_head_vec,
                          self.shoulder_tail_vec, self.elbow_vec, self.wrist_vec, self.spine_start_vec, self.spine_pitch, self.spine_lengths, self.upleg_vec, self.knee_vec,
                          self.ankle_vec, self.toe_vec, self.head_length, self.head_pitch, self.eye_center, self.eye_radius, self.chin_vec, self.jaw_vec, self.use_simple_toe, self.num_tail_bones, self.tail_length, self.use_ears, self.use_belly, self.use_bepuik_tail, self.use_simple_hand)

        ob.select = True
        ob.show_x_ray = True

        bpy.ops.object.mode_set(mode='OBJECT')

        if bpy.context.area.type == 'VIEW_3D':
            bpy.context.area.spaces[0].show_relationship_lines = False

        return {'FINISHED'}


class CreateFullBodyRig(bpy.types.Operator):
    """Create Full Body Rig"""
    bl_idname = "bepuik_tools.rig_full_body"
    bl_label = "Create Full Body Rig"
    bl_description = "Use selected meta armature as input to generate a new animation-ready armature"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.bepuik_autorig.is_meta_armature and context.mode == 'OBJECT' and bpy.context.object.type == 'ARMATURE'

    def execute(self, context):
        context.object.hide = False
        riggenerator.widgetdata_refresh_defaults()
        rig_obj = riggenerator.rig_full_body(bpy.context.object, self)
        rig_obj.show_x_ray = True
        rig_obj.data.show_bepuik_controls = True
        rig_obj.use_bepuik_inactive_targets_follow = True
        rig_obj.use_bepuik_dynamic = True

        if bpy.context.area.type == 'VIEW_3D':
            bpy.context.area.spaces[0].show_relationship_lines = False

        return {'FINISHED'}


def pchan_get_first_control_with_pulled_point(ob, pchan, x, y, z):
    assert bpy.context.mode == 'POSE'

    for constraint in pchan.constraints:
        if constraint.type == 'BEPUIK_CONTROL':
            if constraint.connection_subtarget in ob.pose.bones:
                if constraint.pulled_point[0] == x:
                    if constraint.pulled_point[1] == y:
                        if constraint.pulled_point[2] == z:
                            return constraint

    return None


def phcan_get_any_tail_control(ob, pchan):
    assert bpy.context.mode == 'POSE'

    control = pchan_get_first_control_with_pulled_point(ob, pchan, 0.0, 1.0, 0.0)

    if control:
        return control
    else:
        for pchild in pchan.children:
            control = pchan_get_first_control_with_pulled_point(ob, pchan, 0.0, 0.0, 0.0)
            if control:
                if (pchild.bone.head - pchan.bone.tail).length <= .0001:
                    return control

    return None


def phcan_get_any_head_control(ob, pchan):
    assert bpy.context.mode == 'POSE'

    control = pchan_get_first_control_with_pulled_point(ob, pchan, 0.0, 0.0, 0.0)

    if control:
        return control
    elif pchan.parent:
        control = pchan_get_first_control_with_pulled_point(ob, pchan.parent, 0.0, 1.0, 0.0)
        if control:
            if (pchan.parent.bone.tail - pchan.bone.head).length <= .0001:
                return control

    return None


def is_unique_bone_name(ob, bone_name):
    assert bpy.context.mode == 'EDIT_ARMATURE'

    for bone in ob.data.bones:
        if bone.name == bone_name:
            return False

    return True


class CreateControl(BEPUikAutoRigOperator, bpy.types.Operator):
    """Create Control"""
    bl_idname = "bepuik_tools.create_control_and_target"
    bl_label = "Create Control and Target"
    bl_description = "Create a control and target for each currently selected bepuik bones"

    head_tail = FloatProperty(name="Head to Tail", description="Head to tail position of the target",
                              default=0, max=1, min=0)
    widget_name = StringProperty(name="Widget", description="Widget to use for bone display",
                                 default=WIDGET_CUBE)
    scale = FloatProperty(name="Scale", default=.15)
    lock_rotation_w = BoolProperty(name="Lock Rotation w", default=False)
    lock_rotation = BoolVectorProperty(name="Lock Rotation", default=(False, False, False))
    lock_rotations_4d = BoolProperty(name="Lock Rotation 4d", default=False)
    name = StringProperty(name="Name", description="Name of the newly created bones", default="")
    presuffix = StringProperty(name="Presuffix", description="Presuffix of the newly created bones",
                               default="")
    create_empties = BoolProperty(name="Create Target Empties", default=False,
                                  description="Create target empties as targets instead of target bones")

    @classmethod
    def poll(cls, context):
        ob = get_armature_ob(context)
        if ob and bpy.context.selected_pose_bones:
            return True
        else:
            return False

    def execute(self, context):
        riggenerator.widgetdata_refresh_defaults()
        ob = bpy.context.object
        previous_mode = ob.mode

        bones_with_controls = set()
        new_targets = []

        if self.create_empties:
            effective_head_tail = 0
            default_presuffix = "target"
            prefix = "%s " % ob.name
        else:
            prefix = ""
            effective_head_tail = self.head_tail
            if effective_head_tail == 1.0:
                default_presuffix = "tail target"
                for pchan in bpy.context.selected_pose_bones:
                    if phcan_get_any_tail_control(ob, pchan):
                        bones_with_controls.add(pchan.name)
            elif effective_head_tail == 0.0:
                default_presuffix = "target"
                for pchan in bpy.context.selected_pose_bones:
                    if phcan_get_any_head_control(ob, pchan):
                        bones_with_controls.add(pchan.name)
            else:
                default_presuffix = "mid target"

        metabones = riggenerator.MetaBoneDict.from_ob(ob)

        if "root" in metabones:
            root = metabones["root"]
        else:
            root = None

        controlledmetabones = {}
        for ebone in bpy.context.selected_editable_bones:
            controlledmetabone = metabones[ebone.name]
            controlledmetabones[ebone.name] = controlledmetabone

            need_presuffix = False

            if self.name:
                base_name = self.name
            else:
                base_name = ebone.basename
                need_presuffix = True

            suffix = ebone.name[len(ebone.basename):]

            if self.create_empties:
                if ob.name in bpy.data.objects:
                    need_presuffix = True
            else:
                if not is_unique_bone_name(ob, "%s%s" % (base_name, suffix)):
                    need_presuffix = True

            if self.presuffix:
                presuffix = " %s" % self.presuffix
            elif need_presuffix:
                presuffix = " %s" % default_presuffix
            else:
                presuffix = ""

            new_target_name = "%s%s%s%s" % (prefix, base_name, presuffix, suffix)

            if self.create_empties:
                if new_target_name not in bpy.data.objects:
                    new_targets.append((ebone.name, new_target_name))
                    target = bpy.data.objects.new(name=new_target_name, object_data=None)
                    bpy.context.scene.objects.link(target)
            else:
                if is_unique_bone_name(ob, new_target_name) and ebone.name not in bones_with_controls:
                    new_targets.append((ebone.name, new_target_name))
                    riggenerator.rig_new_target(metabones, new_target_name, controlledmetabone=controlledmetabone,
                                                parent=root, headtotail=effective_head_tail,
                                                custom_shape_name=self.widget_name, scale=self.scale,
                                                lock_rotation=self.lock_rotation,
                                                lock_rotations_4d=self.lock_rotations_4d, use_rest_offset=True)

        if self.create_empties:
            bpy.ops.object.mode_set(toggle=False, mode='POSE')

            for affected_bone_name, target_name in new_targets:
                target = bpy.data.objects[target_name]
                affected_bone = ob.pose.bones[affected_bone_name]

                c = affected_bone.constraints.new(type='BEPUIK_CONTROL')
                c.connection_target = target

                namesuffix_pair = riggenerator.split_suffix(new_target_name)

                c.name = "%s control%s" % (namesuffix_pair[0], namesuffix_pair[1])

                target.matrix_world = ob.matrix_world * affected_bone.matrix.normalized()

                target.empty_draw_type = 'ARROWS'
                target.empty_draw_size = affected_bone.bone.length
        else:
            metabones.to_ob(ob)

            for affected_bone_name, target_bone_name in new_targets:
                target_bone = ob.pose.bones[target_bone_name]
                affected_bone = ob.pose.bones[affected_bone_name]

                offset = Vector((0, affected_bone.length * self.head_tail, 0))

                target_bone.matrix = affected_bone.matrix.normalized() * Matrix.Translation(offset)
                target_bone.scale = (1, 1, 1)

                if ob.bepuik_autorig.is_auto_rig:
                    riggenerator.organize_pchan_layer(target_bone, affected_bone_name, True)

        if previous_mode != ob.mode:
            bpy.ops.object.mode_set(mode=previous_mode)

        return {'FINISHED'}


def create_and_apply_rig(scene):
    bpy.ops.object.mode_set()
    if 'Meta Armature' in scene.objects:
        meta_arm_obj = bpy.context.scene.objects['Meta Armature']
        scene.objects.unlink(meta_arm_obj)
        meta_arm_obj.name = "Other Meta Armature"

    bpy.ops.bepuik.create_full_body_meta_armature()
    meta_arm_obj = bpy.context.scene.objects['Meta Armature']

    if 'Rig' in bpy.context.scene.objects:
        rig_obj = scene.objects['Rig']
        rig_obj.name = "Other Rig"
        bpy.context.scene.objects.unlink(rig_obj)

    if 'Rig Mesh' in bpy.context.scene.objects:
        rig_mesh_obj = scene.objects['Rig Mesh']
    else:
        raise Exception("Need Rig Mesh")

    rig_mesh_obj.modifiers.clear()
    meta_arm_obj.select = True
    scene.objects.active = meta_arm_obj
    bpy.ops.bepuik.rig_full_body()
    rig_obj = bpy.context.scene.objects['Rig']

    rig_obj.select = True
    rig_mesh_obj.hide_select = False
    rig_mesh_obj.select = True
    scene.objects.active = rig_obj
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    rig_mesh_obj.select = False
    rig_mesh_obj.hide_select = True


class BEPUikTest(bpy.types.Operator):
    """BEPUikTest"""
    bl_idname = "bepuik_tools.test"
    bl_label = "BEPUikTest"
    bl_description = "BEPUikTest"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        create_and_apply_rig(bpy.context.scene)

        return {'FINISHED'}


class BEPUikObjectProperties(bpy.types.PropertyGroup):
    is_meta_armature = BoolProperty(default=False, options=set())
    is_auto_rig = BoolProperty(default=False, options=set())
    use_thumb = BoolProperty(default=False, options=set())
    use_simple_toe = BoolProperty(default=False, options=set())
    use_bepuik_tail = BoolProperty(default=False, options=set())
    use_simple_hand = BoolProperty(default=False, options=set())




class BUILTIN_KSI_BEPUikControlsTargets(bpy.types.KeyingSetInfo):
    """Insert a keyframe for all BEPUik Controls' rigidities and their targets' location and rotation"""
    bl_idname = "BEPUikControlsTargets"
    bl_label = "BEPUik Controls and Targets"

    poll = keyingsets_builtins.BUILTIN_KSI_WholeCharacter.poll

    def iterator(ksi, context, ks):
        ksi.targets = set()
        ob = context.active_object

        for pchan in ob.pose.bones:
            if pchan.use_bepuik:
                for con in pchan.constraints:
                    if con.type == 'BEPUIK_CONTROL':
                        if con.connection_subtarget:
                            ksi.targets.add(con.connection_subtarget)

        for pchan in ob.pose.bones:
            ksi.generate(context, ks, pchan)


    def generate(ksi, context, ks, pchan):
        if pchan.name in ksi.targets:
            # loc, rot, scale - only include unlocked ones
            ksi.doLoc(ks, pchan)

            if pchan.rotation_mode in {'QUATERNION', 'AXIS_ANGLE'}:
                ksi.doRot4d(ks, pchan)
            else:
                ksi.doRot3d(ks, pchan)

        if pchan.use_bepuik:
            for con in pchan.constraints:
                if con.type == 'BEPUIK_CONTROL':
                    ksi.addProp(ks, con, 'bepuik_rigidity')
                    ksi.addProp(ks, con, 'orientation_rigidity')
                    ksi.addProp(ks, con, 'use_hard_rigidity')

    addProp = keyingsets_builtins.BUILTIN_KSI_WholeCharacter.addProp
    doLoc = keyingsets_builtins.BUILTIN_KSI_WholeCharacter.doLoc
    doRot3d = keyingsets_builtins.BUILTIN_KSI_WholeCharacter.doRot3d
    doRot4d = keyingsets_builtins.BUILTIN_KSI_WholeCharacter.doRot4d

def register():
    bpy.utils.register_module(__name__)
    bpy.types.Object.bepuik_autorig = PointerProperty(type=BEPUikObjectProperties)


def unregister():
    bpy.utils.unregister_module(__name__)
