import bpy
import xml.etree.ElementTree as ET
from mathutils import Euler, Quaternion, Vector
import os
import numpy as np
from math import radians
import math
import json
from mathutils import Matrix
from pathlib import Path


with open('D:\\GitHub\\BesiegeCreationImporter\\modules\\object_transform_data.json') as json_file:
    object_atlas = json.load(json_file)

base_location = "D:\\GitHub\\BesiegeCreationImporter\\modules\\Models\\Template"


def ImportCreation(path):
	bpy.ops.object.select_all(action='DESELECT')

	doc = ET.parse(path)
	block_list = list(doc.getroot()[2])

		# so according to my "calculations" the final location of the block is determined by the file defined location minus the offset defined for the block
		# at https://besiege.fandom.com/wiki/Skin_Model_Transforms
		# The same applies to the scale... but I might be wrong...
		# Hopefully it is the same rule and it also appies to rotation
		#
		# Update : So I was SUPER wrong

	for block in block_list:
		bpy.ops.object.select_all(action='DESELECT')
		transform_data = list(list(block)[0])
		block_id = block.get("id")

		position = transform_data[0]
		rotation = transform_data[1]
		scale = transform_data[2]

		if not block_id in object_atlas:
			print("Block ID {} cannot be found in atlas...".format(block_id))
			continue

		bpy.ops.import_scene.obj(filepath=FetchModel(block_id))
		
		wrq = float(rotation.get("w")) 
		xrq = float(rotation.get("x")) 
		yrq = float(rotation.get("z")) 
		zrq = float(rotation.get("y")) 
		
		current_obj = bpy.context.selected_objects[0]
		

		for m in current_obj.data.materials:
			bpy.data.materials.remove(m)

		new_mat = GenerateMaterial(block_id)
		current_obj.data.materials.append(new_mat)
		current_obj.active_material = new_mat

		# get the offset transform values from the skin model website
		preset_pos = object_atlas[block_id]["relative_transform"]["position"]
		preset_rot = object_atlas[block_id]["relative_transform"]["rotation"]
		preset_sca = object_atlas[block_id]["relative_transform"]["scale"]
		current_obj.scale = (preset_sca["x"], preset_sca["z"], preset_sca["y"])

		print("{} {} {}".format(preset_rot['x'], preset_rot['y'], preset_rot['z']))

		# rotate according to the offset
		bpy.ops.transform.rotate(value=math.radians(preset_rot["x"]), orient_axis='X', orient_type='LOCAL', orient_matrix_type='LOCAL')
		bpy.ops.transform.rotate(value=math.radians(preset_rot["y"]), orient_axis='Y', orient_type='LOCAL', orient_matrix_type='LOCAL')
		bpy.ops.transform.rotate(value=math.radians(preset_rot["z"]), orient_axis='Z', orient_type='LOCAL', orient_matrix_type='LOCAL')

	

		# translate according to the offset
		offset_x = (preset_pos["x"])
		offset_y = (preset_pos["z"])
		offset_z = (preset_pos["y"])
		current_obj.location = Vector((offset_x, offset_y, offset_z))
		bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

		# continue

		# scale
		current_obj.scale = (float(scale.get("x")), float(scale.get("z")), float(scale.get("y")))

		# rotate
		current_obj.rotation_mode = 'QUATERNION'
		qtrans = Quaternion([wrq, xrq, yrq, zrq])
		qtrans.invert()
		current_obj.rotation_quaternion  = qtrans


		# translate according to the BSG file
		xtrans = float(position.get("x"))
		ztrans = float(position.get("z"))
		ytrans = float(position.get("y"))
		current_obj.location = Vector((xtrans, ztrans, ytrans ))

def FetchModel(block_id):
	for f in os.listdir(os.path.join(base_location, object_atlas[block_id]["path"])):
		if f.endswith(".obj"):
			return os.path.join(base_location, object_atlas[block_id]["path"], f)


def FetchTexture(block_id):
	for f in os.listdir(os.path.join(base_location, object_atlas[block_id]["path"])):
		if f.endswith(".png"):
			return os.path.join(base_location, object_atlas[block_id]["path"], f)

def GenerateMaterial(obj_code):
	mat_name = object_atlas[obj_code]["material"]["name"]
	for m in bpy.data.materials:
		if mat_name == m.name:
			return m
	m = bpy.data.materials.new(name=mat_name) # create new material
	m.use_nodes = True # enable nodes
	nodes = m.node_tree.nodes
	nodes.clear() # get rid of the default nodes
	image_texture_node = nodes.new("ShaderNodeTexImage") # create nodes
	principled_bdsf_node = nodes.new("ShaderNodeBsdfPrincipled")
	output_node = nodes.new("ShaderNodeOutputMaterial")
	image_texture_node.location = (0, 0) # organise the nodes
	principled_bdsf_node.location = (400, 0)
	output_node.location = (800, 0)
	image_texture_node.image = bpy.data.images.load(FetchTexture(obj_code))# load the image for the image texture node
	m.node_tree.links.new(principled_bdsf_node.inputs[0], image_texture_node.outputs[0])# link the ndoes
	m.node_tree.links.new(output_node.inputs[0], principled_bdsf_node.outputs[0])

	return m # return the newly generated material

def move_local_axis(obj, vec):
	inv = obj.matrix_world.copy()
	inv.invert()
	# vec aligned to local axis in Blender 2.8+
	# in previous versions: vec_rot = vec * inv
	# So this prolly wouldn't work for versions of blender prior to 2.8
	vec_rot = vec @ inv
	obj.location = obj.location + vec_rot
	
def quaternion_to_euler(x, y, z, w):
		# Note to self... if something allows you to enter the values in quarternions, dont go out your way to
		# find a method to calculate it to Euler and then to radians and apply the rotation it in radians...
		# if it allows quarternion input and the data source is in quarternions, just use fucking quarternions...
        t0 = +2.0 * (w * x + y * z)
        t1 = +1.0 - 2.0 * (x * x + y * y)
        X = math.degrees(math.atan2(t0, t1))
        t2 = +2.0 * (w * y - z * x)
        t2 = +1.0 if t2 > +1.0 else t2
        t2 = -1.0 if t2 < -1.0 else t2
        Y = math.degrees(math.asin(t2))
        t3 = +2.0 * (w * z + x * y)
        t4 = +1.0 - 2.0 * (y * y + z * z)
        Z = math.degrees(math.atan2(t3, t4))
        return radians(X), radians(Y), radians(Z)


if __name__ == "__main__":
	print('Starting console...')
	# ImportCreation("D:\\GitHub\\besiege creation importer\\tgyd-mech.bsg")
	ImportCreation("D:\\GitHub\\BesiegeCreationImporter\\modules\\bsgs\\Spot.bsg")
