bl_info = {
	'name': 'Import Besiege Machines',
	'author': 'Sam Ramirez',
	'version': (1, 6, 0),
	'blender': (2, 90, 1),
	'location': 'View3D > Toolbar > Besiege',
	'description': 'Imports Besiege Creation Files (.bsg) files',
	'warning': 'This addon is still being worked on',
	'wiki_url': '',
	'category': 'Import-Export',
}

dev_mode = False

if dev_mode:
	import blenapi
else:
	from . import blenapi
from bpy.app.handlers import persistent
import bpy
import xml.etree.ElementTree as ET
import os
import traceback
import configparser
import time
from pathlib import Path



class GlobalData():
	importer = None
	result_data = {}

	#This is the Main Panel (Parent of Panel A and B)
class MainPanel(bpy.types.Panel):
	bl_label = 'Besiege Import'
	bl_idname = 'PT_MainPanel'
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Besiege'

   
	def draw(self, context):
		layout = self.layout
		layout.scale_x = 2
		layout.row().prop(context.scene, 'bsgimp_bsg_path', icon='FILE')
		if bool(GlobalData.result_data):
			if not GlobalData.result_data['FAILED']:
				layout.row().label(text="Block Count : {}".format(GlobalData.result_data['TOTAL_BLOCKS']))
				if GlobalData.result_data['SKIPPED_BLOCKS'] > 0:
					layout.row().label(text="Skipped Count : {}".format(GlobalData.result_data['SKIPPED_BLOCKS']), icon='ERROR')
			else:
				layout.row().label(text="Failed to read file", icon='ERROR')

			importer_row = layout.row()
			importer_row.operator('mesh.importoperator', text = 'Import')
			importer_row.enabled = not GlobalData.result_data['FAILED']

class GeneralSettings(bpy.types.Panel):
	bl_label = 'General Settings'
	bl_idname = 'PT_GeneralSettingsPanel'
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_parent_id = 'PT_MainPanel'
	bl_options = {'DEFAULT_CLOSED'}

	def draw(self, context):
		layout = self.layout
		layout.row().prop(context.scene, 'bsgimp_create_parent')
		layout.row().operator('obj.selectimported', text = 'Select Imported')

class SettingsPanel(bpy.types.Panel):
	bl_label = 'Addon Settings'
	bl_idname = 'PT_SettingsPanel'
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Besiege'
	bl_parent_id = 'PT_MainPanel'
	bl_options = {'DEFAULT_CLOSED'}

	def draw(self, context):
		layout = self.layout
		layout.row().prop(context.scene, 'bsgimp_template_path')
		layout.row().prop(context.scene, 'bsgimp_workshop_template_path')
		layout.row().prop(context.scene, 'bsgimp_backup_skin')
		layout.row().operator('mesh.importsaveglobalconfig', text = 'Save Global Configuration')

class LineTypeObjectSettings(bpy.types.Panel):
	bl_label = 'Line Type Blocks'
	bl_idname = 'PT_LineTypeSettingPanel'
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Besiege'
	bl_parent_id = 'PT_MainPanel'
	bl_options = {'DEFAULT_CLOSED'}



	def draw(self, context):
		layout = self.layout
		layout.row().prop(context.scene, 'bsgimp_line_type_brace_delete_threshold')
		layout.row().prop(context.scene, 'bsgimp_line_type_join_components')
		cleanup_row = layout.row()
		cleanup_row.prop(context.scene, 'bsgimp_line_type_cleanup_options')
		cleanup_row.enabled = context.scene.bsgimp_line_type_join_components


class SkinSettings(bpy.types.Panel):
	bl_label = 'Skin Settings'
	bl_idname = 'PT_SkinSettingsPanel'
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Besiege'
	bl_parent_id = 'PT_MainPanel'
	bl_options = {'DEFAULT_CLOSED'}

	def draw(self, context):
		layout = self.layout
		layout.row().prop(context.scene, 'bsgimp_use_vanilla_blocks')
		layout.row().prop(context.scene, 'bsgimp_generate_materials')
 
		bsgimp_use_node_group_row = layout.row()
		bsg_imp_node_set_row = layout.row()
		bsgimp_make_unique_node_groups_row = layout.row()

		bsgimp_use_node_group_row.prop(context.scene, 'bsgimp_use_node_group')
		layout.row().operator('materials.purgematerials', text = 'Purge Materials', icon='CANCEL')

		bsgimp_use_node_group_row.enabled = context.scene.bsgimp_generate_materials
		bsg_imp_node_set_row.enabled = bsgimp_make_unique_node_groups_row.enabled = context.scene.bsgimp_generate_materials and context.scene.bsgimp_use_node_group
		

class PurgeableMaterialList(bpy.types.PropertyGroup):
	obj_pointer = bpy.props.PointerProperty(name="ObjPointer", type=bpy.types.Material)

class SelectableImportedObjectList(bpy.types.PropertyGroup):
	obj_pointer = bpy.props.PointerProperty(name="ObjPointer", type=bpy.types.Object)

class ImportOperator(bpy.types.Operator):
	'''Import the selected besiege file'''
	bl_idname = 'mesh.importoperator'
	bl_label = 'Import Creation'

	def __init__(self):
		pass

	def execute(self, context):
		try:
			st_t = time.time()
			return_data = GlobalData.importer.ImportCreation(
				vanilla_skins=context.scene.bsgimp_use_vanilla_blocks,
				create_parent=context.scene.bsgimp_create_parent,
				join_line_components=context.scene.bsgimp_line_type_join_components,
				generate_material=context.scene.bsgimp_generate_materials,
				bracethreshold=context.scene.bsgimp_line_type_brace_delete_threshold,
				line_type_cleanup=context.scene.bsgimp_line_type_cleanup_options,
				node_grouping_mode=context.scene.bsgimp_make_unique_node_groups,
				use_node_groups=context.scene.bsgimp_use_node_group,
				node_group_setup=context.scene.bsgimp_node_set
				
			)
			et_t = time.time()
			for material in return_data['imported_materials']:
				newmat = bpy.context.scene.bsgimp_purgeable_materials.add()
				newmat.obj_pointer = material

			for object_imp in return_data['imported_objects']:
				try:
					newobj = bpy.context.scene.bsgimp_selectable_imports.add()
					# newobj.name = object_imp.name
					newobj.obj_pointer = object_imp
					# print(object_imp)
					# object_imp.select_set(True)
				except:
					pass

			self.report({'INFO'}, 'Import complete in {:.2f} seconds'.format((et_t - st_t)))
		except:
			self.report({'ERROR'}, 'Error encountered in the import process. Check console')
			traceback.print_exc() 
		return({'FINISHED'})

class PurgeMaterials(bpy.types.Operator):
	bl_idname = 'materials.purgematerials'
	bl_label = 'Purge Materials'

	def __init__(self):
		pass

	def execute(self, context):
		count = 0
		for material in bpy.context.scene.bsgimp_purgeable_materials:
			try:
				bpy.data.materials.remove(material.obj_pointer)
				print("Purged {}...".format(material))
				count += 1
			except:
				pass
		self.report({'INFO'}, "{} materials purged".format(count))
		return({'FINISHED'})

class SelectImportedObjects(bpy.types.Operator):
	bl_idname = 'obj.selectimported'
	bl_label = 'Select Imported Besiege Blocks'

	def __init__(self):
		pass

	def execute(self, context):
		for object_imp in bpy.context.scene.bsgimp_selectable_imports:
			try:
				object_imp.obj_pointer.select_set(True)
			except:
				pass
		return({'FINISHED'})

class SaveGlobalConfiguration(bpy.types.Operator):
	'''Save Global Configuration'''
	bl_idname = 'mesh.importsaveglobalconfig'
	bl_label = 'Simple Object Operator'

	def __init__(self):
		pass

	def execute(self, context):
		WriteGlobalConfig()
		return({'FINISHED'})

@persistent
def ReadGlobalConfig(*_):
	if not bpy.data.is_saved:
		print('Reading global config...')
		location = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.ini')
		if dev_mode: location = 'config.ini'
		if not Path(location).is_file:
			WriteGlobalConfig()
		config = configparser.ConfigParser()
		config.read(location)
		bpy.context.scene.bsgimp_template_path = config['GamePaths']['GameFolder']
		bpy.context.scene.bsgimp_workshop_template_path = config['GamePaths']['WorkshopFolder']
		bpy.context.scene.bsgimp_backup_skin = config['GamePaths']['Backup']

def WriteGlobalConfig():
	print('Writing global config...')
	config_loc = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.ini')
	if dev_mode: config_loc = 'config.ini'
	config = configparser.ConfigParser()
	config['GamePaths'] = {}
	config['GamePaths']['GameFolder'] = bpy.context.scene.bsgimp_template_path
	config['GamePaths']['WorkshopFolder'] = bpy.context.scene.bsgimp_workshop_template_path
	config['GamePaths']['Backup'] = bpy.context.scene.bsgimp_backup_skin
	with open(config_loc, 'w') as configfile:
		config.write(configfile)

def ReadFileStats(self, context):
	print("RUNNNING!")
	GlobalData.importer = blenapi.BlenderAPI(
		context.scene.bsgimp_workshop_template_path,
		context.scene.bsgimp_template_path,
		context.scene.bsgimp_backup_skin
	)
	GlobalData.result_data = GlobalData.importer.ReadMachine(bpy.path.abspath(context.scene.bsgimp_bsg_path))
	

def register():

	# register classes
	bpy.utils.register_class(MainPanel)
	bpy.utils.register_class(GeneralSettings)
	bpy.utils.register_class(SkinSettings)
	bpy.utils.register_class(LineTypeObjectSettings)
	bpy.utils.register_class(SettingsPanel)
	bpy.utils.register_class(SaveGlobalConfiguration)
	bpy.utils.register_class(ImportOperator)
	bpy.utils.register_class(PurgeMaterials)
	bpy.utils.register_class(PurgeableMaterialList)
	bpy.utils.register_class(SelectableImportedObjectList)
	bpy.utils.register_class(SelectImportedObjects)
	
	# register properties
	# paths
	bpy.types.Scene.bsgimp_bsg_path = bpy.props.StringProperty(name = '', update=ReadFileStats, default = '', description = 'Path to the Besiege Creation File (.bsg) you want to import', subtype = 'FILE_PATH')
	bpy.types.Scene.bsgimp_template_path = bpy.props.StringProperty(name = 'Game Folder', default='C:\\Program Files (x86)\\Steam\\steamapps\\common\\Besiege\\Besiege_Data\\Skins', description = 'Path to the skin folder in the game data folder.', subtype = 'DIR_PATH')
	bpy.types.Scene.bsgimp_workshop_template_path = bpy.props.StringProperty(name = 'Workshop Folder', default='C:\\Program Files (x86)\\Steam\\steamapps\\workshop\\content\\346010', description='Path to the Besiege workshop folder', subtype='DIR_PATH')
	bpy.types.Scene.bsgimp_backup_skin = bpy.props.StringProperty(name = 'Backup', default='C:\\Program Files (x86)\\Steam\\steamapps\\common\\Besiege\\Besiege_Data\\Skins\\Template', description='Path to the backup skin folder incase something goes wrong', subtype='DIR_PATH')
	
	# properties
	bpy.types.Scene.bsgimp_create_parent = bpy.props.BoolProperty(name = 'Create parent', default=False, description = 'Create a boundbox around creation and parent all blocks to it')

	# materials
	bpy.types.Scene.bsgimp_use_vanilla_blocks = bpy.props.BoolProperty(name = 'Use vanilla blocks', default=False, description = 'Ignore BSG file skin data and use vanilla blocks')
	bpy.types.Scene.bsgimp_generate_materials = bpy.props.BoolProperty(name = 'Generate materials', default=True, description = 'Generate node material for each type of block')
	bpy.types.Scene.bsgimp_node_set = bpy.props.EnumProperty(
		name='Node Setup',
		items=(
			('PRINCIPLED_BDSF', 'Principled BDSF', 'Simple Principled BDSF Setup'),
			('DIFFUSE_GLOSSY_MIX', 'Diffuse Glossy Mix BDSF', 'Simple node setup with Diffuse BDSF mixed with Glossy BDSF'),
			('EMISSION', 'Emission Node', 'Hook up the texture to an emission node')
		)
	)
	bpy.types.Scene.bsgimp_use_node_group = bpy.props.BoolProperty(name = 'Use node groups for materials', default=False, description='Use node groups to generate the materials for blocks')
	bpy.types.Scene.bsgimp_make_unique_node_groups = bpy.props.EnumProperty(
		name='Grouping Method',
		items=(
			('SAME_CONFIG', 'Same Group', 'Use the same node group for all blocks'),
			('FOR_EACH_BLOCK', 'By Block', 'Use one node group for each kind of block'),
			('FOR_EACH_SKIN', 'By Skin', 'Use one node group for each kind of skin')
		)
	)

	# line type object properties
	bpy.types.Scene.bsgimp_line_type_join_components = bpy.props.BoolProperty(name = 'Join components', default=True, description='If checked, the addon will join the components of a line type block')
	bpy.types.Scene.bsgimp_line_type_brace_delete_threshold = bpy.props.FloatProperty(name = 'Delete Threshold', default=0.5, description='The minimum length a line type block should be before the connector and end block gets deleted')
	bpy.types.Scene.bsgimp_line_type_cleanup_options = bpy.props.EnumProperty(
		name='Cleanup Action',
		items=(
			('DELETE_EMPTIES', 'Delete Empties', 'Delete empties after joining line type blocks'),
			('HIDE_EMPTIES', 'Hide empties', 'Hide empties after joining line type blocks'),
			('DO_NOTHING', 'Do Nothing', 'Do absolutely nothing')
		)
	)

	bpy.types.Scene.bsgimp_purgeable_materials = bpy.props.CollectionProperty(type=PurgeableMaterialList)
	bpy.types.Scene.bsgimp_selectable_imports = bpy.props.CollectionProperty(type=SelectableImportedObjectList)

	bpy.app.handlers.load_post.append(ReadGlobalConfig)

def unregister():
	# unregister classes	
	bpy.utils.unregister_class(MainPanel)
	bpy.utils.unregister_class(SkinSettings)
	bpy.utils.unregister_class(LineTypeObjectSettings)
	bpy.utils.unregister_class(SettingsPanel)
	bpy.utils.unregister_class(ImportOperator)
	bpy.utils.unregister_class(SaveGlobalConfiguration)
	bpy.utils.unregister_class(GeneralSettings)
	bpy.utils.unregister_class(PurgeMaterials)
	bpy.utils.unregister_class(PurgeableMaterialList)
	bpy.utils.unregister_class(SelectableImportedObjectList)
	bpy.utils.unregister_class(SelectImportedObjects)

	# unregister properties
	del bpy.types.Scene.bsgimp_bsg_path
	del bpy.types.Scene.bsgimp_template_path
	del bpy.types.Scene.bsgimp_workshop_template_path
	del bpy.types.Scene.bsgimp_backup_skin
	del bpy.types.Scene.bsgimp_use_vanilla_blocks
	del bpy.types.Scene.bsgimp_generate_materials
	del bpy.types.Scene.bsgimp_create_parent
	del bpy.types.Scene.bsgimp_line_type_join_components
	del bpy.types.Scene.bsgimp_line_type_brace_delete_threshold
	del bpy.types.Scene.bsgimp_purgeable_materials
	del bpy.types.Scene.bsgimp_make_unique_node_groups
	del bpy.types.Scene.bsgimp_use_node_group
	del bpy.types.Scene.bsgimp_line_type_cleanup_options
	del bpy.types.Scene.bsgimp_selectable_imports
	

#This is required in order for the script to run in the text editor   
if __name__ == '__main__':
	register()
	