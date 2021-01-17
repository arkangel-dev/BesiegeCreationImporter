import json
import xml.etree.ElementTree as ET
import os
import bpy



dev_mode = True

if dev_mode:
	from Component import Component
	from Block import Block, Surface, Surface_Edge
else:
	from .Component import Component
	from .Block import Block, Surface, Surface_Edge

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
		try:
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
					for key in block.find("Data").getchildren():
						if key.get('key').__eq__('flipped'):
							current_block.flipped = key.text

				# These are for the "Line type blocks". These blocks have two sets of co-ordinates. The start and
				# end position as well as rotation.
				if (block_id in ['7','9','45']):
					sp, ep, sr, er = ('0','0','0'), ('0','0','0'), ('0','0','0'), ('0','0','0')
					for key in block.find("Data").getchildren():
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

			edges = []
			for edge in surface_data_edges:
				c_edge = Surface_Edge()
				start_guid = edge.find("Data/String[@key='start']").text
				end_guid = edge.find("Data/String[@key='end']").text
				s_f = False
				e_f = False


				for point in surface_data_nodes:
					if point.get('guid') == start_guid:
						s_f = True
						c_edge.s_x = float(point.find("Transform/Position").get('x'))
						c_edge.s_y = float(point.find("Transform/Position").get('z'))
						c_edge.s_z = float(point.find("Transform/Position").get('y'))
						# surface_data_nodes.remove(point)
					
					if point.get('guid') == end_guid:
						e_f = True
						c_edge.e_x = float(point.find('Transform/Position').get('x'))
						c_edge.e_y = float(point.find('Transform/Position').get('z'))
						c_edge.e_z = float(point.find('Transform/Position').get('y'))
						# surface_data_nodes.remove(point)
					if s_f and e_f: break

				c_edge.x = float(edge.find('Transform/Position').get('x'))
				c_edge.y = float(edge.find('Transform/Position').get('z'))
				c_edge.z = float(edge.find('Transform/Position').get('y'))
				c_edge.guid = edge.get('guid')
				edges.append(c_edge)
			
			for surface in surface_data_surfaces:
				c_surface = None
				c_surface = Surface(surface.get('guid'))
				surface_edge_guids = surface.find("Data/String[@key='edges']").text.split("|")
				for edge in edges:
					if edge.guid in surface_edge_guids:
						c_surface.edges.append(edge)
						# edges.remove(edge)
				try:
					skin_name = surface.find("Settings/Skin").get("name")
					skin_id = surface.find("Settings/Skin").get("id")
				except:
					skin_name = "Template"
					skin_id = "Template"
				c_surface.skin = skin_name
				c_surface.skin_id = skin_id
				returnList.append(c_surface)
			
			print("{} blocks imported...\n{} components imported...\n{} blocks skipped".format(total_blocks, total_components, skipped_blocks))
			return {
				'RETURN_LIST' : returnList,
				'TOTAL_BLOCKS' : total_blocks,
				'TOTAL_COMPONENTS' : total_components,
				'SKIPPED_BLOCKS' : skipped_blocks,
				'FAILED' : False
			}
		except:
			print("Warning: Cannot read data from BSG file...")
			return {
				'RETURN_LIST' : 0,
				'TOTAL_BLOCKS' : 0,
				'TOTAL_COMPONENTS' : 0,
				'SKIPPED_BLOCKS' : 0,
				'FAILED' : True
			}
		
