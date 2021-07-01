import json
import xml.etree.ElementTree as ET
import os
import bpy
import copy


dev_mode = False

if dev_mode:
	from Component import Component
	from Block import Block, BuildSurface, BuildSurfaceEdge
else:
	from .Component import Component
	from .Block import Block, BuildSurface, BuildSurfaceEdge

from typing import List
from copy import deepcopy

class Reader():
	"""
	This is the reader class. It allows the BSG file to be read.
	"""
	cfile = ""
	atlas = {}

	def __init__(self, src:str):
		self.cfile = src
		atlas_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'object_transform_data_converted_v2.json')
		if dev_mode: atlas_dir = 'object_transform_data_converted_v2.json'
		with open(atlas_dir) as json_file:
			self.atlas = json.load(json_file)

	def ReadBlockData(self) -> List[Block]:
		# try:
		# First we open the BSG file and parse it.
		# Then we can use a xpath statement to find all the block tags
		self.cfile = ET.parse(self.cfile)
		all_blocks = self.cfile.findall(".//Blocks/*")
		returnList = []

		total_blocks = 0
		total_components = 0
		skipped_blocks = 0

		# We will also need to find the global rotation of the machine
		# This will not effect the normal blocks but will definetly affect
		# the rotation of the brace cubes and might effect the surface blocks...
		global_data = self.cfile.findall("./Global/*")
		global_rot_x = float(global_data[1].get('x'))
		global_rot_y = float(global_data[1].get('y'))
		global_rot_z = float(global_data[1].get('z'))
		global_rot_w = float(global_data[1].get('w'))

		surface_data_nodes = []
		surface_data_edges = []
		surface_data_surfaces = []

		# We are going to loop over all the blocks in the BSG file...
		# Here we will organize the blocks, collect special attributes
		# for certain blocks. Because we have to collect special attributes
		# the method looks like a complete mess
		for block in all_blocks:				
			block_id = block.get('id')

			# first we will check if its a surface data block...
			# and if it is, save them into an array so we can process them later...
			# We are checking it here because the surface block has only points and
			# doesn't need to be normalized...
			if block_id in ['71','72','73']:
				if block_id == '71':
					surface_data_nodes.append(block)
					continue
				if block_id == '72':
					surface_data_edges.append(block)
					continue
				if block_id == '73':
					surface_data_surfaces.append(block)
					continue

			# Check if the block is in the transform atlast...
			# if its not, print and increment the skipped block count
			# we can display it on the addon page...
			if not block_id in self.atlas.keys():
				skipped_blocks += 1
				print("Warning: Cannot find block ID {} in transform data atlas...".format(block_id))
				continue

			total_blocks += 1
			
			# Get the position of the block...
			trans_p_x = float(block.find("Transform/Position").get('x'))
			trans_p_y = float(block.find("Transform/Position").get('y'))
			trans_p_z = float(block.find("Transform/Position").get('z'))

			# Get the rotation of the block...
			trans_r_x = float(block.find("Transform/Rotation").get('x'))
			trans_r_y = float(block.find("Transform/Rotation").get('y'))
			trans_r_z = float(block.find("Transform/Rotation").get('z'))
			trans_r_w = float(block.find("Transform/Rotation").get('w'))

			# Get the scale of the block...
			trans_s_x = float(block.find("Transform/Scale").get('x'))
			trans_s_y = float(block.find("Transform/Scale").get('y'))
			trans_s_z = float(block.find("Transform/Scale").get('z'))

			# Create a new instance of the Block object and pass its
			# its information in...
			current_block = Block(
				[trans_p_x, trans_p_y, trans_p_z],
				[trans_r_x, trans_r_y, trans_r_z, trans_r_w],
				[trans_s_x, trans_s_y, trans_s_z]
				)

			# Set the GUID and the other various data...
			current_block.guid = block.get('guid')
			current_block.block_id = block_id
			current_block.code_name = self.atlas[block_id]['code_name']

			# Set the global rotation of the block...
			current_block.SetGlobalMachineRotation(global_rot_x, global_rot_y, global_rot_z, global_rot_w)

			# These are for propeller blocks...
			# Various blocks have the flipped property, these include, wheels,
			# steering blocks, steering hinges, wheels etc... But out of all these
			# blocks only the propeller blocks have their transform data altered...
			if (block_id in ['26', '55']):
				for key in list(block.find("Data")):
					if key.get('key').__eq__('flipped'):
						current_block.flipped = key.text

			# These are for the "Line type blocks". These blocks have two sets of co-ordinates. The start and
			# end position as well as rotation.
			if (block_id in ['7','9','45']):
				sp, ep, sr, er = ('0','0','0'), ('0','0','0'), ('0','0','0'), ('0','0','0')
				for key in list(block.find("Data")):
					if key.get('key').__eq__('start-position'): sp = [key.find('X').text, key.find('Y').text, key.find('Z').text]
					if key.get('key').__eq__('end-position'): ep = [key.find('X').text, key.find('Y').text, key.find('Z').text]
					if key.get('key').__eq__('start-rotation'): sr = [key.find('X').text, key.find('Y').text, key.find('Z').text]
					if key.get('key').__eq__('end-rotation'): er = [key.find('X').text, key.find('Y').text, key.find('Z').text]
				current_block.SetLineTypeGeometry(sp, ep, sr, er)
							
			# Each block will have multiple components. The main mesh itself and other little details that do not come
			# with the mesh. For example, stuff like the needle and switches. This segment will allow us to import that stuff
			# as well
			for component in self.atlas[block_id]['components']:
				print("Adding component ID {}...".format(component['base_source']))
				total_components += 1
				o_p_x, o_p_y, o_p_z = component['offset']['position'].values()
				o_r_x, o_r_y, o_r_z = component['offset']['rotation'].values()

				o_s_x = component['offset']['scale']['x']
				o_s_y = component['offset']['scale']['z']
				o_s_z = component['offset']['scale']['y']

				current_comp_inst = Component(
					[o_p_x, o_p_y, o_p_z],
					[o_r_x, o_r_y, o_r_z],
					[o_s_x, o_s_y, o_s_z]
				)
				try:
					current_comp_inst.skin_id = block.find('Settings/Skin').get('id')
					current_comp_inst.skin_name = block.find('Settings/Skin').get('name')
				except:			
					current_comp_inst.skin_id = 'Template'
					current_comp_inst.skin_name = 'Template'
				if (current_comp_inst.skin_name == 'default'):
					current_comp_inst.skin_id = 'Template'
					current_comp_inst.skin_name = 'Template'
				current_comp_inst.base_source = component['base_source']
				current_comp_inst.group = component['group']
				current_comp_inst.line_type_block = component['line_type_blocks']
				if current_comp_inst.line_type_block:
					current_comp_inst.line_type_start = component['line_type_components']['start']
					current_comp_inst.line_type_end = component['line_type_components']['end']
					current_comp_inst.line_type_middle = component['line_type_components']['middle']
				current_block.components.append(deepcopy(current_comp_inst))
			returnList.append(current_block)
		
		# now that the normal blocks have been processed and all the surface data blocks have been loaded,
		# we can easily process them as well...
		# First define a storage for the edges and surfaces. We'll process the edges first


		for surface in surface_data_surfaces:
			try:
				surface_guid = surface.get('guid')

				# Split the string to get a list of the edge GUIDs
				surface_edge_guids = surface.find("Data/String[@key='edges']").text.split("|")

				c_surface = BuildSurface(surface_guid)
				if len(surface_edge_guids) == 3:
					# If we dont have enough edges, we can take a GUID
					# from the list and add it to the end of the list
					surface_edge_guids.append(surface_edge_guids[0])
					c_surface.IsQuad = False

				raw_edges = []
				# Ok so in the last version what went wrong was that the we needed the edges in the same order
				# that they were defined in the surface tag. But I simply used a for loop iterating through the
				# edge tags and checking if their guids were in the list of GUIDs from the surface block tag...
				# Should've seen that coming because ProNou did warn me... I really need to start reading the 
				# instructions before starting to code...
				for edge_guid in surface_edge_guids:
					for edge in surface_data_edges:
						guid = edge.get('guid')
						if guid != edge_guid: continue

						c_edge = BuildSurfaceEdge(guid)		
						start_guid = edge.find("Data/String[@key='start']").text
						end_guid = edge.find("Data/String[@key='end']").text

						start_point_found = False
						end_point_found = False
						
						# Find the pointss that define the start and end point of the edge.
						for point in surface_data_nodes:
							if start_point_found and end_point_found: break
							if point.get('guid') == start_guid:
								start_point_found = True
								c_edge.SetStartPoint([
									float(point.find("Transform/Position").get('x')),
									float(point.find("Transform/Position").get('z')),
									float(point.find("Transform/Position").get('y'))
								])
							if point.get('guid') == end_guid:
								end_point_found = True
								c_edge.SetEndPoint([
									float(point.find("Transform/Position").get('x')),
									float(point.find("Transform/Position").get('z')),
									float(point.find("Transform/Position").get('y'))
								])

						# Then set the mid point for the edge...
						c_edge.SetMidPoint([
							float(edge.find('Transform/Position').get('x')),
							float(edge.find('Transform/Position').get('z')),
							float(edge.find('Transform/Position').get('y'))
						])

						# Add it to the list of raw edges
						raw_edges.append(c_edge)

				# Now that we have all the raw data edge data,
				# We can use that data to create the U edges and save it...
				# First we'll calculate the center edge. Because that's more complicated
				# than the other two...
				# First we'll need to get the center point...

				center_edge_mid_point = [0,0,0]

				# Calculate the total location of the points and edges...
				# Initilze the variables for the location
				point_total_location_x = 0
				point_total_location_y = 0
				point_total_location_z = 0
				
				# Initilize the variable for the edges
				edge_total_location_x = 0
				edge_total_location_y = 0
				edge_total_location_z = 0



				# This code segment makes sure that no curtain effects are produced.
				# curtain effect is when the addon fails to align the points in the 3 
				# edges needed to generate the surface mesh
				# The curtain effect works differently for Quad surfaces from surfaces with
				# 3 sides
				if not c_surface.IsQuad:
					if raw_edges[0].GetStartPoint() != raw_edges[3].GetEndPoint() and raw_edges[2].GetEndPoint() != raw_edges[3].GetStartPoint():
						raw_edges[3].InvertPointLocations()

					if raw_edges[0].GetEndPoint() != raw_edges[1].GetStartPoint() and raw_edges[1].GetEndPoint() != raw_edges[2].GetStartPoint():
						raw_edges[1].InvertPointLocations()

					raw_edges[3].InvertPointLocations()
					if raw_edges[1].GetStartPoint() != raw_edges[3].GetStartPoint():
						if raw_edges[1].GetEndPoint() != raw_edges[0].GetEndPoint():
							raw_edges[3].InvertPointLocations()
						else:
							raw_edges[1].InvertPointLocations()
					
				else:
					if raw_edges[1].GetEndPoint() != raw_edges[0].GetStartPoint(): raw_edges[1].InvertPointLocations()
					if raw_edges[2].GetEndPoint() != raw_edges[1].GetStartPoint(): raw_edges[2].InvertPointLocations()
					if raw_edges[3].GetEndPoint() != raw_edges[2].GetStartPoint(): raw_edges[3].InvertPointLocations()
					if raw_edges[0].GetStartPoint() != raw_edges[3].GetEndPoint() and raw_edges[2].GetEndPoint() != raw_edges[3].GetStartPoint(): raw_edges[3].InvertPointLocations()
					if raw_edges[0].GetEndPoint() != raw_edges[1].GetStartPoint() and raw_edges[1].GetEndPoint() != raw_edges[2].GetStartPoint(): raw_edges[1].InvertPointLocations()
					raw_edges[3].InvertPointLocations()

				if not c_surface.IsQuad:
					raw_edges[3].IsFalseEdge = True

				# Add up all the surfaces edge location as well as
				# the point locations. If the surface is not a Quad,
				# then skip the edge position and the point positions
				for edge in raw_edges:
					if not edge.IsFalseEdge:
						point_total_location_x += edge.GetEndPoint()[0]
						point_total_location_y += edge.GetEndPoint()[1]
						point_total_location_z += edge.GetEndPoint()[2]

						point_total_location_x += edge.GetStartPoint()[0]
						point_total_location_y += edge.GetStartPoint()[1]
						point_total_location_z += edge.GetStartPoint()[2]

						edge_total_location_x += edge.GetMidPoint()[0]
						edge_total_location_y += edge.GetMidPoint()[1]
						edge_total_location_z += edge.GetMidPoint()[2]


				# Then do some mathematical magic...
				# Note that this formula is different for Quads.
				# because the number of points that needs to split apart
				# are differnet 
				if c_surface.IsQuad:
					center_edge_mid_point[0] = 2 * (edge_total_location_x / 4) - (point_total_location_x / 8)
					center_edge_mid_point[1] = 2 * (edge_total_location_y / 4) - (point_total_location_y / 8)
					center_edge_mid_point[2] = 2 * (edge_total_location_z / 4) - (point_total_location_z / 8)
				else:
					center_edge_mid_point[0] = 2 * (edge_total_location_x / 3) - (point_total_location_x / 6)
					center_edge_mid_point[1] = 2 * (edge_total_location_y / 3) - (point_total_location_y / 6)
					center_edge_mid_point[2] = 2 * (edge_total_location_z / 3) - (point_total_location_z / 6)


				# And now we can finally create a new BuildSurfaceEdge object and feed it the points
				center_edge = BuildSurfaceEdge("NULL")
				center_edge.SetStartPoint(raw_edges[0].GetMidPoint())
				center_edge.SetEndPoint(raw_edges[2].GetMidPoint())
				center_edge.SetMidPoint(center_edge_mid_point)


				# if the surface is not a quad, then check if the edge_a and edge_b's start and end points
				# align. if they do not align, use the Start point of the center edge. Otherwise use the end
				# point. This will result with all the points converging to a single point...
				if not c_surface.IsQuad:
					# if raw_edges[0].GetStartPoint() != center_edge.GetEndPoint(): center_edge.InvertPointLocations()
					if raw_edges[1].GetStartPoint() != raw_edges[0].GetEndPoint():
						center_edge.SetStartPoint(raw_edges[0].GetStartPoint())
					else:
						center_edge.SetStartPoint(raw_edges[0].GetEndPoint())
					

				# As for the other two edges we already have the data for those two...
				# So we can feed it to the surface object...
				c_surface.edge_a = raw_edges[1]
				c_surface.edge_b = center_edge
				c_surface.edge_c = raw_edges[3]
				c_surface.RawEdgeList = raw_edges

				# define the color data for the surface blocks...
				c_surface.thickness = float(surface.find("Data/Single[@key='bmt-thickness']").text)
				c_surface.saturation = float(surface.find("Data/Single[@key='bmt-sat']").text)
				c_surface.luminosity = float(surface.find("Data/Single[@key='bmt-lum']").text)
				c_surface.col_rgb = [
					float(surface.find("Data/Color/R").text),
					float(surface.find("Data/Color/G").text),
					float(surface.find("Data/Color/B").text)
				]
				c_surface.UsePaint = surface.find("Data/Boolean[@key='bmt-painted']").text == "True"
				c_surface.MaterialType = int(surface.find("Data/Integer[@key='bmt-surfMat']").text)

				# define the skin data
				try:
					c_surface.skin_id = surface.find('Settings/Skin').get('id')
					c_surface.skin_name = surface.find('Settings/Skin').get('name')
				except:			
					c_surface.skin_id = 'Template'
					c_surface.skin_name = 'Template'
				if (c_surface.skin_name == 'default'):
					c_surface.skin_id = 'Template'
					c_surface.skin_name = 'Template'

				# Add it to the list and increment the number of blocks imported
				returnList.append(c_surface)
				total_blocks += 1


			# 	try:
			# 		skin_name = surface.find("Settings/Skin").get("name")
			# 		skin_id = surface.find("Settings/Skin").get("id")
			# 	except:
			# 		skin_name = "Template"
			# 		skin_id = "Template"
			# 	c_surface.skin = skin_name
			# 	c_surface.skin_id = skin_id
			# 	returnList.append(c_surface)
			except:
				skipped_blocks += 1
		
		print("{} blocks imported...\n{} components imported...\n{} blocks skipped".format(total_blocks, total_components, skipped_blocks))
		return {
			'RETURN_LIST' : returnList,
			'TOTAL_BLOCKS' : total_blocks,
			'TOTAL_COMPONENTS' : total_components,
			'SKIPPED_BLOCKS' : skipped_blocks,
			'FAILED' : False
		}
		# except Exception:
		# 	print("Warning: Cannot read data from BSG file...")
		# 	return {
		# 		'RETURN_LIST' : 0,
		# 		'TOTAL_BLOCKS' : 0,
		# 		'TOTAL_COMPONENTS' : 0,
		# 		'SKIPPED_BLOCKS' : 0,
		# 		'FAILED' : True
		# 	}
		
