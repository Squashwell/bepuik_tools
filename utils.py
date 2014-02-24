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
import bpy
from mathutils import Vector, geometry, Matrix
import math
 
def create_editbone(armature_obj,ebone_name,head,tail,roll,bbone_x=None,bbone_z=None):
    new_bone = armature_obj.data.edit_bones.new(name=ebone_name)
    new_bone.head = head
    new_bone.tail = tail
    new_bone.roll = roll
    length = (tail-head).length

    if bbone_x:
        new_bone.bbone_x = bbone_x
    else:
        new_bone.bbone_x = length/8
        
    if bbone_z:
        new_bone.bbone_z = bbone_z
    else:
        new_bone.bbone_z = length/8
        
    return new_bone
    

def create_editbone_by_headtotail_fraction(armature_obj,ebone,name,start_fraction,end_fraction):
    ebone_start_point = ebone.head
    ebone_end_point = ebone.tail
    
    local_vector = (ebone_end_point - ebone_start_point)
    local_start = local_vector * start_fraction
    local_end =   local_vector * end_fraction
    global_start = ebone_start_point + local_start
    global_end = ebone_start_point + local_end
    
    return create_editbone(armature_obj,name,global_start,global_end,ebone.roll)

def quat_get_up(v):
    w = v.w
    x = v.x
    y = v.y
    z = v.z
    return Vector(( 2 * (x * z + w * y), 
                    2 * (y * x - w * x),
                    1 - 2 * (x * x + y * y)))

def quat_get_forward(v):
    w = v.w
    x = v.x
    y = v.y
    z = v.z
    return Vector(( 2 * (x * y - w * z), 
                    1 - 2 * (x * x + z * z),
                    2 * (y * z + w * x)))

def quat_get_right(v):
    w = v.w
    x = v.x
    y = v.y
    z = v.z
    return Vector(( 1 - 2 * (y * y + z * z),
                    2 * (x * y + w * z),
                    2 * (x * z - w * y)))


