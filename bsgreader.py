import json
import xml.etree.ElementTree as ET
import os
import bpy

# from .Component import Component
# from .Block import Block

from Component import Component
from Block import Block

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
		# atlas_dir = os.path.join(bpy.utils.script_path_user(), "addons", "BesiegeCreationImportAddon", 'object_transform_data_converted_v2.json')
		atlas_dir = 'object_transform_data_converted_v2.json'
		with open(atlas_dir) as json_file:
			self.atlas = json.load(json_file)

		self.cfile = ET.parse(src)

	def ReadBlockData(self) -> List[Block]:
		all_blocks = self.cfile.findall(".//Blocks/*")
		returnList = []

		total_blocks = 0
		total_components = 0
		skipped_blocks = 0

		for block in all_blocks:
			
			block_id = block.get('id')
			if not block_id in self.atlas.keys():
				skipped_blocks += 1
				print("Warning: Cannot find block ID {} in transform data atlas...".format(block_id))
				continue

			total_blocks += 1

			trans_p_x = float(block.find("Transform/Position").get('x'))
			trans_p_y = float(block.find("Transform/Position").get('y'))
			trans_p_z = float(block.find("Transform/Position").get('z'))

			trans_r_x = float(block.find("Transform/Rotation").get('x'))
			trans_r_y = float(block.find("Transform/Rotation").get('y'))
			trans_r_z = float(block.find("Transform/Rotation").get('z'))
			trans_r_w = float(block.find("Transform/Rotation").get('w'))

			trans_s_x = float(block.find("Transform/Scale").get('x'))
			trans_s_y = float(block.find("Transform/Scale").get('y'))
			trans_s_z = float(block.find("Transform/Scale").get('z'))

			current_block = Block(
				[trans_p_x, trans_p_y, trans_p_z],
				[trans_r_x, trans_r_y, trans_r_z, trans_r_w],
				[trans_s_x, trans_s_y, trans_s_z]
				)

			if (block_id in ['26', '55']):
				for key in block.find("Data").getchildren():
					if key.get('key').__eq__('flipped'):
						current_block.flipped = key.text

			if (block_id in ['7']):
				for key in block.find("Data").getchildren():
					if key.get('key').__eq__('start-position'): sp = [key.find('X').text, key.find('Y').text, key.find('Z').text]
					if key.get('key').__eq__('end-position'): ep = [key.find('X').text, key.find('Y').text, key.find('Z').text]
					if key.get('key').__eq__('start-rotation'): sr = [key.find('X').text, key.find('Y').text, key.find('Z').text]
					if key.get('key').__eq__('end-rotation'): er = [key.find('X').text, key.find('Y').text, key.find('Z').text]

				current_block.SetLineTypeGeometry(sp, ep, sr, er)
							
			current_block.guid = block.get('guid')
			current_block.block_id = block_id
			current_block.code_name = self.atlas[block_id]['code_name']

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
		print("{} blocks imported...\n{} components imported...\n{} blocks skipped".format(total_blocks, total_components, skipped_blocks))
		return returnList

		
