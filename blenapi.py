import bpy
import os
import numpy as np
import math
import json
import xml.etree.ElementTree as ET
import random
from mathutils import Euler, Quaternion, Vector, Matrix
from math import radians, pi, sqrt
from pathlib import Path
# from .bsgreader import Reader
import Block
import Component
import MaterialCatalog
from bsgreader import Reader

class BlenderAPI():
	# So we are defining 3 directories. One for the workshop skin directory, one 
	# for the skin folder in the game data skin directory and one to use as the backup
	# preferably the template vanilla skin from the game data directory. Note that the first 2
	# are pointing to a directory with multiple skins whereas the backup store is defining a single skin pack
	workshop_store = ""
	game_store = ""
	backup_store = ""
	status = ""
	status_description = []
	temp_obj_list = []
	import_object_list = {}
	custom_import_object_list = {}
	
	def __init__(self, ws_store, game_store, backup):
		self.status = 'OK'
		self.workshop_store = ws_store
		self.game_store = game_store
		self.backup_store = backup

	def LookupObject(self, block:Block, component:Component, vanilla_skins=False):
		# if the block is not in the object list, create a new key
		# and update it...
		sid = str(hash(block.block_id + component.skin_name + block.flipped))
		if sid in self.import_object_list.keys():
			new_obj = bpy.data.objects[self.import_object_list[sid]].copy()
			bpy.data.collections[bpy.context.view_layer.active_layer_collection.name].objects.link(new_obj)
			return new_obj
		else:
			# ...if we cannot find the skin we need, we'll import it
			model = self.FetchModel(component.base_source, component.skin_id, component.skin_name)
			bpy.ops.import_scene.obj(filepath=model[0])
			current_obj = list(bpy.context.selected_objects)[0]
			[bpy.data.materials.remove(m) for m in current_obj.data.materials]
			skin_name = component.skin_name if not vanilla_skins else 'Template'
			current_obj.active_material = self.GenerateMaterial(component, model[1], skin_name)
			# Set the offset scale data from the JSON file
			current_obj.scale = [component._offset_scale_x, component._offset_scale_z, component._offset_scale_y]
			# special offset for propellers...
			# I'll think of a way to offset this in the json file...
			# TODO Refactor offsetting code for propellers
			if (block.block_id in ['26','55']):
				component._offset_rotation_y += 23 if block.flipped != 'True' else -23
			# Rotate according to the offset data from the JSON file
			current_obj.rotation_euler.x -= math.radians(component._offset_rotation_x)
			current_obj.rotation_euler.y -= math.radians(component._offset_rotation_y)
			current_obj.rotation_euler.z -= math.radians(component._offset_rotation_z)
			# Translate according to the offset data from the JSON file
			current_obj.location = Vector([component._offset_translate_x, component._offset_translate_y, component._offset_translate_z])
			bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
			current_obj.name = str(hash(current_obj.name))
			self.temp_obj_list.append(current_obj)
			newobj = current_obj.copy()
			bpy.data.collections[bpy.context.view_layer.active_layer_collection.name].objects.link(newobj)
			skin_data_template = {sid : current_obj.name}
			self.import_object_list.update(skin_data_template)
			return newobj

	def ImportCreation(self, path:str, vanilla_skins=False, create_parent=False) -> None:
		'''
		Import a Besiege Creation File (bsg file).
		Parameters
			path : string : Path to the bsg file
			vanilla_skins : bool : Use vanilla skins instead of the skins defined in the bsg file
			create_parent : Parent all imported objects to an empty after importing them
		Return : None
		Exceptions : None
		'''
		self.import_object_list = {}
		self.custom_import_object_list = {}

		ReaderInstance = Reader(path)
		block_list = ReaderInstance.ReadBlockData()
		imported_list = []

		print("Importing {} blocks...".format(len(block_list)))

		normal_draw = []
		line_draw = []

		for block in block_list:
			if block.block_id in ['7']:
				line_draw.append(block)
			else:
				normal_draw.append(block)

		for block in normal_draw:
			for component in block.components:
				imported_list.append(self.BlockDrawTypeDefault(block, component, vanilla_skins))
		
		for block in line_draw:
			for component in block.components:
				imported_list.append(self.BlockDrawTypeLineType(block, component, vanilla_skins))		
		
		for block in self.temp_obj_list:
			bpy.data.objects.remove(block)
		self.temp_obj_list.clear()

	def ImportCustomModel(self, block_name):
		if not block_name in self.custom_import_object_list.keys():
			dir_path = self.AttemptLoad(os.path.join("D:\\GitHub\\besiege-creation-importer\\modules\\CustomBlocks", block_name), ".obj")
			bpy.ops.import_scene.obj(filepath=dir_path)
			block = list(bpy.context.selected_objects)[0]
			block.name = str(hash(block.name))
			clone = block.copy()
			self.custom_import_object_list.update({block_name : {'model' : block.name}})
			bpy.data.collections[bpy.context.view_layer.active_layer_collection.name].objects.link(clone)
			self.temp_obj_list.append(block)
			return clone
		else:
			clone = bpy.data.objects[self.custom_import_object_list[block_name]['model']].copy()
			bpy.data.collections[bpy.context.view_layer.active_layer_collection.name].objects.link(clone)
			return clone
			

	def BlockDrawTypeLineType(self, block:Block, component:Component, vanilla_skins=False) -> 'Object':
		'''
		This is the draw type intended for line type blocks. These blocks have a position, scale, rotation, start position,
		end position, start rotation and end rotation. These values are used to draw a block that connects 2 points.
		Parameters
			block : Block : Block to import
			component : Component : Component to import
			vanilla_skins : Bool : Import vanilla skins
		Returns : Object
		Exceptions : None
		'''
		texture_path = self.FetchModel(block.code_name, component.skin_id, component.skin_name, only_texture=True)
		material = self.GenerateMaterial(component, texture_path, component.skin_name)

		# TODO Remove hard coded file paths
		# TODO Fix warped brace cube issues
		# Import the connector, start and end objects
		connector = self.ImportCustomModel(component.line_type_middle)
		start = self.ImportCustomModel(component.line_type_end)
		end = self.ImportCustomModel(component.line_type_start)

		# Set the material for models
		start.active_material = material
		end.active_material = material
		connector.active_material = material

		# Create the empty object. We'll be using it as
		# a parent
		parent = bpy.data.objects.new( "empty", None)
		parent.empty_display_size = 0.25
		parent.empty_display_type = 'CUBE'
		bpy.data.collections[bpy.context.view_layer.active_layer_collection.name].objects.link(parent)

		# Set the location of the blocks
		start.location = Vector(block.GetLineStartPosition())
		end.location = Vector(block.GetLineEndPosition())
		connector.location = Vector(block.GetLineStartPosition())
		parent.location = Vector((block.getVectorPosition()))

		# Set parents of the start, end
		# and connector block to the empty object
		start.parent = parent
		end.parent = parent
		connector.parent = parent

		# Set the rotation of the parent, So it'll
		# transforming the other child blocks as well
		parent.rotation_mode = 'QUATERNION'
		parent.rotation_quaternion = Quaternion(block.getQuarternion()).inverted()
		parent.rotation_mode = 'XYZ'

		# Set the name of the blocks. We'll be
		# using the GUID in the name so it'll be
		# easier to debug
		parent.name = "Brace_" + block.guid
		start.name = "StartPoint_" + block.guid
		end.name = "EndPoint_" + block.guid
		connector.name = "Connector_" + block.guid

		# Set the rotation to the start and end rotation.
		start.rotation_euler.x -= block.GetLineStartRotation()[0]
		start.rotation_euler.y -= block.GetLineStartRotation()[1]
		start.rotation_euler.z -= block.GetLineStartRotation()[2]
		end.rotation_euler.x -= block.GetLineEndRotation()[0]
		end.rotation_euler.y -= block.GetLineEndRotation()[1]
		end.rotation_euler.z -= block.GetLineEndRotation()[2]

		# Set the rotation mode of the end and start block
		start.rotation_mode = 'YXZ'
		end.rotation_mode = 'YXZ'

		# Set the scale of the parent object,
		# which will deform the blocks
		parent.scale = block.getScale()

		# We'll be using a Track-To contraint to point the start block at the end block.
		# So here we'll be creating the contraint and configuring it to point at the end
		# block
		constraint = connector.constraints.new('TRACK_TO')
		constraint.track_axis = "TRACK_Y"
		constraint.up_axis = "UP_X"
		constraint.target = end
		distance = self.GetDistance([start, end])
		connector.dimensions[1] = distance

		# TODO Calibrate distance threshold to delete connector block and end block
		# If the length between the starting and end block is less than a specific value
		# the end and the connector block will be deleted. This specific value... we dont
		# know
		if distance < 0.15:
			bpy.data.objects.remove(connector)
			bpy.data.objects.remove(end)
		return parent

	def RotateGlobal(self, obj, radian, axis) -> None:
		'''
		Rotate an object on the global axis
		Parameters
			obj : Object : Object to rotate
			radian : float : Rotation value in radians
			axis : string : Rotation axies
		Return : None
		Exceptions : None
		'''
		# This thing is not working. and I have no idea how to make it
		# work. I hate it... I hate fucking braces so much...
		# you can also use as axis Y,Z or a custom vector like (x,y,z)
		rot_mat = Matrix.Rotation(radian, 4, axis) 
		# decompose world_matrix's components, and from them assemble 4x4 matrices
		orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
		orig_loc_mat = Matrix.Translation(orig_loc)
		orig_rot_mat = orig_rot.to_matrix().to_4x4()
		orig_scale_mat = Matrix.Scale(orig_scale[0],4,(1,0,0)) * Matrix.Scale(orig_scale[1],4,(0,1,0)) * Matrix.Scale(orig_scale[2],4,(0,0,1))
		# assemble the new matrix
		obj.matrix_world = orig_loc_mat * rot_mat * orig_rot_mat * orig_scale_mat 

	def GetDistance(self, objs:list) -> float:
		'''
		Get the distance between 2 objects
		Parameters
			objs : list : List of objects
		Return : float
		Exceptions : None
		'''
		l = []
		for item in objs:
			l.append(item.location)
		# TODO Refactor GetDistance() to use global position
		distance = sqrt( (l[0][0] - l[1][0])**2 + (l[0][1] - l[1][1])**2 + (l[0][2] - l[1][2])**2)
		return distance

	def BlockDrawTypeDefault(self, block:Block, component:Component, vanilla_skins=False) -> 'Object':
		'''
		Import a block with the draw type, default. Default blocks are simply, imported and oriented correctly.
		It is the simplest type of object to draw. In addition to importing it, the materials are also generated
		Parameters
			block : Block : Block class to import
			component : Component : Component to import
			vanilla_skins : Bool : Use vanilla skins
		Return : Object
		Exceptions : None
		'''
		# # TODO Refactor `blenapi.BlockDrawTypeDefault()`
		# # This can be done by importing a block, and then instead of importing it again from
		# # disk, the same block can be duplicated again. This will give a HUGE performance boost
		current_obj = self.LookupObject(block, component, vanilla_skins)
		# Set the scale according to the BSG file.
		current_obj.scale = block.getScale()
		# Set the rotation according to the BSG file.
		# Note: This is described in the BSG file in Quarternions
		current_obj.rotation_mode = 'QUATERNION'
		current_obj.rotation_quaternion = Quaternion(block.getQuarternion()).inverted()
		current_obj.rotation_mode = 'XYZ'
		# Set the location of the object according to the BSG file
		current_obj.location = Vector(block.getVectorPosition())
		# Rename the object.
		# The name will have the block name and the block guid.
		# Having the GUID will be helpful for debugging
		current_obj.name = component.base_source + "_" + block.guid
		return current_obj

	def CreateParent(self, obj_list:list) -> None:
		'''
		Parent all objects imported to a single empty
		Parameters
			obj_list : list : List of objects to parent
		Return : None
		Exceptions : None
		'''
		# TODO Finish `blenapi.CreateParent()`
		o = bpy.data.objects.new( "Parent", None )
		bpy.context.scene.objects.link(o)
		o.empty_draw_size = 5
		o.empty_draw_type = 'PLAIN_AXES'


	def FetchModel(self, block_name:str, skin_id:str, skin_name='Template', only_texture=False) -> None:
		'''
		Finds the absolute path to the image and model of the skin needed.
		Parameters
			block_name : string : Name of the block to import (the name used in code)
			skin_id : string : Steam workshop ID
			skin_name : string : Name of the skin
			only_texture : boolean : Only fetch the texture of the block
		Return : Tuple or String
		Exceptions : None
		'''
		# TODO Add skin not found exception
		# TODO Refactor `blenapi.FetchModel()`
		dlist = '?'
		if skin_name != 'Template':
			try:
				d = os.path.join(self.workshop_store, skin_id)
				dlist = [os.path.join(d, o) for o in os.listdir(d) if os.path.isdir(os.path.join(d,o))]
			except FileNotFoundError:
				pass
		model_dirs = [
			os.path.join(self.workshop_store, skin_id, dlist[0], block_name),
			os.path.join(self.game_store, skin_name, block_name),
			os.path.join(self.backup_store, block_name)
		]
		for cdir in model_dirs:
			result_t = self.AttemptLoad(cdir, '.png')
			result_o = self.AttemptLoad(cdir, '.obj')
			if result_t and result_o: return [result_o, result_t]
			if only_texture and result_t: return result_t
			print('\t\t >> Cannot find in {}'.format(cdir))
		return ""

	def AttemptLoad(self, directory:str, extension:str) -> bool:
		'''
		Try to see if a file with a certain extenson exists in the folder
		Parameters
			directory : string : The directory to search for
			extension : string : Extension to look for
		Return : Boolean
		Exceptions : None
		'''
		# This method is used to find an obj or png file in the texture folder. Because Besiege
		# allows the png file to have any name and the only thing that matters is the extension.
		# So we'll just take the first file that matches the requirements
		try:
			for f in os.listdir(directory):
				if f.endswith(extension):
					return os.path.join(directory, f)
		except FileNotFoundError:
			return False
		return False

	def GenerateMaterial(self, block:Block, texture_path:str, skin_name:str) -> 'Material':
		'''
		Generate material for a block. If the material already exists, return that.
		Parameters
			block : Block : The block class for which the material should be generated
			texture_path : String : The path to the object texture. ie a PNG for something
			skin_name : String : The name of the skin used
		Return : Material
		Exceptions : None
		'''
		# Ok time to generate the material. So first We generate the material and then we return it... Its that simple
		# TODO : Add NodeGroup setup
		mat_name = block.base_source + skin_name + "Material"
		for m in bpy.data.materials:
			if str(mat_name).__eq__(str(m.name)): return m
		return MaterialCatalog.DefaultMaterial(block, texture_path, mat_name).Generate()