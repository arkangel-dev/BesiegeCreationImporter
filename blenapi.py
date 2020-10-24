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
from MaterialCatalog import *
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
	
	def __init__(self, ws_store, game_store, backup):
		self.status = 'OK'
		self.workshop_store = ws_store
		self.game_store = game_store
		self.backup_store = backup

	def ImportCreation(self, path, vanilla_skins=False, create_parent=False):
		ReaderInstance = Reader(path)
		block_list = ReaderInstance.ReadBlockData() # read the block data from the bsgreader class
		imported_list = []

		for block in block_list:
			for comp in block.components:
				print("Block {} >> Component {} ({})".format(block.block_id, comp.base_source, id(comp)))
		
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
				current_obj = self.BlockDrawTypeDefault(block, component, vanilla_skins)
		
		for block in line_draw:
			for component in block.components:
				current_obj = self.BlockDrawTypeLineType(block, component, vanilla_skins)
		
		

	def BlockDrawTypeLineType(self, block, component, vanilla_skins=False):

		bpy.ops.import_scene.obj(filepath="D:\\GitHub\\besiege-creation-importer\\modules\\CustomBlocks\\Connector\\connector.obj")
		connector = bpy.context.selected_objects[0]
		connector.location= Vector((0,0,0))

		# bpy.ops.mesh.primitive_cube_add(scale=(0.45, 0.45, 0.45), location=(0,0,0))
		bpy.ops.import_scene.obj(filepath="D:\\GitHub\\besiege-creation-importer\\modules\\CustomBlocks\\BraceSectionA\\brace_cube.obj")
		start = bpy.context.selected_objects[0]
		# bpy.ops.mesh.primitive_cube_add(scale=(0.45, 0.45, 0.45), location=(0,0,0))
		bpy.ops.import_scene.obj(filepath="D:\\GitHub\\besiege-creation-importer\\modules\\CustomBlocks\\BraceSectionA\\brace_cube.obj")
		end = bpy.context.selected_objects[0]

		parent = bpy.data.objects.new( "empty", None)
		bpy.context.scene.collection.objects.link(parent)
		parent.empty_display_size = 0.25
		parent.empty_display_type = 'CUBE'


		start.parent = parent
		end.parent = parent
		connector.parent = parent


		parent.location = Vector((block.getVectorPosition()))
		parent.scale = block.getScale()
		

		start.location = Vector(block.GetLineStartPosition())
		end.location = Vector(block.GetLineEndPosition())
		connector.location = Vector(block.GetLineStartPosition())
		# start.rotation_euler = Euler(block.GetLineStartRotation())


		end.rotation_mode = 'XYZ'
		end.rotation_euler = Euler(block.GetLineEndRotation())

		# start.select_set(True)
		# end.select_set(True)
		# # bpy.ops.object.select_all(action='DESELECT')
		# bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

		qtrans = Quaternion(block.getQuarternion())
		qtrans.invert()
		parent.rotation_mode = 'QUATERNION'
		parent.rotation_quaternion = qtrans
		parent.rotation_mode = 'XYZ'

		constraint = connector.constraints.new('TRACK_TO')
		constraint.track_axis = "TRACK_Y"
		constraint.up_axis = "UP_X"
		constraint.target = end
		distance = self.GetDistance([start, end])
		connector.dimensions[1] = distance



		hash_key = str(hash(random.randint(1000, 9999)))

		parent.name = "Parent_" + hash_key
		start.name = "StartPoint_" + hash_key
		end.name = "EndPoint_" + hash_key
		connector.name = "Connector_" + hash_key

		bpy.ops.object.select_all(action='DESELECT')
		end.select_set(True)
		# end.clrParent(mode=2)
		bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
		end.rotation_mode = 'XYZ'
		end.rotation_euler = Euler(block.GetLineEndRotation())
		if distance < 0.15:
			bpy.data.objects.remove(connector)
			bpy.data.objects.remove(end)
		return ""

	def GetDistance(self, objs):
		l = []  # we store the loacation vector of each object
		for item in objs:
			l.append(item.location)

		distance = sqrt( (l[0][0] - l[1][0])**2 + (l[0][1] - l[1][1])**2 + (l[0][2] - l[1][2])**2)
		return distance

	def BlockDrawTypeDefault(self, block, component, vanilla_skins=False):
		hash_key = str(hash(random.randint(1000, 9999)))
		bpy.ops.object.select_all(action='DESELECT')
		model = self.FetchModel(component.base_source, component.skin_id, component.skin_name) if not vanilla_skins else self.FetchModel(component.base_source, 'Template', 'Template')
		bpy.ops.import_scene.obj(filepath=model[0])
		current_obj = bpy.context.selected_objects[0]
		for m in current_obj.data.materials:
			bpy.data.materials.remove(m)
		texture_name = component.skin_name if not vanilla_skins else 'Template'
		new_mat = self.GenerateMaterial(component, model[1], texture_name)
		current_obj.data.materials.append(new_mat)
		current_obj.active_material = new_mat
		# get the offset transform values from the skin model website
		preset_pos = [component._offset_translate_x, component._offset_translate_y, component._offset_translate_z]
		preset_rot = [component._offset_rotation_x, component._offset_rotation_y, component._offset_rotation_z]
		preset_sca = [component._offset_scale_x, component._offset_scale_z, component._offset_scale_y]
		current_obj.scale = (preset_sca)
		# special offset for propellers...
		# I'll think of a way to offset this in the json file...
		if (block.block_id in ['26','55']):
			preset_rot[1] += 23 if block.flipped != 'True' else -23
		# rotate according to the offset
		bpy.ops.transform.rotate(value=math.radians(preset_rot[0]), orient_axis='X', orient_type='LOCAL', orient_matrix_type='LOCAL')
		bpy.ops.transform.rotate(value=math.radians(preset_rot[1]), orient_axis='Y', orient_type='LOCAL', orient_matrix_type='LOCAL')
		bpy.ops.transform.rotate(value=math.radians(preset_rot[2]), orient_axis='Z', orient_type='LOCAL', orient_matrix_type='LOCAL')
		# translate according to the offset
		offset_x = (preset_pos[0])
		offset_y = (preset_pos[1])
		offset_z = (preset_pos[2])
		current_obj.location = Vector((offset_x, offset_y, offset_z))
		bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
		# scale
		current_obj.scale = block.getScale()
		# rotate
		current_obj.rotation_mode = 'QUATERNION'
		qtrans = Quaternion(block.getQuarternion())
		qtrans.invert()
		current_obj.rotation_quaternion  = qtrans
		current_obj.rotation_mode = 'XYZ'
		# translate according to the BSG file
		current_obj.location = Vector(block.getVectorPosition())
		current_obj.name = component.base_source + "_" + hash_key
		return current_obj

	def CreateParent(self, obj_list):
		o = bpy.data.objects.new( "Parent", None )
		bpy.context.scene.objects.link(o)
		o.empty_draw_size = 5
		o.empty_draw_type = 'PLAIN_AXES'


	def FetchModel(self, block_name, skin_id, skin_name='Template'):

		dlist = 'null'
		if skin_name != 'Template':
			try:
				d = os.path.join(self.workshop_store, skin_id)
				dlist = [os.path.join(d, o) for o in os.listdir(d) if os.path.isdir(os.path.join(d,o))]
			except FileNotFoundError:
				pass
		model_dirs = [ # create a list of the directories to check

			os.path.join(self.workshop_store, skin_id, dlist[0], block_name),
			os.path.join(self.game_store, skin_name, block_name),
			os.path.join(self.backup_store, block_name),
			os.path.join("D:\\GitHub\\besiege-creation-importer\\modules\\CustomBlocks", block_name)
		]

		for cdir in model_dirs:
			result_t = self.AttemptLoad(cdir, '.png')
			result_o = self.AttemptLoad(cdir, '.obj')
			if result_t and result_o: return [result_o, result_t]
			print('\t\t >> Cannot find in {}'.format(cdir))
		return ""

	def AttemptLoad(self, directory, extension):
		try:
			for f in os.listdir(directory):
				if f.endswith(extension):
					return os.path.join(directory, f)
		except FileNotFoundError:
			return False
		return False

	def GenerateMaterial(self, block, texture_path, texture_name):
		# Ok time to generate the material. So first We generate the material and then we return it... Its that simple
		# TODO : Add NodeGroup setup
		mat_name = block.base_source + texture_name + "Material"
		for m in bpy.data.materials:
			if mat_name == m.name:
				return m
		generator = DefaultMaterial(block, texture_path, mat_name)
		return generator.Generate()



	