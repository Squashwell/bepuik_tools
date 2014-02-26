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
#  The Original Code is: all of this file, except for root widget
#  pydata taken from Rigify's utils.py
#
#  Contributor(s): none yet.
#
#
#======================= END GPL LICENSE BLOCK ========================

import bpy

from bepuik_tools import utils
from mathutils import Vector, Matrix, geometry

import math
import inspect

AL_ANIMATABLE = 0
AL_TARGET = 1
AL_DEFORMER = 2
AL_MECHANICAL = 3
AL_BEPUIK_BONE = 4

AL_SPINE = 17
AL_HEAD = 16
AL_ROOT = 18

AL_ARM_L = 8
AL_HAND_L = 9
AL_LEG_L = 10
AL_FOOT_L = 11
AL_RIB_L = 12

AL_ARM_R = AL_ARM_L + 16
AL_HAND_R = AL_HAND_L + 16
AL_LEG_R = AL_LEG_L + 16
AL_FOOT_R = AL_FOOT_L + 16
AL_RIB_R = AL_RIB_L + 16

AL_START = set((AL_ARM_L,AL_ARM_R,AL_LEG_L,AL_LEG_R,AL_SPINE,AL_HEAD,AL_HAND_L,AL_HAND_R,AL_FOOT_L,AL_FOOT_R))

BEPUIK_BALL_SOCKET_RIGIDITY_DEFAULT = 16

ARM_SUBSTRINGS = ('shoulder','clavicle','loarm','uparm','hand','elbow',)
LEG_SUBSTRINGS = ('leg','foot','knee','heel','ball',)
FOOT_SUBSTRINGS = ('toe',)
TORSO_SUBSTRINGS = ('spine','hip','chest','torso',)
RIB_SUBSTRINGS = ('rib',)
HAND_SUBSTRINGS = ('finger','thumb','palm',)
HEAD_SUBSTRINGS = ('head','neck','eye','jaw',)
ROOT_SUBSTRINGS = ('root',)
TARGET_SUBSTRINGS = ('target',)


SUBSTRING_SETS = []
SUBSTRING_SETS.append(HAND_SUBSTRINGS)
SUBSTRING_SETS.append(ARM_SUBSTRINGS)
SUBSTRING_SETS.append(LEG_SUBSTRINGS)
SUBSTRING_SETS.append(FOOT_SUBSTRINGS)
SUBSTRING_SETS.append(TORSO_SUBSTRINGS)
SUBSTRING_SETS.append(RIB_SUBSTRINGS)
SUBSTRING_SETS.append(HEAD_SUBSTRINGS)
SUBSTRING_SETS.append(ROOT_SUBSTRINGS)
SUBSTRING_SETS.append(TARGET_SUBSTRINGS)

MAP_SUBSTRING_SET_TO_ARMATURELAYER = {}
MAP_SUBSTRING_SET_TO_ARMATURELAYER[(ARM_SUBSTRINGS,'L')] = AL_ARM_L
MAP_SUBSTRING_SET_TO_ARMATURELAYER[(HAND_SUBSTRINGS,'L')] = AL_HAND_L
MAP_SUBSTRING_SET_TO_ARMATURELAYER[(LEG_SUBSTRINGS,'L')] = AL_LEG_L
MAP_SUBSTRING_SET_TO_ARMATURELAYER[(FOOT_SUBSTRINGS,'L')] = AL_FOOT_L
MAP_SUBSTRING_SET_TO_ARMATURELAYER[(RIB_SUBSTRINGS,'L')] = AL_RIB_L

MAP_SUBSTRING_SET_TO_ARMATURELAYER[(TORSO_SUBSTRINGS,None)] = AL_SPINE
MAP_SUBSTRING_SET_TO_ARMATURELAYER[(TORSO_SUBSTRINGS,'')] = AL_SPINE
MAP_SUBSTRING_SET_TO_ARMATURELAYER[(TORSO_SUBSTRINGS,'L')] = AL_SPINE
MAP_SUBSTRING_SET_TO_ARMATURELAYER[(TORSO_SUBSTRINGS,'R')] = AL_SPINE

MAP_SUBSTRING_SET_TO_ARMATURELAYER[(ROOT_SUBSTRINGS,None)] = AL_ROOT
MAP_SUBSTRING_SET_TO_ARMATURELAYER[(ROOT_SUBSTRINGS,'')] = AL_ROOT

MAP_SUBSTRING_SET_TO_ARMATURELAYER[(HEAD_SUBSTRINGS,None)] = AL_HEAD
MAP_SUBSTRING_SET_TO_ARMATURELAYER[(HEAD_SUBSTRINGS,'')] = AL_HEAD
MAP_SUBSTRING_SET_TO_ARMATURELAYER[(HEAD_SUBSTRINGS,'L')] = AL_HEAD
MAP_SUBSTRING_SET_TO_ARMATURELAYER[(HEAD_SUBSTRINGS,'R')] = AL_HEAD

MAP_SUBSTRING_SET_TO_ARMATURELAYER[(ARM_SUBSTRINGS,'R')] = AL_ARM_R
MAP_SUBSTRING_SET_TO_ARMATURELAYER[(HAND_SUBSTRINGS,'R')] = AL_HAND_R
MAP_SUBSTRING_SET_TO_ARMATURELAYER[(LEG_SUBSTRINGS,'R')] = AL_LEG_R
MAP_SUBSTRING_SET_TO_ARMATURELAYER[(FOOT_SUBSTRINGS,'R')] = AL_FOOT_R
MAP_SUBSTRING_SET_TO_ARMATURELAYER[(RIB_SUBSTRINGS,'R')] = AL_RIB_R

MAP_SUBSTRING_SET_TO_ARMATURELAYER[(TARGET_SUBSTRINGS,'L')] = AL_TARGET
MAP_SUBSTRING_SET_TO_ARMATURELAYER[(TARGET_SUBSTRINGS,'R')] = AL_TARGET

FINGER_TOE_RIGIDITY = 3

WIDGET_HAND = 'Widget-Hand'
WIDGET_SOLE = 'Widget-Sole'
WIDGET_BONE = 'Widget-Bone'
WIDGET_ROOT = 'Widget-Root'
WIDGET_EYE_TARGET = 'Widget-Eye-Target'
WIDGET_SPHERE = 'Widget-Sphere'
WIDGET_CUBE = 'Widget-Cube'
WIDGET_PAD = 'Widget-Pad'
WIDGET_CIRCLE = 'Widget-Circle'
WIDGET_FOOT = 'Widget-Foot'

class WidgetData():
    def __init__(self,vertices=[],edges=[],faces=[]):
        self.vertices = vertices
        self.edges = edges
        self.faces = faces
        self.subsurface_levels = 0
        self.ob = None

    def create(self,name):
        mesh = bpy.data.meshes.new(name + "-Mesh")
        ob = bpy.data.objects.new(name,mesh)
        ob.data.from_pydata(self.vertices,self.edges,self.faces)
        ob.data.update()
        
        if self.subsurface_levels > 0:
            ob.modifiers.new(name="Subsurface",type='SUBSURF').levels = self.subsurface_levels
        
        self.ob = ob
        return ob
    
def widgetdata_circle(radius):
    widgetdata = WidgetData()
    vertices = [(0.7071068286895752, 2.980232238769531e-07, -0.7071065306663513), (0.8314696550369263, 2.980232238769531e-07, -0.5555699467658997), (0.9238795042037964, 2.682209014892578e-07, -0.3826831877231598), (0.9807852506637573, 2.5331974029541016e-07, -0.19509011507034302), (1.0, 2.365559055306221e-07, 1.6105803979371558e-07), (0.9807853698730469, 2.2351741790771484e-07, 0.19509044289588928), (0.9238796234130859, 2.086162567138672e-07, 0.38268351554870605), (0.8314696550369263, 1.7881393432617188e-07, 0.5555704236030579), (0.7071068286895752, 1.7881393432617188e-07, 0.7071070075035095), (0.5555702447891235, 1.7881393432617188e-07, 0.8314698934555054), (0.38268327713012695, 1.7881393432617188e-07, 0.923879861831665), (0.19509008526802063, 1.7881393432617188e-07, 0.9807855486869812), (-3.2584136988589307e-07, 1.1920928955078125e-07, 1.000000238418579), (-0.19509072601795197, 1.7881393432617188e-07, 0.9807854294776917), (-0.3826838731765747, 1.7881393432617188e-07, 0.9238795638084412), (-0.5555707216262817, 1.7881393432617188e-07, 0.8314695358276367), (-0.7071071863174438, 1.7881393432617188e-07, 0.7071065902709961), (-0.8314700126647949, 1.7881393432617188e-07, 0.5555698871612549), (-0.923879861831665, 2.086162567138672e-07, 0.3826829195022583), (-0.9807853698730469, 2.2351741790771484e-07, 0.1950896978378296), (-1.0, 2.365559907957504e-07, -7.290432222362142e-07), (-0.9807850122451782, 2.5331974029541016e-07, -0.195091113448143), (-0.9238790273666382, 2.682209014892578e-07, -0.38268423080444336), (-0.831468939781189, 2.980232238769531e-07, -0.5555710196495056), (-0.7071058750152588, 2.980232238769531e-07, -0.707107424736023), (-0.555569052696228, 2.980232238769531e-07, -0.8314701318740845), (-0.38268208503723145, 2.980232238769531e-07, -0.923879861831665), (-0.19508881866931915, 2.980232238769531e-07, -0.9807853102684021), (1.6053570561780361e-06, 2.980232238769531e-07, -0.9999997615814209), (0.19509197771549225, 2.980232238769531e-07, -0.9807847142219543), (0.3826850652694702, 2.980232238769531e-07, -0.9238786101341248), (0.5555717945098877, 2.980232238769531e-07, -0.8314683437347412)]
    widgetdata.edges = [(28, 12), (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9), (9, 10), (10, 11), (11, 12), (12, 13), (13, 14), (14, 15), (15, 16), (16, 17), (17, 18), (18, 19), (19, 20), (20, 21), (21, 22), (22, 23), (23, 24), (24, 25), (25, 26), (26, 27), (27, 28), (28, 29), (29, 30), (30, 31), (0, 31)]
    widgetdata.faces = []
    widgetdata.vertices = [(v[0]*radius,v[1]*radius,v[2]*radius) for v in vertices]
    return widgetdata

def widgetdata_pad(width=1.0,length=1.0,mid=.5):
    widgetdata = WidgetData()
    hw = width/2
    widgetdata.vertices = [(-hw, 0.0, 0.0), (-hw, mid, 0.0), (-hw, length, 0.0), (hw, length, 0.0), (hw, mid, 0.0), (hw, 0.0, 0.0)]
    widgetdata.edges = [(0,1),(1,2),(2,3),(3,4),(4,5),(5,0)]
    widgetdata.faces = []
    widgetdata.subsurface_levels = 2
    return widgetdata



    


    

def pydata_get_edges(obj):
    return [(edge.vertices[0],edge.vertices[1]) for edge in obj.data.edges]

def pydata_get_vertices(obj):
    return [(v.co[0],v.co[1],v.co[2]) for v in obj.data.vertices]

def pydata_get_faces(obj):
    return [[v for v in p.vertices] for p in obj.data.polygons]

_metabone_root = None
_recognized_suffix_letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
_recognized_suffix_delimiters = ('_','.','-',' ')



OB_LAYERS_WIDGET = [False if i < 19 else True for i in range(20)]

def apply_rig_starting_layers(obj):
    obj.data.layers = [True if i in AL_START else False for i in range(32)]

def draw_rig_layers(layout):
    data = bpy.context.object.data
    
    
    box1 = layout.box()
    box1.label("Animation Bones")
    box1.prop(data,'layers',toggle=True,index=AL_ANIMATABLE,text="All")

    top = box1.column(align=True)
    
    top.prop(data,'layers',toggle=True,index=AL_HEAD,text="Head")
    top.prop(data,'layers',toggle=True,index=AL_SPINE,text="Spine")
    top.prop(data,'layers',toggle=True,index=AL_ROOT,text="Root")
    
    middle = box1.row()
    
    col = middle.column(align=True)
    col.label("Left")
    col.prop(data,'layers',toggle=True,index=AL_ARM_L,text="Arm")
    col.prop(data,'layers',toggle=True,index=AL_HAND_L,text="Fingers")
    col.prop(data,'layers',toggle=True,index=AL_LEG_L,text="Leg")
    col.prop(data,'layers',toggle=True,index=AL_FOOT_L,text="Toes")
    col.prop(data,'layers',toggle=True,index=AL_RIB_L,text="Ribs")

    col = middle.column(align=True)
    col.label("Right")
    col.prop(data,'layers',toggle=True,index=AL_ARM_R,text="Arm")
    col.prop(data,'layers',toggle=True,index=AL_HAND_R,text="Fingers")
    col.prop(data,'layers',toggle=True,index=AL_LEG_R,text="Leg")
    col.prop(data,'layers',toggle=True,index=AL_FOOT_R,text="Toes")
    col.prop(data,'layers',toggle=True,index=AL_RIB_R,text="Ribs")
  
    box2 = layout.box()
    box2.label("Other")
    col = box2.column(align=True)
    col.prop(data,'layers',toggle=True,index=AL_TARGET,text="Targets")
    col.prop(data,'layers',toggle=True,index=AL_DEFORMER,text="Deformers")
    col.prop(data,'layers',toggle=True,index=AL_MECHANICAL,text="Mechanical")
    col.prop(data,'layers',toggle=True,index=AL_BEPUIK_BONE,text="BEPUik Bones")

def split_suffix(s):
    possible_suffix = s[-2:]
    if possible_suffix[0] in _recognized_suffix_delimiters and possible_suffix[1] in _recognized_suffix_letters:
        return (s[:-2],possible_suffix)
    
    return (s,'')

def get_suffix_letter(s):
    presuffix, suffix = split_suffix(s)

    if suffix:
        return suffix[1]
    
    return None

_blender_struct_attrs = {item[0] for item in inspect.getmembers(bpy.types.Struct)}

def get_rig_relevant_attr_names(ob):
    global _blender_struct_attrs
    return {item[0] for item in inspect.getmembers(ob) 
            if item[0] not in _blender_struct_attrs | {'__qualname__','__weakref__','__dict__'} 
            if not hasattr(getattr(ob,item[0]),'__call__')}

class MetaBlenderConstraint():
    def __init__(self,type,name=None):
        self.type = type
        self.name = name
    
    def apply_data_to_pchan(self,pbone):
        constraint = pbone.constraints.new(type=self.type)
        
        excluded_attr_names = set(['name','type','connection_a','connection_b','subtarget','rigidity'])    
        angle_attr_names = set(['max_swing','max_twist'])
        
        self_attr_names = get_rig_relevant_attr_names(self)
        self_attr_names -= excluded_attr_names
        
        constraint.name = self.name
        
        if constraint.is_bepuik:
            #we know that the bepuik constraint's object targets should always be the context object
            constraint.connection_target = bpy.context.object
            
            #the pchan containing the constraint is always considered connection a
            #therefore the connection subtarget is always connection b
            constraint.connection_subtarget = self.connection_b.name
            
            if hasattr(self,'rigidity'):
                constraint.bepuik_rigidity = self.rigidity        
        
            for attr_name in self_attr_names:
                dodefault = False
                val = getattr(self,attr_name)
                typeofval = type(val)
#                print(pbone,constraint,attr_name,val)
                if attr_name in angle_attr_names:
                    #rig generation code always uses degrees, so we need to convert
                    setattr(constraint,attr_name,math.radians(val))
                elif typeofval is MetaBone:
                    '''
                    Blender constraints use a string to point to bones, but this
                    rig generation code doesn't use strings, it uses a Metabone object.
                    We can get the needed blender bone name from the metabone.name attribute
                    
                    Also, the rig generation code is concise, and leaves off the _subtarget suffix,
                    so it has to be reapplied to set the proper blender python attribute
                    '''
                    setattr(constraint,attr_name + "_subtarget",val.name)
                elif typeofval is list or typeofval is tuple:
                    mytuple = val
                    
                    if type(val[0]) == MetaBone:
                        val1type = type(val[1])
                        
                        if val1type == str: 
                            #axis using bone as reference
                            setattr(constraint,attr_name + "_target",bpy.context.object)
                            setattr(constraint,attr_name + "_subtarget",val[0].name)
                            setattr(constraint,attr_name,val[1])
                        elif val1type == int or val1type == float:
                            #point using bone as reference
                            setattr(constraint,attr_name + "_target",bpy.context.object)
                            setattr(constraint,attr_name + "_subtarget",val[0].name)
                            setattr(constraint,attr_name + "_head_tail",val[1])
                        else:
                            dodefault = True
                    else:
                        dodefault = True
                else:
                    dodefault = True        
                    
                if dodefault:
                    try:
                        setattr(constraint,attr_name,val)
                    except:
                        raise Exception("""Don't know what to do with:
                                            pbone:%s
                                            constraint:%s
                                            attr:%s
                                            val:%s""" % (pbone.name,constraint.name,attr_name,val))
                        
        else:
            constraint.target = bpy.context.object
            constraint.subtarget = self.connection_b.name
                
            for attr_name in self_attr_names:
                setattr(constraint,attr_name,getattr(self,attr_name))        

def safesetattr(ob,attr,val):
    if isinstance(val,Vector):
        val = val.copy()
        
    setattr(ob,attr,val)    

def vector_is_zero(vec,epsilon=0.000001):
    for v in vec:
        if abs(v) > epsilon:
            return False
        
    return True
            
def Vector4_to_Vector3(v4):
    return Vector((v4[0],v4[1],v4[2]))

def Vector3_to_Vector4(v3):
    return Vector((v3[0],v3[1],v3[2],0))

''' A MetaBone object stores common values between pchans, ebones, and metabones, and helps control how information is copied between them '''                
class MetaBone():

    ebone_attrs = { 'head':Vector((0,0,0)),
                    'tail':Vector((0,1,0)),
                    'roll':0,
                    'tail_radius':None,
                    'head_radius':None,
                    'bbone_x':None,
                    'bbone_z':None,
                    'bbone_in':0,
                    'bbone_out':0,
                    'bbone_segments':1,
                    'use_connect':False,
                    'use_deform':False,
                    'use_envelope_multiply':False,
                    'envelope_distance':None}

    pchan_attrs = { 'use_bepuik':False,
                    'use_bepuik_always_solve':False,
                    'bepuik_ball_socket_rigidity':0,
                    'bepuik_rotational_heaviness':2.5,
                    'lock_location':(False,False,False),
                    'lock_rotation':(False,False,False),
                    'lock_rotation_w':False,
                    'lock_scale':(False,False,False),
                    'custom_shape':None,
                    'rotation_mode':'QUATERNION'}
    
    #can only be accessed thru the bone context for some strange reason
    bone_attrs = {'show_wire':False}
    
    special_attrs = {'align_roll':Vector((0,0,1)),
                     'parent':None}
    
    all_attrs = dict(list(ebone_attrs.items()) + 
                     list(pchan_attrs.items()) +
                     list(bone_attrs.items()) +
                     list(special_attrs.items()))
        
    def __init__(self,name,metabone=None,transform=None):
        self.meta_blender_constraints = []
        
        if metabone:
            for attr in MetaBone.all_attrs.keys():
                safesetattr(self,attr,getattr(metabone,attr))
        else:
            for attr, val in MetaBone.all_attrs.items():
                safesetattr(self,attr,val)
                       
        if transform:
            self.head = transform * self.head
            self.tail = transform * self.tail
            self.align_roll = transform.to_3x3() * self.align_roll

                   
        self.name = name
        
    def copy_pchan_data(self,pchan):
        for attr in MetaBone.pchan_attrs.keys():                
            safesetattr(self,attr,getattr(pchan,attr))
        
        for attr in MetaBone.bone_attrs.keys():
            safesetattr(self,attr,getattr(pchan.bone,attr))
            
    def copy_ebone_data(self,ebone):
        for attr in MetaBone.ebone_attrs.keys():                
            safesetattr(self,attr,getattr(ebone,attr))
            
        self.align_roll = ebone.z_axis.copy()

    def is_valid(self):
        return self.length() > 0.0001

    def create_ebone(self,ob):
        if not self.is_valid():
            return None
        
        length = (self.tail - self.head).length
        ebone = ob.data.edit_bones.new(name=self.name)
        
        
        
        if not self.head_radius:
            self.head_radius = length / 10
            
        if not self.tail_radius:
            self.tail_radius = length / 10
        
        if not self.bbone_x:
            self.bbone_x = length / 10
            
        if not self.bbone_z:
            self.bbone_z = length / 10
            
        if not self.envelope_distance:
            self.envelope_distance = self.head_radius * 15
        
        for attr in MetaBone.ebone_attrs.keys():
            val = getattr(self,attr)
            safesetattr(ebone,attr,val)

        ebone.align_roll(self.align_roll)
        
        return ebone
                
    def apply_data_to_pchan(self,pchan):
        for attr in MetaBone.pchan_attrs.keys():
            safesetattr(pchan,attr,getattr(self,attr))
        
        for attr in MetaBone.bone_attrs.keys():
            safesetattr(pchan.bone,attr,getattr(self,attr))
            
    def apply_data_to_pchan_constraints(self,pchan):
        for meta_blender_constraint in self.meta_blender_constraints:
            if meta_blender_constraint.name in pchan.constraints:
                continue
        
            meta_blender_constraint.apply_data_to_pchan(pchan)
            
    def new_meta_blender_constraint(self,type,target,name=None):
        if not name:
            name = "%s_%s" % (type.lower(),len(self.meta_blender_constraints)+1)
            
        mbc = MetaBlenderConstraint(type,name)
        mbc.connection_a = self
        mbc.connection_b = target
        self.meta_blender_constraints.append(mbc)
        return mbc
    
    @classmethod
    def from_ebone(cls,ebone):
        metabone = cls(name=ebone.name)
        
        metabone.copy_ebone_data(ebone)
        
        return metabone
    
    def y_axis(self):
        v = (self.tail - self.head)
        assert not vector_is_zero(v), "%s has same tail and head" % self.name
        return v.normalized()
    
    def x_axis(self):
        y = self.y_axis()
        ar = self.align_roll
            
        c = y.cross(ar)
        if vector_is_zero(c):
            c = y.cross(Vector((ar[0],-ar[2],ar[1])))
            
        return c.normalized()
        
    def z_axis(self):
        return self.x_axis().cross(self.y_axis()).normalized()
    
    def matrix(self):
        m = Matrix.Identity(4)
        
        m.col[0] = Vector3_to_Vector4(self.x_axis())
        m.col[1] = Vector3_to_Vector4(self.y_axis())
        m.col[2] = Vector3_to_Vector4(self.z_axis())
        m.col[3] = Vector3_to_Vector4(self.head)
        m.col[3][3] = 1.0
        
        m.normalize()
        
        return m
    
    def length(self):
        return (self.tail - self.head).length

def suffixed(name,suffixletter):
    if suffixletter:
        return "%s.%s" % (name,suffixletter)
    else:
        return name



class MetaBoneDict(dict):
    def __init__(self, *args):
        dict.__init__(self, args)

    def __getitem__(self, key):
        if key in self:
            return dict.__getitem__(self, key)
        else:
            return None

    def __setitem__(self, key, val):
        if key in self:
            raise Exception("Cannot add metabone with name %s! Already exists!" % key)
        dict.__setitem__(self, key, val)
        
    def new_bone(self,name,metabone=None,transform=None):
        self[name] = MetaBone(name, metabone, transform)
        return self[name]
    
    def new_bone_by_fraction(self,name,source_metabone,start_fraction=0,end_fraction=1):
        new_bone = self.new_bone(name=name)
        new_bone.name = "%s-%s" % (source_metabone.name,name)
        start_point = source_metabone.head
        end_point = source_metabone.tail
        
        local_vector = (end_point - start_point)
        local_start = local_vector * start_fraction
        local_end =   local_vector * end_fraction
        new_bone.head = start_point + local_start
        new_bone.tail = start_point + local_end
        
        new_bone.align_roll = source_metabone.align_roll
        return new_bone

    @classmethod
    def from_bakedata(cls,bakedata_list):
        destination_metabones = cls()
        
        for bake in bakedata_list:
            for source_name, source_metabone in bake.metabones.items():
                destination_metabones.new_bone(suffixed(source_name, bake.suffixletter),source_metabone,bake.transform)
        
        #the destination_metabone.parent attribute still point to metabones in the source metabone group, so 
        #we need to update them to be pointing to the metabones in the destination group         
        for bake in bakedata_list:
            for source_name, source_metabone in bake.metabones.items():
                destination_metabone = destination_metabones[suffixed(source_name, bake.suffixletter)]
                
                if destination_metabone.parent:
                    destination_metabone.parent = destination_metabones[suffixed(destination_metabone.parent.name, bake.suffixletter)]
    
        return destination_metabones
    
    
    
    @classmethod
    def from_transform_length_pairs(cls,name,transform_length_pairs):
        metabones = cls()
        
        num_id = 1
        prev_bone = None
        t = Matrix.Identity(4)
        for transform, length in transform_length_pairs:
            t = t * transform
            new_bone = metabones.new_bone("%s-%s" % (name,num_id))
            new_bone.head = Vector4_to_Vector3(t.col[3])
            new_bone.align_roll = Vector4_to_Vector3(t.col[2])
            t = t * Matrix.Translation(Vector((0,length,0)))
            new_bone.tail = Vector4_to_Vector3(t.col[3])
            
            if prev_bone:
                new_bone.parent = prev_bone
                
                if (prev_bone.tail - new_bone.head).length < .0001:
                    new_bone.use_connect = True
                else:
                    new_bone.use_connect = False
            else:
                new_bone.use_connect = False
            
                                
            prev_bone = new_bone
            
            num_id+=1
            
        return metabones
    
    @classmethod
    def from_angle_length_pairs(cls,name,angle_length_pairs):
        transform_length_pairs = []
        
        for angle, length in angle_length_pairs:
            transform_length_pairs.append((Matrix.Rotation(angle,4,'X'),length))
            
        return cls.from_transform_length_pairs(name, transform_length_pairs)
            
    
    @classmethod
    def from_ob(cls,ob):
        assert ob.type == 'ARMATURE'
        assert ob.mode == 'POSE'
        assert ob == bpy.context.object

        metabones = MetaBoneDict()     
    
        for pchan in ob.pose.bones:
            metabone = metabones.new_bone(pchan.name)
            metabone.copy_pchan_data(pchan)
            
        bpy.ops.object.mode_set(mode='EDIT',toggle=False)
        
        for name, metabone in metabones.items():
            ebone = ob.data.edit_bones[name]
            metabone.copy_ebone_data(ebone)
            
            if ebone.parent:
                metabones[ebone.name].parent = metabones[ebone.parent.name]
                
        return metabones
        
    def to_ob(self,ob):
        assert bpy.context.object == ob
        assert ob.type == 'ARMATURE'
        assert ob.mode == 'EDIT'
        
        ebone_creators = []
        
        for metabone in self.values():
            if metabone.name not in ob.data.edit_bones:
                if metabone.create_ebone(ob):
                    ebone_creators.append(metabone)
                
        
        for metabone in ebone_creators:
            ebone = ob.data.edit_bones[metabone.name]
            if metabone.parent and metabone.parent.is_valid():
                ebone.parent = ob.data.edit_bones[metabone.parent.name]
                
        bpy.ops.object.mode_set(mode='POSE')
        
        for metabone in ebone_creators:
            pchan = ob.pose.bones[metabone.name]
            metabone.apply_data_to_pchan(pchan)
            
        for metabone in self.values():
            if metabone.is_valid():
                pchan = ob.pose.bones[metabone.name]
                metabone.apply_data_to_pchan_constraints(pchan)
                
    def get_args_subset(self,local_names,suffixletter):
        arm_metabones = {}
        for local_name in local_names:
            name = "%s.%s" % (local_name,suffixletter)
            if name not in self:
                name = local_name
            
            assert name in self, "%s couldn't be found in metabones!" % name
            
            arm_metabones[local_name] = self[name]
        return arm_metabones            
   
class MetaBonesBakeData():
    def __init__(self,metabones,transform=None,suffixletter=""):
        self.metabones = metabones
        self.suffixletter = suffixletter
        self.transform = transform
        
def meta_create_full_body(ob,num_fingers,num_toes,foot_width,wrist_width,wrist_yaw,wrist_pitch,wrist_roll,use_thumb,finger_curl,toe_curl,finger_splay,thumb_splay,thumb_tilt,shoulder_head_vec,shoulder_tail_vec,elbow_vec,wrist_vec,spine_start_vec,spine_lengths,upleg_vec, knee_vec, ankle_vec, toe_vec, eye_center, eye_radius, chin_vec, jaw_vec, use_simple_toe):
    mat_larm = Matrix.Identity(4)
    
    flip = Matrix.Scale(-1,4,Vector((1,0,0)))
    mat_lleg = Matrix.Identity(4)
    mat_rleg = flip * mat_lleg
    mat_rarm = flip * mat_larm
    
    arm_meta = meta_init_arm(shoulder_head_vec, shoulder_tail_vec, elbow_vec, wrist_vec)
    leg_meta = meta_init_leg(upleg_vec, knee_vec, ankle_vec, toe_vec, foot_width)
    spine_meta = meta_init_spine(spine_start_vec, spine_lengths)
    fingers_meta = meta_init_fingers(num_fingers, finger_curl, wrist_width, use_thumb, finger_splay, thumb_splay, thumb_tilt)
    toes_meta = meta_init_toes(num_toes,toe_curl,foot_width,use_simple_toe)
    face_meta = meta_init_face(eye_center, eye_radius, chin_vec, jaw_vec)
    
    mat_arm_to_fingers = Matrix.Translation(Vector((arm_meta["loarm"].tail))).to_4x4()
    mat_leg_to_toes = Matrix.Translation(Vector((leg_meta["foot"].tail))).to_4x4()
    
    mat_fingers = Matrix.Rotation(wrist_yaw,4,'Z') * Matrix.Rotation(wrist_pitch,4,'X') * Matrix.Rotation(wrist_roll,4,'Y')
    mat_toes = Matrix.Rotation(math.pi,4,'Z')
    
    bakedata_list = []
    bakedata_list.append(MetaBonesBakeData(arm_meta, mat_larm, 'L'))
    bakedata_list.append(MetaBonesBakeData(arm_meta, mat_rarm, 'R'))
    bakedata_list.append(MetaBonesBakeData(leg_meta, mat_lleg, 'L'))
    bakedata_list.append(MetaBonesBakeData(leg_meta, mat_rleg, 'R'))
    bakedata_list.append(MetaBonesBakeData(spine_meta, Matrix.Identity(4)))
    bakedata_list.append(MetaBonesBakeData(face_meta,Matrix.Identity(4)))
    bakedata_list.append(MetaBonesBakeData(fingers_meta, mat_larm * mat_arm_to_fingers * mat_fingers, 'L'))
    bakedata_list.append(MetaBonesBakeData(fingers_meta, mat_rarm * mat_arm_to_fingers * mat_fingers, 'R'))
    bakedata_list.append(MetaBonesBakeData(toes_meta,mat_lleg * mat_leg_to_toes * mat_toes, 'L'))
    bakedata_list.append(MetaBonesBakeData(toes_meta,mat_rleg * mat_leg_to_toes * mat_toes, 'R'))
    
#    testleft = MetaBoneDict()
#    b = testleft.new_bone("test")
#    b.head = Vector((0,0,0))
#    b.tail = Vector((1,0,0))
#    
#    bakedata_list.append(MetaBonesBakeData(testleft,Matrix.Identity(4) * mat_fingers,'L'))
#    bakedata_list.append(MetaBonesBakeData(testleft,flip * mat_fingers,'R'))

    combined_metabones = MetaBoneDict.from_bakedata(bakedata_list)
    combined_metabones.to_ob(ob)
    
    ob.data.layers = [True]*32
    ob.bepuik_autorig.is_meta_armature = True
    ob.bepuik_autorig.use_thumb = use_thumb
    ob.bepuik_autorig.use_simple_toe = use_simple_toe

def meta_init_faceside(eye_center,eye_radius):
    metabones = MetaBoneDict()
    
    b = metabones.new_bone("eye")
    b.head = eye_center.copy()
    b.tail = eye_center + Vector((0,-1*eye_radius,0))
    
    return metabones

def meta_init_face(eye_center,eye_radius,chin_vec,jaw_vec):
    face_side_meta = meta_init_faceside(eye_center, eye_radius)
    
    bakedata_list = []
    bakedata_list.append(MetaBonesBakeData(face_side_meta, Matrix.Identity(4), 'L'))
    bakedata_list.append(MetaBonesBakeData(face_side_meta, Matrix.Scale(-1,4,Vector((1,0,0))), 'R'))
    combined_metabones = MetaBoneDict.from_bakedata(bakedata_list)
    
    b = combined_metabones.new_bone('jaw')
    b.head = jaw_vec.copy()
    b.tail = chin_vec.copy()
    b.use_connect = False
    
    return combined_metabones
        
def meta_init_spine(spine_start_vec,spine_lengths):
    mbg = MetaBoneDict()
    
    bone_names = ["hips","spine","chest","neck","head"]
    
    v = spine_start_vec.copy()
    
    def prev_bone(i):
        if i - 1 >= 0:
            return mbg[bone_names[i-1]]
        
        return None
        
    
    for i in range(len(spine_lengths)):
        new_bone = mbg.new_bone(bone_names[i])
        new_bone.head = v.copy()
        v += Vector((0,0,spine_lengths[i]))
        new_bone.tail = v.copy()
        new_bone.align_roll= Vector((0,-1,0))
        new_bone.parent = prev_bone(i)
        if new_bone.parent:
            new_bone.use_connect = True

    chest_length = (mbg["chest"].tail - mbg["chest"].head).length
    rib_head_z = mbg["chest"].head[2] + (chest_length * .2)
    rib_tail_z = mbg["chest"].tail[2] - (chest_length * .4)

    b = mbg.new_bone("ribs.L")
    b.head = Vector((0.074,-0.086,rib_head_z))
    b.tail = Vector((0.102,-0.024,rib_tail_z))
    b.align_roll = Vector((0,-1,0))
    b.parent = mbg["chest"]
    
    b = mbg.new_bone("ribs.R")
    b.head = Vector((-0.074,-0.086,rib_head_z))
    b.tail = Vector((-0.102,-0.024,rib_tail_z))
    b.align_roll = Vector((0,-1,0))
    b.parent = mbg["chest"]

    return mbg

def meta_init_arm(shoulder_head_vec,shoulder_tail_vec,elbow_vec,wrist_vec):
    mbg = MetaBoneDict()
     
    arm_vec = wrist_vec - shoulder_tail_vec

    arm_up_vec = arm_vec.cross(Vector((0,1,0)))
   

    new_elbow_vec = (elbow_vec[0]*arm_vec) + shoulder_tail_vec
    
    new_elbow_vec[1] += (elbow_vec[1] * arm_vec.length)
    
    shoulder = mbg.new_bone("shoulder")
    shoulder.use_deform = True
    shoulder.head = shoulder_head_vec.copy()
    shoulder.tail = shoulder_tail_vec.copy()
    shoulder.use_bepuik_ball_socket_rigidity = BEPUIK_BALL_SOCKET_RIGIDITY_DEFAULT
    
    uparm = mbg.new_bone("uparm")
    uparm.head = shoulder_tail_vec.copy()
    uparm.tail = new_elbow_vec.copy()
    uparm.parent = shoulder
    uparm.align_roll = arm_up_vec.copy()
    uparm.use_connect = True
    
    loarm = mbg.new_bone("loarm")
    loarm.head = new_elbow_vec.copy()
    loarm.tail = wrist_vec.copy()
    loarm.parent = uparm
    loarm.align_roll = arm_up_vec.copy()
    loarm.use_connect = True
    
    return mbg
        
class Phalange():
    def __init__(self,name,curl,lengths,length_scale):
        self.name = name
        self.curl = curl
        self.lengths = lengths
        self.lengths_scale = length_scale
        
    def create_metabonedict(self):
        angle_length_pairs = []
        angle_length_pairs.append((0,self.lengths[0]*self.lengths_scale))
        for i in range(1,len(self.lengths)):
            angle_length_pairs.append((self.curl,self.lengths[i]*self.lengths_scale))
            
        return MetaBoneDict.from_angle_length_pairs(self.name, angle_length_pairs)

class Finger(Phalange):
    def __init__(self,name, curl,lengths,length_scale,is_thumb=False):
        super().__init__(name,curl,lengths,length_scale)
        self.is_thumb = is_thumb
        
class Toe(Phalange):
    def __init__(self,name,curl,lengths,length_scale):
        super().__init__(name,curl,lengths,length_scale)

def meta_init_fingers(num_fingers,finger_curl,wrist_width,use_thumb,finger_splay,thumb_splay,thumb_tilt):
    
    thumb_segment_lengths = [.024,.0376,.040,.0339]
    finger_segment_lengths = [.089,.0318,.02632,.0247]
    
    #from thumb to pinky
    finger_scales = [.7,.9,1,.9,.7]
    
    fingers = []
    
    if use_thumb:
        segment_lengths = thumb_segment_lengths
    else:
        segment_lengths = finger_segment_lengths
        
    fingers.append(Finger("finger1", finger_curl, segment_lengths, finger_scales[0],use_thumb))
    
    for finger_index in range(1,num_fingers):
        fingers.append(Finger("finger%s" % (finger_index+1), finger_curl, finger_segment_lengths, finger_scales[finger_index]))
    
    fingers_bakedata = []
    
    if num_fingers > 1:
        wrist_point = Vector((wrist_width/2,0,0))
        wrist_delta = wrist_width/(num_fingers-1)
    else:
        wrist_width = 0    
        wrist_delta = 0
        wrist_point = Vector((0,0,0))
    
    for finger in fingers:
        metabones = finger.create_metabonedict()
        
        if wrist_width > 0:
            wrist_factor = wrist_point[0]/wrist_width/2
        else:
            wrist_factor = wrist_point[0]
        
        if finger.is_thumb:
            transform = Matrix.Translation(wrist_point) * Matrix.Rotation(math.radians(90),4,'Y') * Matrix.Rotation(thumb_splay,4,'X') * Matrix.Rotation(thumb_tilt,4,'Z') 
        else:
            transform = Matrix.Translation(wrist_point) * Matrix.Rotation(wrist_factor*finger_splay,4,'Z')
        
        fingers_bakedata.append(MetaBonesBakeData(metabones,transform))
        wrist_point[0] -= wrist_delta
        
    return MetaBoneDict.from_bakedata(fingers_bakedata)

def meta_init_toes(num_toes,toe_curl,foot_width,use_simple_toe=True):
    
    big_toe_lengths = [.02955,.02653]
    little_toe_lengths = [.028,.01628,.015]

    if use_simple_toe:
        big_toe_lengths = [sum(big_toe_lengths),]
        little_toe_lengths = [sum(little_toe_lengths),]
    
    #from bigtoe to pinky toe
    toe_scales = []
    scale = 1
    for i in range(num_toes):
        toe_scales.append(scale)
        scale *= .80
    
    toes = []
        
    toes.append(Toe("toe1", toe_curl, big_toe_lengths, toe_scales[0]))
    
    for toe_index in range(1,num_toes):
        toes.append(Toe("toe%s" % (toe_index+1), toe_curl, little_toe_lengths, toe_scales[toe_index]))
    
    toes_bakedata = []
    
    if num_toes > 1:
        foot_point = Vector((foot_width/2,0,0))
        foot_delta = foot_width/(num_toes-1)
    else:
        foot_width = 0    
        foot_delta = 0
        foot_point = Vector((0,0,0))
    
    for toe in toes:
        metabones = toe.create_metabonedict()
        
        transform = Matrix.Translation(foot_point)
        
        toes_bakedata.append(MetaBonesBakeData(metabones,transform))
        foot_point[0] -= foot_delta
        
    return MetaBoneDict.from_bakedata(toes_bakedata)

def meta_init_leg(upleg_vec, knee_vec, ankle_vec, toe_vec, foot_width):
    mbg = MetaBoneDict()

    upleg = mbg.new_bone("upleg")
    upleg.use_deform = True
    upleg.head = upleg_vec.copy()
    upleg.tail = knee_vec.copy()
    upleg.align_roll = Vector((0,-1,0))
    
    loleg = mbg.new_bone("loleg")
    loleg.head = upleg.tail.copy()
    loleg.tail = ankle_vec.copy()
    loleg.parent = upleg
    loleg.align_roll = Vector((0,-1,0))
    loleg.use_connect = True
    
    foot = mbg.new_bone("foot")
    foot.head = loleg.tail.copy()    
    foot.tail = toe_vec.copy()
    foot.parent = loleg
    foot.bepuik_ball_socket_rigidity = 1000
    foot.use_connect = True
    

    
    loleg_vec = (loleg.tail - loleg.head)
    foot_vec = (foot.tail - foot.head)
    vec_to_heel = loleg_vec.normalized() * ((loleg_vec.length + foot_vec.length) * 2) 
    
    foottarget_a = geometry.intersect_line_plane(loleg.head,loleg.head + vec_to_heel,foot.tail,Vector((0,0,1)))
    foottarget_b = foot.tail.copy()
    
    if foottarget_a:
        foottarget_length = foot_vec.length * 1.1
        ball_to_heel_dir = (foottarget_a - foottarget_b).normalized()
        
        foottarget = mbg.new_bone("foot-target")
        foottarget.head = foot.tail.copy() + ball_to_heel_dir * foottarget_length
        foottarget.tail = foot.tail.copy()
        
        foot_width_bone = mbg.new_bone("foot-width")
        foot_width_bone.head = foottarget.head.copy()
        foot_width_bone.head += foottarget.y_axis() * foottarget.length()
        foot_width_bone.head += foottarget.x_axis() * foot_width /2
        foot_width_bone.tail = foot_width_bone.head + (-foottarget.x_axis() * foot_width)
    
    return mbg

def degrees_between(a,b):
    if type(a) == MetaBone:
        a = a.y_axis()
        
    if type(b) == MetaBone:
        b = b.y_axis()
        
    return math.degrees(math.acos(max(min(a.dot(b),1),-1))) 

def rig_target_affected(target,affected,headtotail=0,position_rigidity=2,orientation_rigidity=.1):
    metaconstraint = affected.new_meta_blender_constraint('BEPUIK_CONTROL',target,target.name)
    metaconstraint.connection_b = target
    metaconstraint.orientation_rigidity = orientation_rigidity
    metaconstraint.bepuik_rigidity = position_rigidity
    metaconstraint.pulled_point = (0,headtotail,0)
    target.show_wire = True
    target.lock_scale = (True,True,True)


    
    
def rig_twist_limit(a,b,twist):
    c = a.new_meta_blender_constraint('BEPUIK_TWIST_LIMIT',b)
    c.axis_a = a, 'Y'
    c.axis_b = b, 'Y'
    c.measurement_axis_a = a, 'Z'
    c.measurement_axis_b = b, 'Z'
    c.max_twist = twist
    
    return c
    
def rig_swing_limit(a,b,swing):
    c = a.new_meta_blender_constraint('BEPUIK_SWING_LIMIT',b)
    c.axis_a = a, 'Y'
    c.axis_b = b, 'Y'
    c.max_swing = swing
    
def rig_spine(hips,spine,chest,neck,head,ribsl,ribsr):
    def rig_rib(rib):
        rib.parent = chest
        rib.use_deform = True
        rib.align_roll = Vector((0,-1,0))
    
    def spine_defaults(bone_list):
        prev_bone = None
        for bone in bone_list:
            bone.use_deform = True
            bone.use_bepuik = True
            bone.align_roll = Vector((0,-1,0))
            
            if prev_bone:
                bone.use_connect = True
                bone.bepuik_ball_socket_rigidity = BEPUIK_BALL_SOCKET_RIGIDITY_DEFAULT
                bone.parent = prev_bone
            
            prev_bone = bone
        
    rig_rib(ribsl)
    rig_rib(ribsr)


    spine_defaults([hips,spine,chest,neck,head])
    
    neck.bbone_in = .7
    neck.bbone_out = 1
    neck.bbone_segments = 7
    
    hips.bepuik_rotational_heaviness = 20
#    chest.segments = 32
#    chest.bbone_in = 2
#    chest.bbone_out = 0
    
    spine.bbone_segments = 8
    spine.bbone_in = 1
    spine.bbone_out = 1
    spine.bepuik_rotational_heaviness = 40
    
    
#    def spine_constraints(a,b,twist=20,swing=30):        
#        c = a.new_meta_blender_constraint('BEPUIK_TWIST_LIMIT',b)
#        c.axis_a = a, 'Y'
#        c.axis_b = b, 'Y'
#        c.measurement_axis_a = a, 'Z'
#        c.measurement_axis_b = a, 'Z'
#        c.max_twist = twist
#        
#        c = a.new_meta_blender_constraint('BEPUIK_SWING_LIMIT',b)
#        c.axis_a = b, 'Y'
#        c.axis_b = b, 'Y'
#        c.max_swing = swing
#
#    spine_constraints(hips,spine,swing=45)
#    spine_constraints(spine,chest,swing=45)
#    spine_constraints(chest,neck)
#    spine_constraints(neck,head,swing=80)
    
    rig_twist_limit(hips, chest, twist=45)
    rig_twist_limit(chest, head, twist=100)
    
    rig_swing_limit(hips, spine, 45)
    rig_swing_limit(spine, chest, 45)
    rig_swing_limit(chest, neck, 60)
    rig_swing_limit(neck, head, 80)
    
    rig_twist_joint(hips, spine)
    rig_twist_joint(chest, neck)
    
    return hips, head

def sum_vectors(vecs):
    v_sum = Vector((0,0,0))
    for v in vecs:
        v_sum += v
        
    return v_sum

WIDGET_DATA_DEFAULTS = {}
w = WIDGET_DATA_DEFAULTS[WIDGET_CUBE] = WidgetData()        
w.vertices = [(-1.0, -1.0, -1.0), (-1.0, 1.0, -1.0), (1.0, 1.0, -1.0), (1.0, -1.0, -1.0), (-1.0, -1.0, 1.0), (-1.0, 1.0, 1.0), (1.0, 1.0, 1.0), (1.0, -1.0, 1.0)]
w.edges = [(4, 5), (5, 1), (1, 0), (0, 4), (5, 6), (6, 2), (2, 1), (6, 7), (7, 3), (3, 2), (7, 4), (0, 3)]
w.faces = [] #faces make bmesh wonky? not right format? [[4, 5, 1, 0], [5, 6, 2, 1], [6, 7, 3, 2], [7, 4, 0, 3], [0, 1, 2, 3], [7, 6, 5, 4]]
    
w = WIDGET_DATA_DEFAULTS[WIDGET_SPHERE] = WidgetData()
w.vertices = [(-0.3826834559440613, 0.0, 0.9238795638084412), (-0.7071068286895752, 0.0, 0.7071067690849304), (-0.9238795638084412, 0.0, 0.3826834261417389), (-1.0, 0.0, -4.371138828673793e-08), (-0.9238795042037964, 0.0, -0.38268351554870605), (-0.7071067690849304, 0.0, -0.7071067690849304), (-0.38268348574638367, 0.0, -0.9238795042037964), (-1.5099580252808664e-07, 0.0, -1.0), (-0.9238795042037964, 0.3826833665370941, -5.960464477539063e-08), (-0.7071067690849304, 0.7071065902709961, -5.960464477539063e-08), (-0.3826834559440613, 0.9238792657852173, -5.960464477539063e-08), (-1.2119348014039133e-07, 0.38268324732780457, 0.9238796234130859), (-1.5099580252808664e-07, 0.7071065902709961, 0.7071068286895752), (-1.2119348014039133e-07, 0.9238792657852173, 0.3826833963394165), (-1.2119348014039133e-07, 0.9999996423721313, -5.960464477539063e-08), (-1.2119348014039133e-07, 0.9238792657852173, -0.38268351554870605), (-1.3609464133423899e-07, 0.7071064710617065, -0.7071067690849304), (-1.3609464133423899e-07, 0.38268327713012695, -0.9238795042037964), (-2.08779383115143e-07, -1.395019069150294e-07, 1.0), (0.3826831579208374, 0.9238791465759277, -5.960464477539063e-08), (0.7071062922477722, 0.7071064710617065, -5.960464477539063e-08), (0.9238789081573486, 0.3826832175254822, -5.960464477539063e-08), (0.38268303871154785, -2.9802322387695312e-08, 0.9238796234130859), (0.7071062922477722, -1.4901161193847656e-08, 0.7071068286895752), (0.9238789677619934, -8.940696716308594e-08, 0.3826833963394165), (0.9999992847442627, -2.9802322387695312e-08, -5.960464477539063e-08), (0.9238789677619934, -8.940696716308594e-08, -0.38268351554870605), (0.7071061730384827, -2.9802322387695312e-08, -0.7071067690849304), (0.38268303871154785, -2.9802322387695312e-08, -0.9238795042037964), (0.9238788485527039, -0.38268324732780457, -5.960464477539063e-08), (0.7071061730384827, -0.7071064114570618, -5.960464477539063e-08), (0.38268303871154785, -0.9238789677619934, -5.960464477539063e-08), (-1.658969637219343e-07, -0.3826831579208374, 0.9238796234130859), (-1.8079812491578195e-07, -0.707106351852417, 0.7071068286895752), (-2.4040275548031786e-07, -0.9238789677619934, 0.3826833963394165), (-1.8079812491578195e-07, -0.9999993443489075, -5.960464477539063e-08), (-2.4040275548031786e-07, -0.9238789677619934, -0.38268351554870605), (-1.658969637219343e-07, -0.707106351852417, -0.7071067690849304), (-1.658969637219343e-07, -0.3826831579208374, -0.9238795042037964), (-0.3826833665370941, -0.9238789081573486, -5.960464477539063e-08), (-0.7071065306663513, -0.7071062326431274, -5.960464477539063e-08), (-0.923879086971283, -0.3826830983161926, -5.960464477539063e-08)]
w.edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (3, 8), (8, 9), (9, 10), (11, 12), (12, 13), (13, 14), (14, 15), (15, 16), (16, 17), (10, 14), (14, 19), (19, 20), (20, 21), (22, 23), (23, 24), (24, 25), (25, 26), (26, 27), (27, 28), (21, 25), (25, 29), (29, 30), (30, 31), (32, 33), (33, 34), (34, 35), (35, 36), (36, 37), (37, 38), (31, 35), (35, 39), (39, 40), (40, 41), (18, 0), (18, 11), (17, 7), (18, 22), (28, 7), (18, 32), (38, 7), (41, 3)]
w.faces = []

w = WIDGET_DATA_DEFAULTS[WIDGET_EYE_TARGET] = WidgetData()
w.vertices = [(-0.5, 2.9802322387695312e-08, 0.5), (-0.5975451469421387, 2.9802322387695312e-08, 0.49039262533187866), (-0.691341757774353, 2.9802322387695312e-08, 0.4619397819042206), (-0.7777851223945618, 2.9802322387695312e-08, 0.41573479771614075), (-0.8535534143447876, 2.9802322387695312e-08, 0.3535533845424652), (-0.9157347679138184, 2.9802322387695312e-08, 0.2777850925922394), (-0.961939811706543, 1.4901161193847656e-08, 0.19134171307086945), (-0.9903926253318787, 7.450580596923828e-09, 0.09754517674446106), (-1.0, 3.552713678800501e-15, 3.774895063202166e-08), (-0.9903926849365234, -7.450580596923828e-09, -0.09754510223865509), (-0.961939811706543, -1.4901161193847656e-08, -0.19134163856506348), (-0.9157348275184631, -2.9802322387695312e-08, -0.2777850925922394), (-0.8535534143447876, -2.9802322387695312e-08, -0.3535533845424652), (-0.777785062789917, -2.9802322387695312e-08, -0.41573482751846313), (-0.6913416385650635, -2.9802322387695312e-08, -0.4619397819042206), (-0.5975450277328491, -2.9802322387695312e-08, -0.49039265513420105), (-0.49999985098838806, -2.9802322387695312e-08, -0.5), (-0.4024546444416046, -2.9802322387695312e-08, -0.4903925955295563), (-0.30865806341171265, -2.9802322387695312e-08, -0.4619396924972534), (-0.22221463918685913, -2.9802322387695312e-08, -0.4157346487045288), (-0.1464463770389557, -2.9802322387695312e-08, -0.3535531461238861), (-0.08426499366760254, -2.9802322387695312e-08, -0.2777848243713379), (-0.03806006908416748, -1.4901161193847656e-08, -0.1913413405418396), (-0.009607285261154175, -7.450580596923828e-09, -0.09754472970962524), (0.0, 5.684341886080802e-14, 4.827995780942729e-07), (-0.009607464075088501, 7.450580596923828e-09, 0.09754567593336105), (-0.03806045651435852, 1.4901161193847656e-08, 0.19134223461151123), (-0.08426553010940552, 2.9802322387695312e-08, 0.27778562903404236), (-0.1464470624923706, 2.9802322387695312e-08, 0.3535538613796234), (-0.2222154438495636, 2.9802322387695312e-08, 0.4157351851463318), (-0.3086589574813843, 2.9802322387695312e-08, 0.46194005012512207), (-0.402455598115921, 2.9802322387695312e-08, 0.490392804145813), (0.5, 2.9802322387695312e-08, 0.5), (0.40245485305786133, 2.9802322387695312e-08, 0.49039262533187866), (0.308658242225647, 2.9802322387695312e-08, 0.4619397819042206), (0.22221487760543823, 2.9802322387695312e-08, 0.41573479771614075), (0.1464465856552124, 2.9802322387695312e-08, 0.3535533845424652), (0.08426523208618164, 2.9802322387695312e-08, 0.2777850925922394), (0.03806018829345703, 1.4901161193847656e-08, 0.19134171307086945), (0.009607374668121338, 7.450580596923828e-09, 0.09754517674446106), (0.0, 3.552713678800501e-15, 3.774895063202166e-08), (0.009607315063476562, -7.450580596923828e-09, -0.09754510223865509), (0.03806018829345703, -1.4901161193847656e-08, -0.19134163856506348), (0.08426517248153687, -2.9802322387695312e-08, -0.2777850925922394), (0.1464465856552124, -2.9802322387695312e-08, -0.3535533845424652), (0.222214937210083, -2.9802322387695312e-08, -0.41573482751846313), (0.3086583614349365, -2.9802322387695312e-08, -0.4619397819042206), (0.4024549722671509, -2.9802322387695312e-08, -0.49039265513420105), (0.5000001192092896, -2.9802322387695312e-08, -0.5), (0.5975453853607178, -2.9802322387695312e-08, -0.4903925955295563), (0.6913419365882874, -2.9802322387695312e-08, -0.4619396924972534), (0.7777853608131409, -2.9802322387695312e-08, -0.4157346487045288), (0.8535536527633667, -2.9802322387695312e-08, -0.3535531461238861), (0.9157350063323975, -2.9802322387695312e-08, -0.2777848243713379), (0.9619399309158325, -1.4901161193847656e-08, -0.1913413405418396), (0.9903926849365234, -7.450580596923828e-09, -0.09754472970962524), (1.0, 5.684341886080802e-14, 4.827995780942729e-07), (0.9903925657272339, 7.450580596923828e-09, 0.09754567593336105), (0.9619395732879639, 1.4901161193847656e-08, 0.19134223461151123), (0.9157344698905945, 2.9802322387695312e-08, 0.27778562903404236), (0.8535529375076294, 2.9802322387695312e-08, 0.3535538613796234), (0.7777845859527588, 2.9802322387695312e-08, 0.4157351851463318), (0.6913410425186157, 2.9802322387695312e-08, 0.46194005012512207), (0.5975444316864014, 2.9802322387695312e-08, 0.490392804145813)]
w.edges = [(1, 0), (2, 1), (3, 2), (4, 3), (5, 4), (6, 5), (7, 6), (8, 7), (9, 8), (10, 9), (11, 10), (12, 11), (13, 12), (14, 13), (15, 14), (16, 15), (17, 16), (18, 17), (19, 18), (20, 19), (21, 20), (22, 21), (23, 22), (24, 23), (25, 24), (26, 25), (27, 26), (28, 27), (29, 28), (30, 29), (31, 30), (0, 31), (33, 32), (34, 33), (35, 34), (36, 35), (37, 36), (38, 37), (39, 38), (40, 39), (41, 40), (42, 41), (43, 42), (44, 43), (45, 44), (46, 45), (47, 46), (48, 47), (49, 48), (50, 49), (51, 50), (52, 51), (53, 52), (54, 53), (55, 54), (56, 55), (57, 56), (58, 57), (59, 58), (60, 59), (61, 60), (62, 61), (63, 62), (32, 63)]
w.faces = []    

w = WIDGET_DATA_DEFAULTS[WIDGET_ROOT] = WidgetData()
w.vertices = [(0.7071067690849304, 0.7071067690849304, 0.0), (0.7071067690849304, -0.7071067690849304, 0.0), (-0.7071067690849304, 0.7071067690849304, 0.0), (-0.7071067690849304, -0.7071067690849304, 0.0), (0.8314696550369263, 0.5555701851844788, 0.0), (0.8314696550369263, -0.5555701851844788, 0.0), (-0.8314696550369263, 0.5555701851844788, 0.0), (-0.8314696550369263, -0.5555701851844788, 0.0), (0.9238795042037964, 0.3826834261417389, 0.0), (0.9238795042037964, -0.3826834261417389, 0.0), (-0.9238795042037964, 0.3826834261417389, 0.0), (-0.9238795042037964, -0.3826834261417389, 0.0), (0.9807852506637573, 0.19509035348892212, 0.0), (0.9807852506637573, -0.19509035348892212, 0.0), (-0.9807852506637573, 0.19509035348892212, 0.0), (-0.9807852506637573, -0.19509035348892212, 0.0), (0.19509197771549225, 0.9807849526405334, 0.0), (0.19509197771549225, -0.9807849526405334, 0.0), (-0.19509197771549225, 0.9807849526405334, 0.0), (-0.19509197771549225, -0.9807849526405334, 0.0), (0.3826850652694702, 0.9238788485527039, 0.0), (0.3826850652694702, -0.9238788485527039, 0.0), (-0.3826850652694702, 0.9238788485527039, 0.0), (-0.3826850652694702, -0.9238788485527039, 0.0), (0.5555717945098877, 0.8314685821533203, 0.0), (0.5555717945098877, -0.8314685821533203, 0.0), (-0.5555717945098877, 0.8314685821533203, 0.0), (-0.5555717945098877, -0.8314685821533203, 0.0), (0.19509197771549225, 1.2807848453521729, 0.0), (0.19509197771549225, -1.2807848453521729, 0.0), (-0.19509197771549225, 1.2807848453521729, 0.0), (-0.19509197771549225, -1.2807848453521729, 0.0), (1.280785322189331, 0.19509035348892212, 0.0), (1.280785322189331, -0.19509035348892212, 0.0), (-1.280785322189331, 0.19509035348892212, 0.0), (-1.280785322189331, -0.19509035348892212, 0.0), (0.3950919806957245, 1.2807848453521729, 0.0), (0.3950919806957245, -1.2807848453521729, 0.0), (-0.3950919806957245, 1.2807848453521729, 0.0), (-0.3950919806957245, -1.2807848453521729, 0.0), (1.280785322189331, 0.39509034156799316, 0.0), (1.280785322189331, -0.39509034156799316, 0.0), (-1.280785322189331, 0.39509034156799316, 0.0), (-1.280785322189331, -0.39509034156799316, 0.0), (0.0, 1.5807849168777466, 0.0), (0.0, -1.5807849168777466, 0.0), (1.5807852745056152, 0.0, 0.0), (-1.5807852745056152, 0.0, 0.0)]
w.edges = [(0, 4), (1, 5), (2, 6), (3, 7), (4, 8), (5, 9), (6, 10), (7, 11), (8, 12), (9, 13), (10, 14), (11, 15), (16, 20), (17, 21), (18, 22), (19, 23), (20, 24), (21, 25), (22, 26), (23, 27), (0, 24), (1, 25), (2, 26), (3, 27), (16, 28), (17, 29), (18, 30), (19, 31), (12, 32), (13, 33), (14, 34), (15, 35), (28, 36), (29, 37), (30, 38), (31, 39), (32, 40), (33, 41), (34, 42), (35, 43), (36, 44), (37, 45), (38, 44), (39, 45), (40, 46), (41, 46), (42, 47), (43, 47)]
w.faces = []

w = WIDGET_DATA_DEFAULTS[WIDGET_CIRCLE] = widgetdata_circle(1)
    
def widgetdata_refresh_defaults():
    for name, widget in WIDGET_DATA_DEFAULTS.items():
        if name in bpy.data.objects:
            widget.ob = bpy.data.objects[name]
        else:
            widget.ob = None


def widgetdata_get(name,custom_widget_data = None):    
    if name in bpy.data.objects:
        old_ob = bpy.data.objects[name]
    else:
        old_ob = None

    if custom_widget_data and name in custom_widget_data:
        widget = custom_widget_data[name]
    elif name in WIDGET_DATA_DEFAULTS:
        widget = WIDGET_DATA_DEFAULTS[name]
    else:
        widget = None
    
    new_ob = old_ob
    if widget and not widget.ob:
        widget.create(name)
        new_ob = widget.ob
                
    if old_ob and old_ob != new_ob and old_ob.name in bpy.context.scene.objects:
        bpy.context.scene.objects.unlink(old_ob)
  
    if new_ob and new_ob.name not in bpy.context.scene.objects:
        bpy.context.scene.objects.link(new_ob)
        
    new_ob.layers = OB_LAYERS_WIDGET
    new_ob.name = name
        
    return new_ob
 
def rig_full_body(meta_armature_obj,op=None):
    custom_widget_data = {}
    
    printmsgs = []
    
    def widget_get(name):
        return widgetdata_get(name,custom_widget_data)
    
    
    bpy.ops.object.mode_set(mode='POSE')
    mbs = MetaBoneDict.from_ob(meta_armature_obj)
    
    eyel = mbs["eye.L"]
    eyer = mbs["eye.R"]
    jaw =  mbs["jaw"]
    hips = mbs["hips"]
    head = mbs["head"]
    chest = mbs["chest"]
    spine = mbs["spine"]
    neck = mbs["neck"]
    ribsl = mbs["ribs.L"]
    ribsr = mbs["ribs.R"]
    
    bpy.ops.object.mode_set(mode='OBJECT')
    meta_armature_obj.select = False
    meta_armature_obj.hide = True
    
    rig_ob = bpy.data.objects.new('Rig',bpy.data.armatures.new("Rig Bones"))
    bpy.context.scene.objects.link(rig_ob)
    bpy.context.scene.objects.active = rig_ob
    rig_ob.select = True
    
    root = mbs.new_bone("root")
    root.head = Vector((0,0,0))
    root.tail = Vector((0,1,0))
    root.align_roll = Vector((0,0,1))
    root.custom_shape = widget_get(WIDGET_ROOT)
    root.show_wire = True
    
#    torso = mbs.new_bone("torso")
#    torso.custom_shape = widget_get(WIDGET_ROOT)
#    torso.head = hips.head.copy()
#    torso.tail = torso.head + Vector((0,hips.length(),0))
#    torso.parent = root

    eye_target = mbs.new_bone('eye_target')
    eye_target.head = Vector((0,eyel.tail[1] - .5,eyel.tail[2]))
    eye_target.tail = eye_target.head + Vector((0,-(eyel.length() + eyer.length()),0))
    eye_target.custom_shape = widget_get(WIDGET_EYE_TARGET)
    eye_target.parent = root
    eye_target.show_wire = True

    jaw.use_deform = True
    jaw.lock_location = (True,True,True)
    jaw.align_roll = Vector((0,0,1))
    jaw.parent = head

    rig_spine(hips, spine, chest, neck, head, ribsl, ribsr)
#    hips.parent = torso
    hips.parent = root
    
    rig_point_puller(mbs, "hips-target", hips, root)
    rig_point_puller(mbs, "chest-target", chest, root)
    rig_point_puller(mbs, "head-target", head, root)
    
             
    hips_down_mat = hips.matrix() * Matrix.Rotation(math.pi,4,'Z')
    legcone_mat = hips_down_mat * Matrix.Rotation(math.pi/4,4,'X')
    measurement_axis_mat = hips_down_mat * Matrix.Rotation(math.pi/2,4,'X')
    
    up = Vector((0,0,1))
    forward = Vector((0,-1,0))
    
    def rig_side(suffixletter):
        if suffixletter=="L":
            relative_x_axis = 'X'
            legcone_rot_mat = Matrix.Rotation(math.pi/5,4,'Z')
        else:
            relative_x_axis = 'NEGATIVE_X'
            legcone_rot_mat = Matrix.Rotation(-math.pi/5,4,'Z')
        
        loleg = mbs["loleg.%s" % suffixletter]
        upleg = mbs["upleg.%s" % suffixletter]
        foot = mbs["foot.%s" % suffixletter]
        eye = mbs["eye.%s" % suffixletter]
        shoulder = mbs["shoulder.%s" % suffixletter]
        uparm = mbs["uparm.%s" % suffixletter]
        loarm = mbs["loarm.%s" % suffixletter]
        foot_target = mbs["foot-target.%s" % suffixletter]
        foot_width_bone = mbs["foot-width.%s" % suffixletter]
        
        def ps(name,p,s):
            return mbs["%s%s-%s.%s" % (name,p,s,suffixletter)]
        
        def pssc(name,p,s):
            return mbs.new_bone("MCH-%s%s-%s-swingcenter.%s" % (name,p,s,suffixletter))

        def get_segment_siblings(name,s):
            segment_siblings=[]
            for p in range(1,6):
                segment = ps(name,p,s)
                if segment:
                    segment_siblings.append(segment)
                    
            return segment_siblings
        
        def get_final_segments(name):
            final_segments = []
            for p in range(1,6):
                for s in [3,2,1]:
                    segment = ps(name,p,s)
                    if segment:
                        final_segments.append(segment)
                        break
                    
            return final_segments
        
        def rig_hand():
            def fs(f,s):
                return ps("finger",f,s)
                    
            def fssc(f,s):
                return pssc("finger",f,s)
                        
            palm_bones = get_segment_siblings("finger",1)
            s2_bones = get_segment_siblings("finger",2)
            
            hand = mbs.new_bone("hand.%s" % suffixletter)
            hand.parent = loarm
            hand.head = loarm.tail.copy()
            hand.tail = sum_vectors([s2.tail for s2 in s2_bones])/len(s2_bones)
            hand.align_roll = up.copy()
            hand.use_bepuik = True
            hand.bepuik_ball_socket_rigidity = BEPUIK_BALL_SOCKET_RIGIDITY_DEFAULT
            hand.use_connect = True
            
            antiparallel_limiter(loarm, hand, degrees=80)
            rig_twist_limit(loarm, hand, twist=170)
    
            width_between_tails = (palm_bones[0].tail - palm_bones[len(palm_bones) - 1].tail).length
            width_between_heads = (palm_bones[0].head - palm_bones[len(palm_bones) - 1].head).length
            hand_width_world = max(width_between_heads,width_between_tails)
            
            hand_width_local = hand_width_world / hand.length()
           
            hand_custom_shape_name = "%s.%s" % (WIDGET_HAND,suffixletter)
            
            custom_widget_data[hand_custom_shape_name] = widgetdata_pad(width=hand_width_local*.75,length=.75,mid=0)
            custom_widget_data[hand_custom_shape_name].subsurface_levels = 1
            
            hand_target_custom_shape_name = "%s-target.%s" % (WIDGET_HAND,suffixletter)
            custom_widget_data[hand_target_custom_shape_name] = widgetdata_pad(width=hand_width_local*1.2,length=1.0*1.2,mid=.1)
            
            
            hand.custom_shape = widget_get(hand_custom_shape_name)
            hand.show_wire = True
            
            hand_target = mbs.new_bone("hand-target.%s" % suffixletter)
            hand_target.parent = root 
            hand_target.head = hand.head.copy()
            hand_target.tail = hand.tail.copy()
            hand_target.custom_shape = widget_get(hand_target_custom_shape_name)
            hand_target.show_wire = True
            
            rig_target_affected(hand_target, hand)
            
            s1_swings = [0,0,0,3,3]
        
            if meta_armature_obj.bepuik_autorig.use_thumb:
                align_rolls = [forward,up,up,up,up]
            
            else:
                align_rolls = [up,up,up,up,up]
            
            for f in range(1,6):
                s1 = fs(f,1)
                s2 = fs(f,2)
                s3 = fs(f,3)
                s4 = fs(f,4)
                
                if not all((s1,s2,s3,s4)):
                    continue
                
                s1.swing = s1_swings[f-1]
                
                s3.swing_center = fssc(f,3)
                s4.swing_center = fssc(f,4)
                
                if f == 1 and meta_armature_obj.bepuik_autorig.use_thumb:
                    s2.swing_y = 30
                    
                    s3.swing_angle_max = 20
                    s3.swing_angle_min = -85
                    
                    s4.swing_angle_max = 80
                    s4.swing_angle_min = -60
                else:
                    s2.swing_x = 30
                    s2.swing_y = 90
                    
                    s3.swing_angle_max = 0
                    s3.swing_angle_min = -135
                    
                    s4.swing_angle_max = 45
                    s4.swing_angle_min = -95
                    
                rig_finger(hand, s1, s2, s3, s4, align_rolls[f-1])
        
        def rig_foot():
            def fs(f,s):
                return ps("toe",f,s)
                    
            def fssc(f,s):
                return pssc("toe",f,s)
            
            s1_bones = get_segment_siblings("toe",1)
            
            if len(s1_bones) > 1:
                foot_width_world = (s1_bones[0].head - s1_bones[len(s1_bones) - 1].head).length
            elif foot_width_bone:
                foot_width_world = foot_width_bone.length()
            else:
                foot_width_world = foot.length()/2
                
            #the foot width bone is only needed as a reference for single toed characters, after its used
            #delete it because the final rig doesn't need it.
            if foot_width_bone:
                del mbs[foot_width_bone.name]
            
            multitarget_segments = s1_bones
            final_segments = get_final_segments("toe")
            final_segments_tail_average = sum_vectors([metabone.tail for metabone in final_segments])/len(final_segments)
            
            foot_target_custom_shape_name = "%s-target.%s" % (WIDGET_FOOT,suffixletter)
            custom_widget_data[foot_target_custom_shape_name] = widgetdata_pad(width=foot_width_world / foot_target.length(),length=1.0,mid=.3)
            foot_target.show_wire = True
            foot_target.custom_shape = widget_get(foot_target_custom_shape_name)
            
            toes_target = mbs.new_bone("toes-target.%s" % suffixletter)
            toes_target.head = foot.tail.copy()
            toes_target.tail = final_segments_tail_average.copy()
            toes_target.tail = toes_target.head + (foot_target.y_axis() * toes_target.length()) 
            toes_target.parent = root
            
            toes_width_local = foot_width_world / toes_target.length()
            
            toes_target_custom_shape_name = "toes-target.%s" % (suffixletter)
            custom_widget_data[toes_target_custom_shape_name] = widgetdata_pad(width=toes_width_local*1.2,length=1.2,mid=.1)
            toes_target.show_wire = True
            toes_target.custom_shape = widget_get(toes_target_custom_shape_name)
            
            for f in range(1,6):
                s1 = fs(f,1)
                s2 = fs(f,2)
                s3 = fs(f,3)
                
                if not s1:
                    continue
                
                s1.swing_x = 20
                s1.swing_y = 45
                
                if s2:
                    s2.swing_center = fssc(f,2)
                    s2.swing_angle_max = 0
                    s2.swing_angle_min = -90
                  
                if s3:
                    s3.swing_center = fssc(f,3)    
                    s3.swing_angle_max = 70
                    s3.swing_angle_min = -20
                
                rig_twist_joint(foot, s1)
                rig_ballsocket_joint(foot, s1)
                rig_bone_to_bone_with_2d_swing_info(foot, s1, axis_a_override=s1)
                rig_toe(s1, s2, s3, align_roll=Vector((0,0,1)))
                s1.parent = foot
            
            for multitarget_segment in multitarget_segments:
                rig_target_affected(toes_target, multitarget_segment, headtotail=0, position_rigidity=0, orientation_rigidity=0)
        
            rig_point_puller(mbs, "foot-ball-target.%s" % suffixletter, foot, root, headtotail=1.0)
            
        
        #generally progress from head downward...
        eye.new_meta_blender_constraint('DAMPED_TRACK',eye_target)
        eye.use_deform = True
        eye.align_roll = Vector((0,0,1))
        eye.parent = head
        
        rig_arm(shoulder, uparm, loarm, relative_x_axis, up)
        rig_chest_to_shoulder(chest, shoulder, relative_x_axis) 
        rig_hand()
        
        
        foot_target.parent = root
        rig_leg(upleg, loleg, foot, foot_target, relative_x_axis)
                               
        rig_foot()

        legcone = mbs.new_bone("MCH-legcone.%s" % suffixletter,transform=legcone_mat * legcone_rot_mat)
        measure = mbs.new_bone("MCH-legtwistmeasureaxis.%s" % suffixletter,transform=measurement_axis_mat * legcone_rot_mat)
        rig_hips_to_upleg(hips, upleg, hips, measure, legcone)



    rig_side("L")
    rig_side("R")
    
    bpy.ops.object.mode_set(mode='EDIT')
    
    mbs.to_ob(rig_ob)
    
    organize_pchan_layers(rig_ob)
    rig_ob.bepuik_autorig.is_meta_armature = False
    rig_ob.bepuik_autorig.is_auto_rig = True
    rig_ob.use_bepuik_parented_peripheral_bones = True
    apply_rig_starting_layers(rig_ob)
    
    found_error = False
    found_warning = False
    for warninglevel, msg in printmsgs:
        if warninglevel == 'ERROR':
            found_error = True
        elif warninglevel == 'WARNING':
            found_warning = True
        
        if op:
            op.report({warninglevel},msg)
    
    if not found_error and not found_warning:
        op.report({'INFO'},"Rig Completed successfully!")
    
    return rig_ob



    
def rig_point_puller(metabonegroup,name,pulledmetabone,parent,scale=.10,headtotail=0,custom_shape_name= WIDGET_CUBE, show_wire = True,min_size=.005, lock_rotation = False, custom_widget_data = None):
    
    puller_headtotail_offset = (pulledmetabone.tail.copy() - pulledmetabone.head.copy()) * headtotail
    
    direction = pulledmetabone.tail - pulledmetabone.head
    direction = direction.normalized()
    l = (pulledmetabone.tail-pulledmetabone.head).length
    v = direction * scale * l
    if v.length < min_size:
        v = direction * min_size
    
    pullermetabone = metabonegroup.new_bone(name)
    
    pullermetabone.head = pulledmetabone.head + puller_headtotail_offset
    pullermetabone.tail = pullermetabone.head + v
    pullermetabone.roll = pulledmetabone.roll
    pullermetabone.parent = parent
    pullermetabone.show_wire = show_wire
    pullermetabone.custom_shape = widgetdata_get(custom_shape_name, custom_widget_data)    
    pullermetabone.lock_scale = (True,True,True)
    pullermetabone.align_roll = pulledmetabone.align_roll.copy()
    if lock_rotation:
        pullermetabone.lock_rotation = (True,True,True)
        pullermetabone.lock_rotation_4d = True
    
    rig_target_affected(pullermetabone, pulledmetabone, headtotail=0, position_rigidity=0, orientation_rigidity=0)
    
    return pullermetabone
    
def flag_bone_mechanical(mechanical_bone):
    mechanical_bone.lock_rotation = (True,True,True)
    mechanical_bone.lock_location = (True,True,True)
    mechanical_bone.lock_scale = (True,True,True)
    mechanical_bone.lock_rotation_w = True
    
    if not mechanical_bone.name.startswith("MCH-"):
        mechanical_bone.name = "MCH-%s" % mechanical_bone.name
   
def rig_hips_to_upleg(hips,upleg,upleg_parent,measurement_axis,legcone):
    flag_bone_mechanical(measurement_axis)
    measurement_axis.parent = hips
    flag_bone_mechanical(legcone)
    legcone.parent = hips
    
    upleg.use_deform = True
    upleg.parent = upleg_parent
    
    c = hips.new_meta_blender_constraint('BEPUIK_TWIST_LIMIT',upleg)
    c.axis_a = hips, 'NEGATIVE_Y'
    c.axis_b = upleg, 'Y'
    c.measurement_axis_a = measurement_axis, 'Y'
    c.measurement_axis_b = upleg, 'Z'
    #TODO: this might not be enough twist for sitting feet soles together knees down
    c.max_twist = max(80,degrees_between(upleg.z_axis(), measurement_axis)+2)
    
    if upleg_parent == hips:
        flag_bone_deforming_ballsocket_bepuik(upleg)
    else:
        c = hips.new_meta_blender_constraint('BEPUIK_BALL_SOCKET_JOINT',upleg)
        c.anchor = upleg, 0

    c = hips.new_meta_blender_constraint('BEPUIK_SWING_LIMIT',upleg)
    c.axis_a = legcone, 'Y'
    c.axis_b = upleg, 'Y'
    c.max_swing = max(47,degrees_between(upleg, legcone) + 2)

def rig_bone_to_bone_revolute_swing_center(fa,fb,swing_center,swing_angle_max,swing_angle_min):
    c = fa.new_meta_blender_constraint('BEPUIK_REVOLUTE_JOINT',fb)
    c.free_axis = fa, 'X'

    m = fa.matrix() * Matrix.Rotation(math.radians((swing_angle_max+swing_angle_min)/2),4,'X')
    swing_center.head = fa.tail.copy()
    swing_center.tail = fa.tail.copy() + (Vector4_to_Vector3(m.col[1]) * fa.length())
    swing_center.parent = fa
    flag_bone_mechanical(swing_center)

    c = fa.new_meta_blender_constraint('BEPUIK_SWING_LIMIT',fb)
    c.axis_a = swing_center, 'Y'
    c.axis_b = fb, 'Y'
    c.max_swing = abs(swing_angle_max - swing_angle_min)/2

def rig_twist_joint(a,b,axis_a_override=None):
    if not axis_a_override:
        axis_a_override = a
    
    c = a.new_meta_blender_constraint('BEPUIK_TWIST_JOINT',b)
    c.axis_a = axis_a_override, 'Y'
    c.axis_b = b, 'Y'

def rig_ballsocket_joint(a,b):
    c = a.new_meta_blender_constraint('BEPUIK_BALL_SOCKET_JOINT',b)
    c.anchor = b, 0

def rig_bone_to_bone_with_swing_center_info(s,s_with_swing):
    rig_bone_to_bone_revolute_swing_center(s, s_with_swing, s_with_swing.swing_center, s_with_swing.swing_angle_max,s_with_swing.swing_angle_min)

def rig_bone_to_bone_with_2d_swing_info(a,b,axis_a_override=None):
    if not axis_a_override:
        axis_a_override = a
    
    if(hasattr(b,'swing_y')):
        c = a.new_meta_blender_constraint('BEPUIK_SWING_LIMIT',b)
        c.axis_a = axis_a_override, 'Y'
        c.axis_b = b, 'Y'
        c.max_swing = b.swing_y
    
    if(hasattr(b,'swing_x')):
        c = a.new_meta_blender_constraint('BEPUIK_SWING_LIMIT',b)
        c.axis_a = axis_a_override, 'X'
        c.axis_b = b, 'X'
        c.max_swing = b.swing_x
    
def rig_finger(hand,s1,s2,s3,s4,align_roll):
    hand.align_roll = align_roll.copy()
    s1.align_roll = align_roll.copy()
    s2.align_roll = align_roll.copy()
    s3.align_roll = align_roll.copy()
    s4.align_roll = align_roll.copy()
    
    s1.parent = hand
    
    #s1 is the palm bone
    if s1.swing:
        flag_bone_deforming_ballsocket_bepuik(s1)

        c = hand.new_meta_blender_constraint('BEPUIK_REVOLUTE_JOINT',s1)
        c.free_axis = hand, 'X'
        
        c = hand.new_meta_blender_constraint('BEPUIK_SWING_LIMIT',s1)
        c.axis_a = hand, 'Y'
        c.axis_b = s1, 'Y'
        c.max_swing = max(degrees_between(hand, s1),s1.swing)
        
        #since s1 has a swing, s2 will be its child
        s2_parent = s1
        s2.use_connect = True
    else:
        #s1 doesn't have a swing, therefore, it should simply be a deforming mechanical bone.
        s1.use_deform = True
        flag_bone_mechanical(s1)
        
        s2_parent = hand
        s2.use_connect = False
    
    s2.parent = s2_parent
    
    rig_twist_joint(s2.parent, s2)
    rig_bone_to_bone_with_2d_swing_info(s2.parent, s2, axis_a_override=s1)   
    flag_bone_deforming_ballsocket_bepuik(s2)
    
    rig_twist_joint(s2,s3)
    rig_bone_to_bone_with_swing_center_info(s2,s3)
    flag_bone_deforming_ballsocket_bepuik(s3)
    s3.use_connect = True
    s3.parent = s2

    rig_twist_joint(s3,s4)
    rig_bone_to_bone_with_swing_center_info(s3,s4)
    flag_bone_deforming_ballsocket_bepuik(s4)
    s4.use_connect = True
    s4.parent = s3
    
    
        

def rig_toe(s1,s2,s3,align_roll):
    s1.align_roll = align_roll.copy()
    flag_bone_deforming_ballsocket_bepuik(s1)
    
    if s2:
        s2.use_connect = True
        s2.parent = s1
        s2.align_roll = align_roll.copy()
        
        rig_twist_joint(s1,s2)
        rig_bone_to_bone_with_swing_center_info(s1,s2)
        flag_bone_deforming_ballsocket_bepuik(s2)


    if s3:
        s3.use_connect = True
        s3.parent = s2
        s3.align_roll = align_roll.copy()
        
        rig_twist_joint(s2,s3)
        rig_bone_to_bone_with_swing_center_info(s2,s3)
        flag_bone_deforming_ballsocket_bepuik(s3)

    
    
      
  
def rig_leg(upleg,loleg,foot,foottarget,relative_x_axis='X'):
    upleg.align_roll = Vector((0,-1,0))
    flag_bone_deforming_ballsocket_bepuik(upleg)
    
    loleg.align_roll = Vector((0,-1,0))
    flag_bone_deforming_ballsocket_bepuik(loleg)
    loleg.use_connect = True
    loleg.bepuik_ball_socket_rigidity = 50
    
    foot.align_roll = Vector((0,0,1))
    flag_bone_deforming_ballsocket_bepuik(foot)
    foot.use_connect = True
    foot.bepuik_ball_socket_rigidity = 200

    #upleg to loleg connections

    
    c = upleg.new_meta_blender_constraint('BEPUIK_REVOLUTE_JOINT',loleg)    
    c.free_axis = upleg,'X'
    
    antiparallel_limiter(upleg, loleg)

    
    c = upleg.new_meta_blender_constraint('BEPUIK_SWING_LIMIT',loleg)
    c.axis_a = upleg, 'NEGATIVE_Z'
    c.axis_b = loleg,'Y'
    #the 85 here helps prevent knee locking
    c.max_swing = max(degrees_between(loleg,-upleg.z_axis()),85)
    
    loleg.parent = upleg
    
    #loleg to foot connections
    c = loleg.new_meta_blender_constraint('BEPUIK_TWIST_LIMIT',foot)
    c.axis_a = foot, 'Y'
    c.axis_b = foot, 'Y'
    c.measurement_axis_a = foot, 'Z'
    c.measurement_axis_b = foot, 'Z'
    c.max_twist = 30

    c = loleg.new_meta_blender_constraint('BEPUIK_SWING_LIMIT',foot)
    c.axis_a = foot, 'Y'
    c.axis_b = foot, 'Y'
    c.max_swing = 45

    c = loleg.new_meta_blender_constraint('BEPUIK_SWING_LIMIT',foot)
    c.axis_a = loleg, relative_x_axis
    c.axis_b = loleg, relative_x_axis
    c.max_swing = 22
    
    foot.parent = loleg
    
    rig_target_affected(foottarget, foot)
    
    
      
def rig_twistproxy(metabonegroup,obj,name,parent,twistproxytarget,bbone_segments,align_roll,bbone_in=1,bbone_out=1):    
        twist = metabonegroup.new_bone_by_fraction(name,twistproxytarget,0,1)
        twist.use_bepuik = False
        twist.use_deform = True
        twist.parent = parent
        twist.bbone_segments = bbone_segments
        twist.bbone_out = bbone_in
        twist.bbone_in = bbone_out
        twist.align_roll = align_roll.copy()
        

        c = twist.abc(type='COPY_ROTATION')
        c.target = obj
        c.subtarget = twistproxytarget
        c.target_space = 'LOCAL'
        c.owner_space = 'LOCAL'
        
        return twist


#def init_rig_twistproxy_with_anchor(metabonegroup,obj,name,twiststarttarget,twistanchortarget,bbone_segments,align_roll):    
#        twist = metabonegroup.new_bone_by_fraction(name,twiststarttarget,0,1)
#        twist.use_bepuik = False
#        twist.use_deform = True
#        twist.parent = twiststarttarget
#        twist.use_connect = False
#        twist.bbone_segments = bbone_segments
#        twist.bbone_out = 0
#        twist.bbone_in = 0 
#        twist.align_roll = align_roll.copy()

def rig_twistanchor(metabonegroup,obj,name,parent,twistanchortarget,align_roll):        
        anchor = metabonegroup.new_bone_by_fraction("%s-anchor" % name,twistanchortarget,0,.1)
        anchor.use_bepuik = False 
        anchor.use_deform = False
        anchor.parent = parent
        anchor.align_roll = align_roll.copy()
        c = anchor.abc(type='COPY_ROTATION')
        c.target = obj
        c.subtarget = twistanchortarget
        c.target_space = 'LOCAL'
        c.owner_space = 'LOCAL'
        
        return anchor

def flag_bone_deforming_ballsocket_bepuik(metabone):
    metabone.use_deform = True
    metabone.use_bepuik = True
    metabone.bepuik_ball_socket_rigidity = BEPUIK_BALL_SOCKET_RIGIDITY_DEFAULT

def antiparallel_limiter(a,b,degrees=20):
    c = a.new_meta_blender_constraint('BEPUIK_SWING_LIMIT',b)
    c.axis_a = a, 'Y'
    c.axis_b = b,'Y'
    c.max_swing = 180-degrees



def rig_arm(shoulder,uparm,loarm,relative_x_axis,up=Vector((0,0,1))):
    shoulder.align_roll = up.copy()
    shoulder.use_bepuik = True
    shoulder.use_deform = True
    shoulder.bepuik_ball_socket_rigidity = 0
    shoulder.bepuik_rotational_heaviness = 35
    
    uparm.align_roll = up.copy()
    uparm.use_connect = True
    flag_bone_deforming_ballsocket_bepuik(uparm)

    loarm.bbone_segments = 32
    loarm.bbone_out = 0
    loarm.bbone_in = 0
    loarm.align_roll = up.copy()
    loarm.use_connect = True
    flag_bone_deforming_ballsocket_bepuik(loarm)

    antiparallel_limiter(shoulder, uparm, 30)

#    c = shoulder.new_meta_blender_constraint('BEPUIK_SWING_LIMIT',uparm)
#    c.axis_a = shoulder, 'NEGATIVE_Z'
#    c.axis_b = uparm, 'Y'
#    c.max_swing = max(90,degrees_between(-shoulder.z_axis(), uparm) + 1)

#    c = shoulder.new_meta_blender_constraint('BEPUIK_SWING_LIMIT',uparm)
#    c.axis_a = uparm, relative_x_axis
#    c.axis_b = uparm, 'Y'
#    c.max_swing = 90
    
    c = shoulder.new_meta_blender_constraint('BEPUIK_TWIST_LIMIT',uparm)
    c.axis_a = shoulder, 'Y'
    c.axis_b = uparm, 'Y'
    c.measurement_axis_a = shoulder, 'Z'
    c.measurement_axis_b = shoulder, 'Z'
    c.max_twist = 100
    
    c = uparm.new_meta_blender_constraint('BEPUIK_SWING_LIMIT',loarm)
    c.axis_a = loarm, relative_x_axis
    c.axis_b = loarm,'Y'
    c.max_swing = 90
    
    antiparallel_limiter(uparm, loarm)
    
    c = uparm.new_meta_blender_constraint('BEPUIK_REVOLUTE_JOINT',loarm)      
    c.free_axis = uparm,'Z'       

def rig_chest_to_shoulder(chest,shoulder,relative_x_axis):
    shoulder.parent = chest
    shoulder.use_connect = False
    shoulder.bepuik_ball_socket_rigidity = 16
    
    c = chest.new_meta_blender_constraint('BEPUIK_TWIST_JOINT',shoulder)
    c.axis_a = shoulder, 'Y'
    c.axis_b = shoulder, 'Y'
    
    #prevents the shoulder from going too far up
    c = chest.new_meta_blender_constraint('BEPUIK_SWING_LIMIT',shoulder)   
    c.axis_a = shoulder, 'Y'
    c.axis_b = shoulder, 'Y'
    c.max_swing = 45
    
    #prevents the shoulder from going too far down
    c = chest.new_meta_blender_constraint('BEPUIK_SWING_LIMIT',shoulder)   
    c.axis_a = shoulder, 'Z'
    c.axis_b = shoulder, 'Y'
    c.max_swing = 95
    
    #prevents the shoulder from going too far forward or back
    c = chest.new_meta_blender_constraint('BEPUIK_SWING_LIMIT',shoulder)   
    c.axis_a = shoulder, relative_x_axis
    c.axis_b = shoulder, relative_x_axis
    c.max_swing = 22      

def get_pchan_target_names(ob):
    pchan_target_names = set()
    for pchan in ob.pose.bones:
        for con in pchan.constraints:
            if con.type == 'BEPUIK_CONTROL':
                if con.connection_subtarget:
                    pchan_target_names.add(con.connection_subtarget)
                    
    return pchan_target_names

def organize_pchan_layer(pchan,bone_hint_str=None,is_bepuik_target=False):
    bone = pchan.bone
    suffixletter = get_suffix_letter(bone.name)
    layer_indices = set()
    exclude_from_body_layers = False
    
    if bone.use_deform:
        layer_indices.add(AL_DEFORMER)
    
    if pchan.use_bepuik:
        layer_indices.add(AL_BEPUIK_BONE)
    
    if is_bepuik_target:
        layer_indices.add(AL_TARGET)
    
    if (pchan.rotation_mode == 'QUATERNION' or pchan.rotation_mode == 'AXIS_ANGLE') and pchan.lock_rotations_4d:
        lock_rotation = (all(pchan.lock_rotation) and pchan.lock_rotation_w)
    else:
        lock_rotation = (all(pchan.lock_rotation))
        
    if not lock_rotation or not all(pchan.lock_scale) or not all(pchan.lock_location):
        layer_indices.add(AL_ANIMATABLE)
    else:
        layer_indices.add(AL_MECHANICAL)
        exclude_from_body_layers = True
        
#    if pchan.name.startswith("MCH-"):
#        layer_indices.add(AL_MECHANICAL)
#        exclude_from_body_layers = True
    
    if not exclude_from_body_layers:
        if not bone_hint_str:
            bone_hint_str = bone.basename
        
        for substring_set in SUBSTRING_SETS:
            if any(substring in bone_hint_str for substring in substring_set):
                if (substring_set,suffixletter) in MAP_SUBSTRING_SET_TO_ARMATURELAYER:
                    index_to_add = MAP_SUBSTRING_SET_TO_ARMATURELAYER[(substring_set,suffixletter)]
                    layer_indices.add(index_to_add)
                    break
    
    bone.layers = [True if i in layer_indices else False for i in range(32)]
                    
def organize_pchan_layers(ob):
    pchan_target_names = get_pchan_target_names(ob)
    for pchan in ob.pose.bones:
        organize_pchan_layer(pchan,is_bepuik_target=pchan.name in pchan_target_names)
    
    
