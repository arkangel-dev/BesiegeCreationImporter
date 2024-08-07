import bpy
import os
import numpy as np
import math
import json
import time
import xml.etree.ElementTree as ET
import random
import bmesh
from mathutils import Euler, Quaternion, Vector, Matrix
from math import radians, pi, sqrt
from pathlib import Path

dev_mode = False

if dev_mode:
	import Component
	from Bezier import Bezier
	from Block import Block, BuildSurface, BuildSurfaceEdge
	from MaterialCatalog import MaterialList, NodeGroups
	from bsgreader import Reader
else:
	from .bsgreader import Reader
	from .Bezier import Bezier
	from .Component import Component
	from .Block import Block, BuildSurface, BuildSurfaceEdge
	from .MaterialCatalog import MaterialList, NodeGroups

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
	block_list = []
	imported_materials = []
	import_object_list = {}
	custom_import_object_list = {}

	setting_GenerateMaterial = False
	setting_use_vanilla_skin = False
	setting_join_line_components = False
	setting_hide_parent_empties = False
	setting_use_node_groups = False
	setting_merge_decor_blocks = True
	setting_skip_surface_blocks = False
	setting_brace_threshhold = 0.5
	setting_surface_resolution = 0.1
	setting_surface_thickness_multiplier = 0.0
	setting_clean_up_action = 'DO_NOTHING'
	setting_grouping_mode = 'SAME_CONFIG'
	setting_node_setup = 'PRINCIPLED_BDSF'
	
	
	def __init__(self, ws_store, game_store, backup):
		self.status = 'OK'
		self.workshop_store = ws_store
		self.game_store = game_store
		self.backup_store = backup
		self.custom_block_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'CustomBlocks')
		if dev_mode: self.custom_block_dir = "D:\\GitHub\\besiege-creation-importer\\modules\\CustomBlocks"

	def ImportCreation(
			self,
			vanilla_skins=False,
			create_parent=False,
			generate_material=True, 
			merge_decor_blocks=False,
			use_node_groups=False,
			join_line_components=False,
			hide_parent_empties=True,
			skip_surfaces=False,
			node_grouping_mode='SAME_CONFIG',
			node_group_setup='PRINCIPLED_BDSF',
			line_type_cleanup='DO_NOTHING',
			bracethreshold=0.5,
			surface_block_resolution=0.1,
			surface_block_thickness_mult=0.0
		) -> None:
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
		self.setting_join_line_components = join_line_components
		self.setting_hide_parent_empties = hide_parent_empties
		self.setting_brace_threshhold = bracethreshold
		self.setting_use_vanilla_skin = vanilla_skins
		self.setting_clean_up_action = line_type_cleanup
		self.setting_use_node_groups = use_node_groups
		self.setting_grouping_mode = node_grouping_mode
		self.setting_node_setup = node_group_setup
		self.setting_merge_decor_blocks = merge_decor_blocks
		self.setting_surface_resolution = surface_block_resolution
		self.setting_surface_thickness_multiplier = surface_block_thickness_mult
		self.setting_skip_surface_blocks = skip_surfaces

		# First we'll reset the object history because if we imported a model before this cycle,
		# the import model methods will try to duplicate objects that does not exist
		self.import_object_list = {}
		self.custom_import_object_list = {}
		self.imported_materials = []

		# Create a reader instance. This class is used to read the data from the BSG file and
		# create a list of Block classes
		
		imported_list = []

		print("Importing {} blocks...".format(len(self.block_list)))

		# These lists will be used to find objects that were imported to
		# parent them to an empty object once the import process has been
		# completed
		normal_draw = []
		line_draw = []
		surface_draw = []

		# Catagorize all the blocks. We separate them by their draw type.
		# Some objects will have to "drawn" differently than others.
		for block in self.block_list:
			if block.block_id in ['7','9','45','75']:
				line_draw.append(block)
			elif block.block_id in ['73']:
				surface_draw.append(block)
			else:
				normal_draw.append(block)


		# This is for drawing "normal type blocks". These blocks have to be simply imported
		# offset, rotated and positioned correctly. Nothing else. These are rather simple to import
		for block in normal_draw:
			imported_list.extend(self.ProcessDefaultTypeBlock(block))
		
		# This is for drawing "line type blocks". These blocks are a bit more complicated. These blocks
		# have a position and rotation for start and end blocks. These blocks are positioned and rotated.
		# But due to fact people use exploit this to warp blocks, its a fucking nightmare to get it to work
		for block in line_draw:
			for component in block.components:
				imported_list.append(self.BlockDrawTypeLineType(block, component, vanilla_skins))	

		# There is also the "surface type block". But we dont speak of that... (╬▔皿▔)╯	
		# Scratch that... ProNou has finished the surface blocks so I have an idea how I can finish up
		# surface blocks. Its going to be fucking nightmare (ノ｀Д)ノ
		if not self.setting_skip_surface_blocks:
			for block in surface_draw:
				imported_list.append(self.BlockDrawTypeSurfaceType(block, vanilla_skins))
		
		# Then we get rid of the temp objects because we no longer need them :)
		for block in self.temp_obj_list:
			try:
				bpy.data.objects.remove(block)
			except ReferenceError:
				pass
		self.temp_obj_list.clear()
		return {
			'imported_materials' : self.imported_materials,
			'imported_objects' : imported_list
		}
	
	def ProcessDefaultTypeBlock(self, block:Block) -> list:
		base_block = None
		decor_blocks = []
		return_list = []
		print('Processing block {}'.format(block.code_name))
		for component in block.components:
			imobject = self.BlockDrawTypeDefault(block, component, self.setting_use_vanilla_skin)
			if component.group == 'BASE':
				base_block = imobject
			elif component.group == 'DECOR':
				decor_blocks.append(imobject)
			imobject.select_set(True)
		if self.setting_merge_decor_blocks:
			for obj in bpy.context.selected_objects: obj.select_set(False)
			for obj in decor_blocks: obj.select_set(True)
			base_block.select_set(True)
			if len(decor_blocks) > 0:
				bpy.context.view_layer.objects.active = base_block
				bpy.ops.object.join()
			return [bpy.context.selected_objects[0]]

		return_list.append(base_block)
		return_list.extend(decor_blocks)
		return return_list


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
		sid = str(hash(component.base_source + component.skin_name + block.flipped)) if not self.setting_use_vanilla_skin else str(hash(component.base_source + "Template" + block.flipped))
		print(self.import_object_list)
		if sid in self.import_object_list.keys():
			new_obj = bpy.data.objects[self.import_object_list[sid]].copy()
			new_obj.data = bpy.data.objects[self.import_object_list[sid]].data.copy()
			bpy.data.collections[bpy.context.view_layer.active_layer_collection.name].objects.link(new_obj)
			return new_obj
		else:
			print("Object not found : {}".format(component.base_source))
			# ...if we cannot find the skin we need, we'll import it
			model = self.FetchSkinFile(component.base_source, component.skin_id, component.skin_name, only_model=True) if not self.setting_use_vanilla_skin else self.FetchSkinFile(component.base_source, "0", "Template", only_model=True)
			
			for obj in bpy.context.selected_objects: obj.select_set(False)

			# API changed sometime ago...
			# bpy.ops.import_scene.obj(filepath=model)
			bpy.ops.wm.obj_import(filepath=model)
			if len(bpy.context.selectable_objects) > 1:
				bpy.context.view_layer.objects.active = list(bpy.context.selected_objects)[0]
				bpy.ops.object.join()
			current_obj = list(bpy.context.selected_objects)[0]
			[bpy.data.materials.remove(m) for m in current_obj.data.materials]
			self.ClearExtraMaterialSlots(current_obj)
			if self.setting_GenerateMaterial:
				current_obj.active_material = self.GenerateMaterial(block ,component, component.skin_name if not self.setting_use_vanilla_skin else 'TemplateA')
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

	def ReadBSGData(self, path:str):
		ReaderInstance = Reader(path)
		st_t = time.time()
		data = ReaderInstance.ReadBlockData()
		self.block_list = data['RETURN_LIST']
		et_t = time.time()
		print('Read complete in {}'.format(et_t - st_t))
		return data



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
			print("Object not found : {}".format(block_name))
			dir_path = self.SearchInDirectory(os.path.join(self.custom_block_dir, block_name), ".obj")
			# bpy.ops.import_scene.obj(filepath=dir_path)
			bpy.ops.wm.obj_import(filepath=dir_path)
			block = list(bpy.context.selected_objects)[0]
			block.name = str(hash(block.name))
			[bpy.data.materials.remove(m) for m in block.data.materials]
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


	def BlockDrawTypeSurfaceType(self, surface:BuildSurface, vanilla_skins=False) -> 'Object':
		'''
		This function will generate a surface based off the data from a BuildSurface object.
		Parameters:
			surface : BuildSurface : Suface object containing the data
			vanilla_skins : boolean : Should the surface be imported with vanilla skins?
		'''
		print("Interpolating surface {}...".format(surface.guid))

		# Create mesh and give it an object instance...
		mesh = bpy.data.meshes.new("BuildSurface_" + surface.guid)
		mesh_object = bpy.data.objects.new(mesh.name, mesh)
		bpy.data.collections[bpy.context.view_layer.active_layer_collection.name].objects.link(mesh_object)

		# We will store the points we will actually plot in this list
		mesh_vertex_list = []
		
		# Generate a list start, end and mid points...
		curve_start_points = self.GenerateCurve(surface.edge_a)
		curve_mid_points = self.GenerateCurve(surface.edge_b)
		curve_end_points = self.GenerateCurve(surface.edge_c)

		# mesh_vertex_list.extend(curve_start_points)
		# mesh_vertex_list.extend(curve_mid_points)
		# mesh_vertex_list.extend(curve_end_points)
		
		# self.MakeReferencePoint("Edge_A_Start_" + surface.guid, surface.edge_a.GetStartPoint(), empty_type="SPHERE")
		# self.MakeReferencePoint("Edge_A_Mid_" + surface.guid, surface.edge_a.GetMidPoint(), empty_type="SPHERE")
		# self.MakeReferencePoint("Edge_A_End_" + surface.guid, surface.edge_a.GetEndPoint(), empty_type="SPHERE")
		# self.MakeReferencePoint("Edge_B_Start_" + surface.guid, surface.edge_b.GetStartPoint(), empty_type="SPHERE")
		# self.MakeReferencePoint("Edge_B_End_" + surface.guid, surface.edge_b.GetEndPoint(), empty_type="SPHERE")
		# self.MakeReferencePoint("Edge_C_Start_" + surface.guid, surface.edge_c.GetStartPoint(), empty_type="SPHERE")
		# self.MakeReferencePoint("Edge_C_Mid_" + surface.guid, surface.edge_c.GetMidPoint(), empty_type="SPHERE")
		# self.MakeReferencePoint("Edge_C_End_" + surface.guid, surface.edge_c.GetEndPoint(), empty_type="SPHERE")
		# self.MakeReferencePoint("CenterPoint_" + surface.guid, surface.edge_b.GetMidPoint(), empty_type="SPHERE")
		# for edge in surface.RawEdgeList:
		# 	self.MakeReferencePoint("StartPoint_" + edge.guid, edge.GetStartPoint())
		# 	self.MakeReferencePoint("MidPoint_" + edge.guid, edge.GetMidPoint())
		# 	self.MakeReferencePoint("EndPoint_" + edge.guid, edge.GetEndPoint())

		
		# Calculate the points based off the data from the curves generated previously
		# The function will plot a curve with the start taken from curve_start_points,
		# control point taken from curve_mid_points and the end point taken from curve_end_points.
		# Each one will generated step by step
		for i in range(0, len(curve_start_points)):
			midpoint = self.GetMidpoint(curve_start_points[i], curve_end_points[i])
			newpoint = [
				midpoint[0] + (curve_mid_points[i][0] - midpoint[0]) * 2,
				midpoint[1] + (curve_mid_points[i][1] - midpoint[1]) * 2,
				midpoint[2] + (curve_mid_points[i][2] - midpoint[2]) * 2
			]
			mesh_vertex_list.extend(self.CalculateCurvePoints([
				curve_start_points[i],
				newpoint,
				curve_end_points[i]
			], self.setting_surface_resolution))

		# Generate list of 4x4 points so that they can be used as a way to 
		# map the faces of the mesh
		face_list = self.GenerateFaceList(len(curve_mid_points))

		# Generate the actual mesh based off the data...
		mesh.from_pydata(mesh_vertex_list, [], face_list)

		# Generate UV map...
		mesh.uv_layers.new(name="base")
		bm = bmesh.new()
		bm.from_mesh(mesh)
		bm.faces.ensure_lookup_table()
		uv_layer = bm.loops.layers.uv[0]
		x_l = len(curve_mid_points) - 1

		count = 0
		current_x = 0
		total_len = int(math.pow(x_l, 2))
		scale_down = 1/(len(curve_mid_points) - 1)

		for current_face in reversed(range(total_len)):
			bm.faces[current_face].loops[2][uv_layer].uv = (
				(0 + count) * scale_down,
				(0 + current_x) * scale_down
			)
			bm.faces[current_face].loops[1][uv_layer].uv = (
				(1 + count) * scale_down,
				(0 + current_x) * scale_down
			)
			bm.faces[current_face].loops[0][uv_layer].uv = (
				(1 + count) * scale_down,
				(1 + current_x) * scale_down
			)
			bm.faces[current_face].loops[3][uv_layer].uv = (
				(0 + count) * scale_down,
				(1 + current_x) * scale_down
			)
			count += 1
			if count >= x_l:
				count = 0
				current_x += 1
		bm.to_mesh(mesh)



		# Create the Solidify and Edge Split modifiers. and smooth out the surface
		mesh_object.modifiers.new("Solidify", 'SOLIDIFY')
		mesh_object.modifiers.new("Edge Split", 'EDGE_SPLIT')
		mesh_object.modifiers["Solidify"].thickness = surface.thickness * self.setting_surface_thickness_multiplier
		mesh_object.modifiers["Solidify"].offset = 0.0

		if self.setting_GenerateMaterial:
			mat = self.GenerateSurfaceBlockMaterial(surface)
			mesh_object.active_material = mat
		
		for f in mesh.polygons:
			f.use_smooth = True
		return mesh_object



	def GenerateCurve(self, edge:BuildSurfaceEdge) -> list:
		'''
		Generates a curve. Not to be confused with GenerateCurvePoint. This function
		will calculate the position of the center control point and generate a curve.
		Parameters:
			edge : BuildSurfaceEdge : The edge
		Return : list : list of points
		Exceptions : None
		'''
		midpoint = self.GetMidpoint(edge.GetStartPoint(), edge.GetEndPoint())
		newpoint = [
			midpoint[0] + (edge.GetMidPoint()[0] - midpoint[0]) * 2,
			midpoint[1] + (edge.GetMidPoint()[1] - midpoint[1]) * 2,
			midpoint[2] + (edge.GetMidPoint()[2] - midpoint[2]) * 2
		]
		return self.CalculateCurvePoints([
			edge.GetStartPoint(),
			newpoint,
			edge.GetEndPoint()
		], self.setting_surface_resolution)

			
	def GenerateFaceList(self, chunk_size) -> list:
		'''
		Generates a list of points that can be used as faces.
		Parameters:
			chunk_size : int : size of the mesh in one axis
		Returns : list : list of points
		Exceptions : None
		'''
		point_array = range(0, chunk_size * chunk_size)
		chunk_arr = [point_array[i:i + chunk_size] for i in range(0, len(point_array), chunk_size)]
		return_list = []
		for x in range(0, chunk_size - 1):
			for y in range(0, chunk_size -1):
				p1 = chunk_arr[x][y]
				p2 = chunk_arr[x + 1][y]
				p3 = chunk_arr[x + 1][y + 1]
				p4 = chunk_arr[x][y + 1]
				return_list.append([p1, p2, p3, p4])
		return return_list

	def CalculateCurvePoints(self, points, resolution=0.1) -> list:
		'''
		Calculates points of a curves and returns them.
		Parameters:
			points : list : list of co-ordinates used as the controls points
			resolution : float : number of steps in the 3D curve
		Returns : list : list of co-ordinates
		Exceptions : None
		'''
		t_points = np.arange(0, 1, resolution)
		curve_set = Bezier.Curve(t_points, np.array(points))
		return_l = curve_set.tolist()
		return_l.append(points[len(points) - 1])
		return return_l

		
	def MakeReferencePoint(self, name:str, location:list, size=0.25, empty_type="PLAIN_AXES") -> None:
		'''
		This function creates an empty. The empty can be useful for marking a point in 3D space.
		Parameters:
			name : string : name of empty
			location : list : co-ordinates for point
			size : float : size of empty
			empty_type : string : Type of empty. Check Blender API docs for a list of types
		Returns : None
		Exceptions : None
		'''
		empty = bpy.data.objects.new(name, None)
		empty.empty_display_size = size
		empty.empty_display_type = empty_type
		empty.location = location
		bpy.data.collections[bpy.context.view_layer.active_layer_collection.name].objects.link(empty)

	def GetMidpoint(self, start:list, end:list) -> list:
		'''
		This function gets the mid point between 2 points in 3D space. Will return a point in the form of
		a list of length 3.
		Parameters:
			start : list : list of co-ordiantes for the start point
			end : list : list of co-ordinates for the end point
		Returns : None
		Exceptions : None
		'''
		locx = (end[0] + start[0]) / 2
		locy = (end[1] + start[1]) / 2
		locz = (end[2] + start[2]) / 2
		return [locx, locy, locz]

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
		
		# Import the connector, start and end objects
		connector = self.ImportCustomModel(component.line_type_middle)
		start = self.ImportCustomModel(component.line_type_end)
		end = self.ImportCustomModel(component.line_type_start)

		# Set the material for models
		if self.setting_GenerateMaterial:
			material = self.GenerateMaterial(block, component, component.skin_name) #if not self.setting_use_vanilla_skin else self.GenerateMaterial(block, component, "TemplateB")
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

		if self.setting_join_line_components:
			for obj in list(bpy.context.selected_objects): obj.select_set(False)
			bpy.context.view_layer.objects.active = start

			start.select_set(True)
			if not distance < self.setting_brace_threshhold:
				connector.select_set(True)
				end.select_set(True)
				bpy.ops.object.join()
			current_obj = bpy.context.selected_objects[0]

			if self.setting_clean_up_action == 'DELETE_EMPTIES':
				self.UnparentKeepTransform(current_obj)
				bpy.data.objects.remove(parent)
			elif self.setting_clean_up_action == 'HIDE_EMPTIES':
				parent.hide_set(True)
			return current_obj
		return parent
	
	def UnparentKeepTransform(self, ob):
		# So turns out blender doesn't support shearing... so whatever its called...
		# That's why this code was copied from https://blender.stackexchange.com/questions/154848/clear-parent-and-keep-transformation
		# I have no idea how it works. But it works. not my proudest moment
		mat = ob.matrix_world
		for obj in list(bpy.context.selected_objects): obj.select_set(False)
		bpy.context.view_layer.objects.active = ob
		ob.select_set(True)
		loc, rot, sca = mat.decompose()
		mat_loc = Matrix.Translation(loc)
		mat_rot = rot.to_matrix().to_4x4()
		mat_sca = Matrix.Identity(4)
		mat_sca[0][0], mat_sca[1][1], mat_sca[2][2] = sca
		mat_out = mat_loc @ mat_rot @ mat_sca
		mat_h = mat_out.inverted() @ mat

		# Unparent the object.
		bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

		# Move the vertices to their original position,
		# which the mat_out can't represent.
		for v in ob.data.vertices:
			v.co = mat_h @ v.co

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

	# def RotateGlobal(self, obj, radian, axis) -> None:
	# 	from math import radians
	# 	from mathutils import Matrix
	# 	obj.rotation_euler = (obj.rotation_euler.to_matrix() @ Matrix.Rotation(radian, 3, axis)).to_euler()

	def ClearExtraMaterialSlots(self, obj):
		obj.active_material_index = 0
		for _ in range(len(obj.material_slots)):
			with bpy.context.temp_override(object=obj):
				bpy.ops.object.material_slot_remove()

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
		print(">>>>>>>>")
		print(current_obj)
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
		if (block.code_name == "Unknown"):
			current_obj.name = block.block_id + "_" + current_obj.name
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


	def FetchSkinFile(self, block_name:str, skin_id:str, skin_name='Template', only_texture=False, only_model=False) -> None:
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
			os.path.join(self.backup_store, block_name),
			os.path.join(self.custom_block_dir, block_name)
		]
		for cdir in model_dirs:
			target_type = "skin" if only_texture and (not only_model) else "model" 
			print("Searching in {} for skin file (type : {})...".format(cdir, target_type))
			result_t = self.SearchInDirectory(cdir, '.png')
			result_o = self.SearchInDirectory(cdir, '.obj')
			if only_texture and result_t: return result_t
			if only_model and result_o: return result_o
			# if result_t and result_o: return [result_o, result_t]
		print("ERROR: Cannot find file...")
		return ""

	def SearchInDirectory(self, directory:str, extension:str) -> bool:
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

	# def CheckIfMaterialExists(block, skin_name):
	# 	mat_name = block.base_source + skin_name + "Material"
	# 	return str(mat_name) in bpy.data.materials.keys()

	def GenerateSurfaceBlockMaterial(self, surface:BuildSurface):
		mat_name = "SurfaceBlock-{}".format(surface.skin_name)

		if self.setting_grouping_mode.__eq__('SAME_CONFIG'): node_group_name = 'Surface-GlobalConfigNodeSetup'
		elif self.setting_grouping_mode.__eq__('FOR_EACH_SKIN'): node_group_name = 'Surface-{}SkinNodeSetup'.format(surface.skin_name)
		else: node_group_name = 'SurfaceBlockNodeGoup'
		node_group = None
		try: node_group = bpy.data.node_groups[node_group_name]
		except KeyError: node_group = NodeGroups().SurfaceBlockPrincipledBDSF(name=node_group_name, custom_block_dir=self.custom_block_dir)
		texture_path = self.FetchSkinFile("BuildSurface", surface.skin_id, surface.skin_name, only_texture=True) if not self.setting_use_vanilla_skin else self.FetchSkinFile("BuildSurface", "0", "Template", only_texture=True)
		final_m = MaterialList.NodeGroupSurfaceMaterial(texture_path, mat_name, node_group, surface)
		self.imported_materials.append(final_m)
		return final_m
		


	def GenerateMaterial(self, block:Block, component:Component, skin_name:str) -> 'Material':
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

		mat_name = component.base_source + skin_name + "Material"
		search_name = mat_name + "NodeGrouped" if self.setting_use_node_groups else ""
		if str(search_name) in bpy.data.materials.keys(): return bpy.data.materials[search_name]
		texture_path = self.FetchSkinFile(block.code_name, component.skin_id, component.skin_name, only_texture=True) if not self.setting_use_vanilla_skin else self.FetchSkinFile(block.code_name, "0", "Template", only_texture=True)

		if self.setting_use_node_groups:
			node_group_name = ''
			if self.setting_grouping_mode.__eq__('SAME_CONFIG'): node_group_name = 'GlobalConfigNodeSetup'
			elif self.setting_grouping_mode.__eq__('FOR_EACH_SKIN'): node_group_name = '{}SkinNodeSetup'.format(skin_name)
			elif self.setting_grouping_mode.__eq__('FOR_EACH_BLOCK'): node_group_name = '{}BlockNodeSetup'.format(component.base_source)

			node_group = None
			
			try: node_group = bpy.data.node_groups[node_group_name] 
			except KeyError: node_group = NodeGroups().SimplePrincipledBDSF(name=node_group_name)
			final_m = MaterialList.NodeGroupMaterial(texture_path, mat_name, node_group)
			self.imported_materials.append(final_m)
			return final_m
		else:
			final_m = MaterialList.DefaultMaterial(component, texture_path, mat_name)
			self.imported_materials.append(final_m)
			return final_m