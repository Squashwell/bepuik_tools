#====================== BEGIN GPL LICENSE BLOCK ======================
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
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
from bepuik_tools.riggenerator import WIDGET_CUBE

#TODO: wiki: Peripheral bones are: bones which are not controlled and have no controlled descendants

import os
import sys
import bpy
import math
from bpy.app.handlers import persistent
import bgl
import blf

if os.path.exists("pydev_debug.py"):
    from bepuik_tools import pydev_debug
    try:    
        pydev_debug.debug()
        dbgm = pydev_debug.dbgm
    except:
        pass



from bepuik_tools import riggenerator
from bepuik_tools import utils

from mathutils import Vector, geometry, Matrix

from bpy.props import EnumProperty, FloatProperty, StringProperty, BoolProperty, PointerProperty

bl_info = {
    "name": "BEPUik Tools",
    "author": "Harrison Nordby, Ross Nordby",
    "version": (0, 3, 0),
    "blender": (2, 7, 0),
    "description": "Automatically create humanoid BEPUik rigs and other rigging knickknacks.",
    "category": "Rigging" }

class BEPUikAutoRigLayers(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "BEPUik Auto Rig Layers"    

    @classmethod
    def poll(cls,context):
        return context.object and context.object.type == 'ARMATURE'

    def draw(self,context):
        riggenerator.draw_rig_layers(self.layout)
        self.layout.prop(bpy.context.object,"show_x_ray")
        self.layout.prop(bpy.context.object.data,"show_bepuik_controls")

class BEPUikTools(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label = "BEPUik Rigging Tools"
    bl_category = "BEPUik"

    def draw(self, context):
        col = self.layout.column(align=True)
        col.operator(CreateFullBodyMetaArmature.bl_idname)
        col.operator(CreateFullBodyRig.bl_idname)
        col.separator()
        col.label("Create Control with Target")
        
        op = col.operator(CreateControl.bl_idname,text="Position and Orientation")
        op.head_tail = 0
        op.lock_rotation = False
        op.scale = .1
        op.widget_name = WIDGET_CUBE
        
        op = col.operator(CreateControl.bl_idname,text="Tail Position Only")
        op.head_tail = 1
        op.lock_rotation = True
        op.scale = .1
        op.widget_name = WIDGET_CUBE

                
#        box = self.layout.box()
#        box.label("Selected Bones:")
#        column = box.column(align=True)
#        column.operator(ApplyBEPUikToSelectedBones.bl_idname,text="Add BEPUik").value = True
#        column.operator(ApplyBEPUikToSelectedBones.bl_idname,text="Remove BEPUik").value = False
#        self.layout.operator(OrganizeBones.bl_idname)
#        self.layout.operator(CreateTwistChain.bl_idname)
#        self.layout.operator(ApplyFingerRig.bl_idname)
#        self.layout.operator(ApplyArmRig.bl_idname)
 
#class BEPUikDebug(bpy.types.Panel):
#    bl_space_type = "VIEW_3D"
#    bl_region_type = "TOOLS"
#    bl_label = "BEPUik Debug"
#    bl_options = {'DEFAULT_CLOSED'}
#    bl_category = "BEPUik"
#    
#    def draw(self, context):
#        col = self.layout.column(align=True)
#        
##        if context.mode == 'POSE' and context.object.pose:
##            pose = context.object.pose
##            col.prop(pose,"bepuik_calculating")
##            col.prop(pose,"bepuik_has_bepuik_bones")
##            col.prop(pose,"bepuik_match_solved")
##            col.prop(pose,"bepuik_selection_as_dragcontrol")
##            col.prop(pose,"bepuik_selection_as_statecontrol")
##            col.prop(pose,"bepuik_skip")
##            col.prop(pose,"bepuik_stiff_children")
##            col.prop(pose,"bepuik_stiff_invisible_bones")
##            col.prop(pose,"bepuik_working_set")
#        
#        col.operator(BEPUikTest.bl_idname)
#        col.operator(BEPUikShowDebugMatrix.bl_idname)

class CreateFullBodyMetaArmature(bpy.types.Operator):
    '''Create Full Body Meta Armature'''
    bl_idname = "bepuik.create_full_body_meta_armature"
    bl_label = "Create Full Body Meta Armature"
    bl_description = "Creates the meta bones which define the basic parameters of a full body rig"
    bl_options = {'REGISTER','UNDO'}

    num_fingers = bpy.props.IntProperty(name="Number of Fingers",description="The number of fingers on each hand, including the thumb",default=5,min=1,max=5)
    num_toes = bpy.props.IntProperty(name="Number of Toes",description="The number of toes the character has on one foot",default=1,min=1,max=5)
    use_simple_toe = bpy.props.BoolProperty(name="Simple Toe", description="Approximate each toe as a single bone", default=True)
    use_thumb = bpy.props.BoolProperty(name="Thumb",description="The first finger will be a thumb",default=True)

    wrist_width = bpy.props.FloatProperty(name="Wrist Width",description="The width of the character's wrist",default=.05)
    wrist_yaw = bpy.props.FloatProperty(name="Wrist Yaw",description="The yaw angle of the character's wrist",default=math.radians(-93.9),subtype='ANGLE')
    wrist_pitch = bpy.props.FloatProperty(name="Wrist Pitch",description="The pitch angle of the character's wrist",default=math.radians(.7),subtype='ANGLE')
    wrist_roll = bpy.props.FloatProperty(name="Wrist Roll",description="The roll angle of the character's wrist",default=math.radians(5.2),subtype='ANGLE')
    
    finger_splay = bpy.props.FloatProperty(name="Finger Splay",description="The amount the fingers are splayed out by default",default=math.radians(-43.1),subtype='ANGLE')
    finger_curl = bpy.props.FloatProperty(name="Finger Curl",description="The default curl of the fingers",default=math.radians(-8.5),subtype='ANGLE')
    thumb_splay = bpy.props.FloatProperty(name="Thumb Splay",description="The extra splay of the thumb",default=math.radians(27.3),subtype='ANGLE')
    thumb_tilt = bpy.props.FloatProperty(name="Thumb Tilt",description="The tilt of the thumb",default=math.radians(-23) ,subtype='ANGLE')
    
    
    foot_width = bpy.props.FloatProperty(name="Foot Width",description="The width of the character's foot",default=.08)    
    toe_curl = bpy.props.FloatProperty(name="Toe Curl",description="The default curl of the toes",default=math.radians(-4),subtype='ANGLE')
    
    shoulder_head_vec = bpy.props.FloatVectorProperty(name="Shoulder Head",description="Position of the shoulder head", default=(0.02, 0, 1.49),subtype='TRANSLATION')
    shoulder_tail_vec = bpy.props.FloatVectorProperty(name="Shoulder Tail",description="Position of the shoulder tail", default=(0.15, 0, 1.49), subtype='TRANSLATION')
    elbow_vec = bpy.props.FloatVectorProperty(name="Elbow",description="Position of the Elbow",default=(.46,.05),size=2,subtype='TRANSLATION')
    wrist_vec = bpy.props.FloatVectorProperty(name="Wrist",description="Position of the Wrist",default=(.72,0.0,1.46),subtype='TRANSLATION')
    
    spine_start_vec = bpy.props.FloatVectorProperty(name="Spine Start",description="Bottom starting point of the spine", default=(0,0,0.93),subtype='TRANSLATION')
    spine_lengths = bpy.props.FloatVectorProperty(name="Spine Lengths",description="Lengths of each spine segment, from hips to head", default=(.15,.16,.30,.11,.17),size=5)

    upleg_vec = bpy.props.FloatVectorProperty(name="Upleg", description="Position of the start of the upper leg",default=(.09,0,.96),subtype='TRANSLATION')
    knee_vec = bpy.props.FloatVectorProperty(name="Knee", description="Position of the knee",default=(0.08,0,0.5),subtype='TRANSLATION')
    ankle_vec = bpy.props.FloatVectorProperty(name="Ankle", description="Position of the ankle",default=(0.07,0.04,0.1),subtype='TRANSLATION')
    toe_vec = bpy.props.FloatVectorProperty(name="Toe", description="Position of the start of the toes",default=(0.07,-0.08,0.01),subtype='TRANSLATION')
    
    eye_center = bpy.props.FloatVectorProperty(name="Eye Center", description="Position of the center of the eye",default=(0.03075,-0.09405,1.71475),subtype='TRANSLATION')
    eye_radius = bpy.props.FloatProperty(name="Eye Radius", description="Radius of the eye",default=0.0166)
    chin_vec = bpy.props.FloatVectorProperty(name="Chin", description="Position of the chin",default=(0,-0.12,1.62),subtype='TRANSLATION')
    jaw_vec = bpy.props.FloatVectorProperty(name="Jaw", description="Position of the head of the jaw",default=(0,-0.03,1.67),subtype='TRANSLATION')
    
    
    
    @classmethod
    def poll(cls,context):
        return context.mode == 'OBJECT'
    
    def execute(self,context):
        global _propertytypes
        bpy.ops.object.select_all(action='DESELECT')
        data = bpy.data.armatures.new(name="MetaBones")
        ob = bpy.data.objects.new(name="Meta Armature",object_data=data)
        bpy.context.scene.objects.link(ob)
        context.scene.objects.active = ob
        bpy.ops.object.mode_set(mode='EDIT')
        
        riggenerator.meta_create_full_body(ob, self.num_fingers, self.num_toes, self.foot_width, self.wrist_width, self.wrist_yaw, self.wrist_pitch, self.wrist_roll, self.use_thumb, self.finger_curl, self.toe_curl, self.finger_splay, self.thumb_splay, self.thumb_tilt, self.shoulder_head_vec, self.shoulder_tail_vec, self.elbow_vec, self.wrist_vec, self.spine_start_vec, self.spine_lengths, self.upleg_vec, self.knee_vec, self.ankle_vec, self.toe_vec, self.eye_center, self.eye_radius, self.chin_vec, self.jaw_vec, self.use_simple_toe)
        
        ob.select = True
        ob.show_x_ray = True
        
        bpy.ops.object.mode_set(mode='OBJECT')
        return {'FINISHED'}

class CreateFullBodyRig(bpy.types.Operator):
    '''Create Full Body Rig'''
    bl_idname = "bepuik.rig_full_body"
    bl_label = "Create Full Body Rig"
    bl_description = "Creates a rig from a meta armature"
    bl_options = {'REGISTER','UNDO'}

    @classmethod
    def poll(cls,context):
        return context.object and context.object.bepuik_autorig.is_meta_armature and context.mode == 'OBJECT' and bpy.context.object.type == 'ARMATURE'
            
    def execute(self,context):
        context.object.hide = False
        riggenerator.widgetdata_refresh_defaults()
        rig_obj = riggenerator.rig_full_body(bpy.context.object,self)
        rig_obj.show_x_ray = True
        rig_obj.data.show_bepuik_controls = True
        rig_obj.use_bepuik_inactive_targets_follow = True
        rig_obj.use_bepuik_dynamic = True
        return {'FINISHED'}

def pchan_get_first_control_with_pulled_point(ob,pchan,x,y,z):
    assert bpy.context.mode == 'POSE'
    
    for constraint in pchan.constraints:
        if constraint.type == 'BEPUIK_CONTROL':
            if constraint.connection_subtarget in ob.pose.bones: 
                if constraint.pulled_point[0] == x:
                    if constraint.pulled_point[1] == y:
                        if constraint.pulled_point[2] == z:
                            return constraint
                    
    return None

def phcan_get_any_tail_control(ob,pchan):
    assert bpy.context.mode == 'POSE'
    
    control = pchan_get_first_control_with_pulled_point(ob,pchan, 0.0, 1.0, 0.0)
    
    if control:
        return control
    else:
        for pchild in pchan.children:
            control = pchan_get_first_control_with_pulled_point(ob,pchan, 0.0, 0.0, 0.0)
            if control:
                if((pchild.bone.head - pchan.bone.tail).length <= .0001):
                    return control
                
    return None

def phcan_get_any_head_control(ob,pchan):
    assert bpy.context.mode == 'POSE'
    
    control = pchan_get_first_control_with_pulled_point(ob,pchan, 0.0, 0.0, 0.0)
    
    if control:
        return control
    elif pchan.parent:
        control = pchan_get_first_control_with_pulled_point(ob,pchan.parent, 0.0, 1.0, 0.0)
        if control:
            if((pchan.parent.bone.tail - pchan.bone.head).length <= .0001):
                return control
                
    return None
        

def is_unique_bone_name(ob,bone_name):
    assert bpy.context.mode == 'EDIT_ARMATURE'
    
    for bone in ob.data.bones:
        if bone.name == bone_name:
            return False
        
    return True
    
    
class CreateControl(bpy.types.Operator):
    '''Create Control'''
    bl_idname = "bepuik.create_control"
    bl_label = "Create Control"
    bl_description = "Create a control and target bone for the currently selected bepuik bones"
    bl_options = {'REGISTER','UNDO'}
    
    head_tail = bpy.props.FloatProperty(name="Head to Tail",description="Head to tail position of the target",default=0,max=1,min=0)
    widget_name = bpy.props.StringProperty(name="Widget",description="Widget to use for bone display",default=WIDGET_CUBE)
    scale = bpy.props.FloatProperty(name="Scale",default=.15)
    lock_rotation = bpy.props.BoolProperty(name="Lock Rotation",default=False)
    name = bpy.props.StringProperty(name="Name",description="Name of the newly created bones",default="")
    presuffix = bpy.props.StringProperty(name="Presuffix",description="Presuffix of the newly created bones",default="")

    @classmethod
    def poll(cls,context):
        ob = bpy.context.object
        return ob and ob.select and ob.type == 'ARMATURE' and ob.mode == 'POSE' and bpy.context.selected_pose_bones
        
    def execute(self,context):
        riggenerator.widgetdata_refresh_defaults()
        ob = bpy.context.object
        previous_mode = ob.mode
        
        bones_with_controls = set()
        new_bone_targets = []
        
        if ob.mode != 'POSE':
            bpy.ops.object.mode_set(mode='POSE')
                    
        if self.head_tail == 1.0:
            default_presuffix = "tail"
            for pchan in bpy.context.selected_pose_bones:
                if phcan_get_any_tail_control(ob,pchan):
                    bones_with_controls.add(pchan.name)   
        elif self.head_tail == 0.0:
            default_presuffix = "head"
            for pchan in bpy.context.selected_pose_bones:
                if phcan_get_any_head_control(ob,pchan):
                    bones_with_controls.add(pchan.name)
        else:
            default_presuffix = "mid"
            
        metabones = riggenerator.MetaBoneDict.from_ob(ob)
        
        if "root" in metabones:
            root = metabones["root"]
        else:
            root = None
        
        pulledmetabones = {}
        for ebone in bpy.context.selected_editable_bones:
            pulledmetabone = metabones[ebone.name]
            pulledmetabones[ebone.name] = pulledmetabone
            
            need_presuffix = False
            
            if self.name:
                base_name = self.name
            else:
                base_name = ebone.basename
                need_presuffix = True
            
            suffix = ebone.name[len(ebone.basename):]
                
            if not is_unique_bone_name(ob, "%s%s" % (base_name,suffix)):
                need_presuffix = True
            
            if self.presuffix:
                presuffix = "%s%s" % ("-",self.presuffix)
            elif need_presuffix:
                presuffix = "%s%s" % ("-",default_presuffix)
            else:
                presuffix = ""
                
            new_bone_name = "%s%s%s" % (base_name,presuffix,suffix)
                
            if is_unique_bone_name(ob, new_bone_name) and ebone.name not in bones_with_controls:
                new_bone_targets.append((ebone.name,new_bone_name))
                riggenerator.rig_point_puller(metabones, new_bone_name, pulledmetabone=pulledmetabone, parent=root, headtotail=self.head_tail, custom_shape_name=self.widget_name, scale=self.scale, lock_rotation=self.lock_rotation)
        
        metabones.to_ob(ob)
        
        for affected_bone_name, target_bone_name in new_bone_targets:
            target_bone = ob.pose.bones[target_bone_name]
            affected_bone = ob.pose.bones[affected_bone_name]
            
            offset = Vector((0,affected_bone.length * self.head_tail,0))
            
            target_bone.matrix = affected_bone.matrix.normalized() * Matrix.Translation(offset)
            riggenerator.organize_pchan_layer(target_bone, affected_bone_name, True)
        
            
        if previous_mode != ob.mode:
            bpy.ops.object.mode_set(mode=previous_mode)
            
        ob.bepuik_autorig.is_auto_rig = True
            
        return {'FINISHED'}

class CreateTwistChain(bpy.types.Operator):
    '''Create Twist Chain'''
    bl_idname = "bepuik.create_twist_chain"
    bl_label = "Create Twist Chain"
    bl_description = "Creates a series of bones from one bone tail to a bone head that twist gradually from the start and end bone"
    bl_options = {'REGISTER','UNDO'}
    
    num_bones = bpy.props.IntProperty(name="Number",description="Number of bones in the chain",default=2,min=1)
    prefix = bpy.props.StringProperty(name="Prefix",description="Prefix to give the twist bones",default="Twist")
    suffix = bpy.props.StringProperty(name="Suffix",description="Suffix to give the twist bones",default="")
    num_executions = 0
    
    @classmethod
    def poll(cls,context):
        return bpy.context.object and bpy.context.object.type == 'ARMATURE' and bpy.context.object.select and bpy.context.mode == 'EDIT_ARMATURE' and len(context.selected_bones) == 2 
    
    def execute(self,context):
        CreateTwistChain.num_executions += 1
        obj = bpy.context.object
        armature = obj.data
        start_bone = context.selected_bones[0]
        end_bone = context.active_bone
        end_point = end_bone.head.copy()
        start_point = start_bone.tail
        roll = start_bone.roll
        bone_direction = (end_point - start_point).normalized()
        bone_length = ((end_point - start_point)/self.num_bones).length
        bone_vector = bone_length * bone_direction
        bone_influence = 1/self.num_bones
         
        newbones = []
        CreateTwistChain.num_executions += 1
        parent_bone = armature.edit_bones.new(name="ntcb%s" % CreateTwistChain.num_executions)
        parent_bone.head = start_point
        parent_bone.tail = end_point
        parent_bone.roll = roll
        parent_bone.use_deform = False
        
        for i in range(self.num_bones):
            CreateTwistChain.num_executions += 1
            n = "ntcb%s" % (CreateTwistChain.num_executions)
            newbone = armature.edit_bones.new(name=n)
            newbones.append(newbone)
            newbone.head = (i * bone_vector) + start_point
            newbone.tail = ((i + 1) * bone_vector) + start_point
            newbone.roll = roll
            newbone.parent = parent_bone
            newbone.use_deform = True
            
                
        bpy.ops.object.mode_set(mode='POSE',toggle=False)
        
        for i in range(self.num_bones):
            pbone = obj.pose.bones[newbones[i].name]
            constraint = pbone.constraints.new(type='COPY_ROTATION')
            constraint.use_x = False
            constraint.use_y = True
            constraint.use_z = False
            constraint.target_space = 'LOCAL'
            constraint.owner_space = 'LOCAL'
            constraint.influence = bone_influence * (i+1)
            constraint.target = obj
            constraint.subtarget = end_bone.name
            pbone.name = "%s-%s%s" % (self.prefix,i+1,self.suffix)
            pbone.use_bepuik = False
        
        pbone = obj.pose.bones[parent_bone.name]
        pbone.name = "%s%s" % (self.prefix,self.suffix)
        bpy.ops.object.mode_set(mode='EDIT',toggle=False)
            
        return {'FINISHED'}
    
def create_and_apply_rig(scene):
    rig_obj = None
    rig_mesh_obj = None
    meta_arm_obj = None
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

#from bpy.app.handlers import persistent
#@persistent
#def debug_scene_update_post(scene):
#    ob = scene.objects.active
#    C = bpy.context
#    active_pose_bone = C.active_pose_bone
#    pydev_debug.dbgc()
#    if ob and ob.type == 'ARMATURE' and ob.pose:
#        for bone in ob.pose.bones:
#            dbg_loc_quat(bone.bepuik_position, bone.bepuik_orientation, bone.name)
#            if bone == active_pose_bone:
#                dbg_loc_quat(bone.bepuik_transform_position, bone.bepuik_transform_orientation, bone.name + " transform")
            
            
class BEPUikShowDebugMatrix(bpy.types.Operator):
    '''BEPUikShowDebugMatrix'''
    bl_idname = "bepuik.show_debug_matrix"
    bl_label = "Debug Matrix"
    bl_description = "Debug Matrix"
    
    @classmethod
    def poll(cls,context):
        return True
    
    def execute(self,context):
        if debug_scene_update_post in bpy.app.handlers.scene_update_post:
            pydev_debug.visualize(False)
            bpy.app.handlers.scene_update_post.remove(debug_scene_update_post)
        else:
            pydev_debug.visualize(True)
            bpy.app.handlers.scene_update_post.append(debug_scene_update_post)
            
            
        return {'FINISHED'}

class BEPUikTest(bpy.types.Operator):
    '''BEPUikTest'''
    bl_idname = "bepuik.test"
    bl_label = "BEPUikTest"
    bl_description = "BEPUikTest"
    
    @classmethod
    def poll(cls,context):
        return True
        
    def execute(self,context):
        create_and_apply_rig(bpy.context.scene)
        
        return {'FINISHED'} 
        

class BEPUikObjectProperties(bpy.types.PropertyGroup):
    is_meta_armature = BoolProperty(default=False,options=set())
    is_auto_rig = BoolProperty(default=False,options=set())
    use_thumb = BoolProperty(default=False,options=set())
    use_simple_toe = BoolProperty(default=False,options=set())
            
def register():
    bpy.utils.register_module(__name__)
    bpy.types.Object.bepuik_autorig = PointerProperty(type=BEPUikObjectProperties)

    
def unregister():
    bpy.utils.unregister_module(__name__)



