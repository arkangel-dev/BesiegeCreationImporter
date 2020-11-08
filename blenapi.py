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

dev_mode = True

if dev_mode:
	import Block
	import Component
	from MaterialCatalog import DefaultMaterial
	from bsgreader import Reader
else:
	from .bsgreader import Reader
	from .Component import Component
	from .Block import Block
	from .MaterialCatalog import *

class BlenderAPI():
	# So we are defining 3 directories. One for the workshop skin directory, one 
	# for the skin folder in the game data skin directory and one to use as the backup
	# preferably the template vanilla skin from the game data directory. Note that the first 2
	# are pointing to a directory with multiple skins whereas the backup store is defining a single skin pack
	workshop_store = ""
	game_store = ""
	backup_store = ""
	status = ""
	custom_block_dir = ""
	status_description = []
	temp_obj_list = []
	import_object_list = {}
	custom_import_object_list = {}

	setting_GenerateMaterial = False
	setting_StopImportOnMissingskin = False
	setting_use_vanilla_skin = False
	setting_join_line_components = False
	setting_hide_parent_empties = False
	setting_brace_threshhold = 0.5
	
	def __init__(self, ws_store, game_store, backup):
		self.status = 'OK'
		self.workshop_store = ws_store
		self.game_store = game_store
		self.backup_store = backup
		self.custom_block_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'CustomBlocks')
		if dev_mode: self.custom_block_dir = "D:\\GitHub\\besiege-creation-importer\\modules\\CustomBlocks"

	def LookupObject(self, block:Block, component:Component, vanilla_skins=False) -> 'Object':
		'''	
		Tries to find an object in the scene. If it does not exist, import it and add it
		to the logbook
		Parameters
			block : Block : Block to import
			component : Component : Component of the block to import
			vanilla_skins : Boolean : If true, will use vanilla skins
		'''

		# if the block is not in the object list, create a new key
		# and update it...
		sid = str(hash(block.block_id + component.skin_name + block.flipped)) if not self.setting_use_vanilla_skin else str(hash(block.block_id + "Template" + block.flipped))
		if sid in self.import_object_list.keys():
			new_obj = bpy.data.objects[self.import_object_list[sid]].copy()
			new_obj.data = bpy.data.objects[self.import_object_list[sid]].data.copy()
			bpy.data.collections[bpy.context.view_layer.active_layer_collection.name].objects.link(new_obj)
			return new_obj
		else:
			# ...if we cannot find the skin we need, we'll import it
			model = self.FetchModel(component.base_source, component.skin_id, component.skin_name) if not self.setting_use_vanilla_skin else self.FetchModel(component.base_source, "0", "Template")
			for obj in bpy.context.selected_objects: obj.select_set(False)
			bpy.ops.import_scene.obj(filepath=model[0])
			bpy.context.view_layer.objects.active = list(bpy.context.selected_objects)[0]
			bpy.ops.object.join()
			current_obj = list(bpy.context.selected_objects)[0]
			self.ClearExtraMaterialSlots(current_obj)
			[bpy.data.materials.remove(m) for m in current_obj.data.materials]
			if self.setting_GenerateMaterial:
				current_obj.active_material = self.GenerateMaterial(component, model[1], component.skin_name if not self.setting_use_vanilla_skin else 'Template')
			# Set the offset scale data from the JSON file
			current_obj.scale = [component._offset_scale_x, component._offset_scale_z, component._offset_scale_y]
			# special offset for propellers...
			# I'll think of a way to offset this in the json file...
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
			newobj.data = current_obj.data.copy()
			bpy.data.collections[bpy.context.view_layer.active_layer_collection.name].objects.link(newobj)
			skin_data_template = {sid : current_obj.name}
			self.import_object_list.update(skin_data_template)
			return newobj

	def ImportCreation(self, path:str, vanilla_skins=False, create_parent=False, generate_material=True, stop_import_on_missing_skin=False, join_line_components=False, hide_parent_empties=True, bracethreshold=0.5) -> None:
		'''
		Import a Besiege Creation File (bsg file).
		Parameters
			path : string : Path to the bsg file
			vanilla_skins : bool : Use vanilla skins instead of the skins defined in the bsg file
			create_parent : Parent all imported objects to an empty after importing them
		Return : None
		Exceptions : None
		'''

		self.setting_GenerateMaterial = generate_material
		self.setting_StopImportOnMissingskin = stop_import_on_missing_skin
		self.setting_join_line_components = join_line_components
		self.setting_hide_parent_empties = hide_parent_empties
		self.setting_brace_threshhold = bracethreshold
		self.setting_use_vanilla_skin = vanilla_skins

		# First we'll reset the object history because if we imported a model before this cycle,
		# the import model methods will try to duplicate objects that does not exist
		self.import_object_list = {}
		self.custom_import_object_list = {}

		# Create a reader instance. This class is used to read the data from the BSG file and
		# create a list of Block classes
		ReaderInstance = Reader(path)
		block_list = ReaderInstance.ReadBlockData()
		imported_list = []

		print("Importing {} blocks...".format(len(block_list)))

		# These lists will be used to find objects that were imported to
		# parent them to an empty object once the import process has been
		# completed
		normal_draw = []
		line_draw = []

		# Catagorize all the blocks. We separate them by their draw type.
		# Some objects will have to "drawn" differently than others.
		for block in block_list:
			if block.block_id in ['7','9','45']:
				line_draw.append(block)
			else:
				normal_draw.append(block)

		# This is for drawing "normal type blocks". These blocks have to be simply imported
		# offset, rotated and positioned correctly. Nothing else. These are rather simple to import
		for block in normal_draw:
			for component in block.components:
				imported_list.append(self.BlockDrawTypeDefault(block, component, vanilla_skins))
		
		# This is for drawing "line type blocks". These blocks are a bit more complicated. These blocks
		# have a position and rotation for start and end blocks. These blocks are positioned and rotated.
		# But due to fact people use exploit this to warp blocks, its a fucking nightmare to get it to work
		for block in line_draw:
			for component in block.components:
				imported_list.append(self.BlockDrawTypeLineType(block, component, vanilla_skins))	

		# There is also the "surface type block". But we dont speak of that... (╬▔皿▔)╯	
		
		# Then we get rid of the temp objects because we no longer need them :)
		for block in self.temp_obj_list:
			bpy.data.objects.remove(block)
		self.temp_obj_list.clear()
		

	def ImportCustomModel(self, block_name:str) -> 'Object':
		'''
		Imports models from the models the addon library.
		Parameters
			block_name : string : Name of the block to import
		Exceptions : None
		Return : None
		'''
		# This will be used to import objects that aren't taken from the skin folder. While besiege does allow you to change the texture
		# of blocks such as braces, contract spring block and rope and winch blocks, you cannot change the models themselves. They come with
		# the game game. So we'll have to make our own models and pack them with the addon.
		if not block_name in self.custom_import_object_list.keys():
			dir_path = self.AttemptLoad(os.path.join(self.custom_block_dir, block_name), ".obj")
			bpy.ops.import_scene.obj(filepath=dir_path)
			block = list(bpy.context.selected_objects)[0]
			block.name = str(hash(block.name))
			clone = block.copy()
			clone.data = block.data.copy()
			bpy.data.collections[bpy.context.view_layer.active_layer_collection.name].objects.link(clone)
			self.temp_obj_list.append(block)
			self.custom_import_object_list.update({block_name : {'model' : block.name}})
			return clone
		else:
			clone = bpy.data.objects[self.custom_import_object_list[block_name]['model']].copy()
			clone.data = bpy.data.objects[self.custom_import_object_list[block_name]['model']].data.copy()
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
		
		# Import the connector, start and end objects
		connector = self.ImportCustomModel(component.line_type_middle)
		start = self.ImportCustomModel(component.line_type_end)
		end = self.ImportCustomModel(component.line_type_start)

		# Set the material for models
		if self.setting_GenerateMaterial:
			material = self.GenerateMaterial(component, texture_path, component.skin_name) if not self.setting_use_vanilla_skin else self.GenerateMaterial(component, texture_path, "Template")
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
		


		# Set the rotation of the parent, So it'll
		# transforming the other child blocks as well
		parent.rotation_mode = 'QUATERNION'
		parent.rotation_quaternion = Quaternion(block.getQuarternion()).inverted()
		parent.rotation_mode = 'XYZ'

		# Set the name of the blocks. We'll be
		# using the GUID in the name so it'll be
		# easier to debug
		parent.name = "LineType_" + block.guid
		start.name = "StartPoint_" + block.guid
		end.name = "EndPoint_" + block.guid
		connector.name = "Connector_" + block.guid

		# Reset the parent transformation data so that
		# the rotation is (0,0,0). Basically doing
		# parenting an object while keeping the transformation
		self.ResetParentTransformRotation(end, parent)
		self.ResetParentTransformRotation(start, parent)

		# Set the rotation of the start block
		start_rot = Euler(block.GetLineStartRotation())
		start_rot.rotate(block.GetGlobalMachineRotation().inverted())
		start.rotation_euler = start_rot
		start.rotation_mode = 'ZXY'
		self.InvertRotation(start)

		# Set the rotation of the end block
		end_rot = Euler(block.GetLineEndRotation())
		end_rot.rotate(block.GetGlobalMachineRotation().inverted())
		end.rotation_euler = end_rot
		end.rotation_mode = 'ZXY'
		self.InvertRotation(end)

		# Set the scale of the parent object,
		# which will deform the blocks
		parent.scale = block.getScale()

		# We'll be using a Track-To contraint to point the start block at the end block.
		# So here we'll be creating the contraint and configuring it to point at the end
		# block
		connector.parent = parent
		self.ResetParentTransformRotation(connector, parent)
		constraint = connector.constraints.new('TRACK_TO')
		constraint.track_axis = "TRACK_Y"
		constraint.up_axis = "UP_X"
		constraint.target = end
		distance = self.GetDistance([start, end])
		connector.dimensions[1] = distance

		# If the length between the starting and end block is less than a specific value
		# the end and the connector block will be deleted. This specific value... we dont
		# know

		if distance < self.setting_brace_threshhold:
			bpy.data.objects.remove(connector)
			bpy.data.objects.remove(end)

		elif self.setting_join_line_components:
			for obj in list(bpy.context.selected_objects): obj.select_set(False)
			bpy.context.view_layer.objects.active = start
			connector.select_set(True)
			start.select_set(True)
			end.select_set(True)
			bpy.ops.object.join()

		if self.setting_hide_parent_empties: parent.hide_set(True)
		
		return parent

	def ResetParentTransformRotation(self, obj, parent):
		try:
			bpy.context.view_layer.update()
			ogloc = (obj.matrix_world.to_translation().x, obj.matrix_world.to_translation().y, obj.matrix_world.to_translation().z)
			obj.parent = None
			obj.location = Vector(ogloc)
			obj.parent = parent
			obj.matrix_parent_inverse = parent.matrix_world.inverted()
		except ValueError:
			print("Warning : ResetParentTransformRotation threw ValueError exception with obj {}".format(obj.name))

	def InvertRotation(self, obj):
		original_rot = obj.rotation_mode
		obj.rotation_mode = 'QUATERNION'
		obj.rotation_quaternion = obj.rotation_quaternion.inverted()
		obj.rotation_mode = original_rot

	def RotateGlobal(self, obj, radian, axis) -> None:
		from math import radians
		from mathutils import Matrix
		obj.rotation_euler = (obj.rotation_euler.to_matrix() @ Matrix.Rotation(radian, 3, axis)).to_euler()

	def ClearExtraMaterialSlots(self, obj):
		obj.active_material_index = 0
		for x in range(len(obj.material_slots)):
			bpy.ops.object.material_slot_remove({'object': obj})

	def GetDistance(self, objs:list) -> float:
		'''
		Get the distance between 2 objects
		Parameters
			objs : list : List of objects
		Return : float
		Exceptions : None
		'''
		l = []
		bpy.context.view_layer.update()
		for item in objs:
			l.append(item.matrix_world.to_translation())
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
		return DefaultMaterial(block, texture_path, mat_name).Generate()