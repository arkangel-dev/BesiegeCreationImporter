bl_info = {
	"name": "Import Besiege Machines",
	"author": "Sam Ramirez",
	"version": (1, 2),
	"blender": (2, 90, 0),
	"location": "View3D > Toolbar > Besiege",
	"description": "Imports Besiege Creation Files (.bsg) files",
	"warning": "This addon is still being worked on",
	"wiki_url": "",
	"category": "Import-Export",
}

# from . import blenapi
import blenapi
import bpy
import xml.etree.ElementTree as ET
import os
import json
import configparser
import threading
from pathlib import Path

	#This is the Main Panel (Parent of Panel A and B)
class MainPanel(bpy.types.Panel):
	bl_label = "Besiege Import"
	bl_idname = "PT_MainPanel"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Besiege'

   
	def draw(self, context):
		layout = self.layout
		layout.scale_x = 2
	
		layout.row().prop(context.scene, 'bsgimp_bsg_path', icon='FILE')
		layout.row().prop(context.scene, 'bsgimp_generate_materials')
		layout.row().prop(context.scene, 'bsgimp_create_parent')
		layout.row().prop(context.scene, 'bsgimp_use_vanilla_blocks')
		layout.row().prop(context.scene, 'bsgimp_halt_missing')
		layout.row().operator("mesh.importoperator", text = "Import")

class SettingsPanel(bpy.types.Panel):
	bl_label = "Settings"
	bl_idname = "PT_SettingsPanel"
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
		layout.row().operator("mesh.importsaveglobalconfig", text = "Save Global Configuration")


class ImportOperator(bpy.types.Operator):
	"""Import the selected besiege file"""
	bl_idname = "mesh.importoperator"
	bl_label = "Simple Object Operator"

	importer = None

	def __init__(self):
		pass

	def execute(self, context):
		self.importer = blenapi.BlenderAPI(
			context.scene.bsgimp_workshop_template_path,
			context.scene.bsgimp_template_path,
			context.scene.bsgimp_backup_skin
		)

		self.importer.ImportCreation(
			bpy.path.abspath(context.scene.bsgimp_bsg_path), 
			vanilla_skins=context.scene.bsgimp_use_vanilla_blocks,
			create_parent=context.scene.bsgimp_create_parent
		)
		return({'FINISHED'})

class SaveGlobalConfiguration(bpy.types.Operator):
	"""Save Global Configuration"""
	bl_idname = "mesh.importsaveglobalconfig"
	bl_label = "Simple Object Operator"

	def __init__(self):
		pass

	def execute(self, context):
		pass
  
def register():
	# register classes
	bpy.utils.register_class(MainPanel)
	bpy.utils.register_class(SettingsPanel)
	bpy.utils.register_class(ImportOperator)
	bpy.utils.register_class(SaveGlobalConfiguration)
	
	# register properties
	# paths
	bpy.types.Scene.bsgimp_bsg_path = bpy.props.StringProperty(name = "BSG File", default = "", description = "Path to the Besiege Creation File (.bsg) you want to import", subtype = 'FILE_PATH')
	bpy.types.Scene.bsgimp_template_path = bpy.props.StringProperty(name = "Game Folder", default="C:\\Program Files (x86)\\Steam\\steamapps\\common\\Besiege\\Besiege_Data\\Skins", description = "Path to the skin folder in the game data folder.", subtype = 'DIR_PATH')
	bpy.types.Scene.bsgimp_workshop_template_path = bpy.props.StringProperty(name = "Workshop Folder", default="C:\\Program Files (x86)\\Steam\\steamapps\\workshop\\content\\346010", description="Path to the Besiege workshop folder", subtype="DIR_PATH")
	bpy.types.Scene.bsgimp_backup_skin = bpy.props.StringProperty(name = "Backup", default="C:\\Program Files (x86)\\Steam\\steamapps\\common\\Besiege\\Besiege_Data\\Skins\\Template", description="Path to the backup skin folder incase something goes wrong", subtype="DIR_PATH")
	
	# properties
	bpy.types.Scene.bsgimp_use_vanilla_blocks = bpy.props.BoolProperty(name = "Use vanilla blocks", default=False, description = "Ignore BSG file skin data and use vanilla blocks")
	bpy.types.Scene.bsgimp_generate_materials = bpy.props.BoolProperty(name = "Generate materials", default=True, description = "Generate node material for each type of block")
	bpy.types.Scene.bsgimp_halt_missing = bpy.props.BoolProperty(name = "Stop import on missing skin", default=False, description = "Stop the import process if a specific skin could not be found")
	bpy.types.Scene.bsgimp_create_parent = bpy.props.BoolProperty(name = "Create parent", default=False, description = "Create a boundbox around creation and parent all blocks to it")

def unregister():
	# unregister classes	
	bpy.utils.unregister_class(MainPanel)
	bpy.utils.unregister_class(SettingsPanel)
	bpy.utils.unregister_class(ImportOperator)
	bpy.utils.unregister_class(SaveGlobalConfiguration)

	# unregister properties
	del bpy.types.Scene.bsgimp_bsg_path
	del bpy.types.Scene.bsgimp_template_path
	del bpy.types.Scene.bsgimp_workshop_template_path
	del bpy.types.Scene.bsgimp_backup_skin
	del bpy.types.Scene.bsgimp_use_vanilla_blocks
	del bpy.types.Scene.bsgimp_generate_materials
	del bpy.types.Scene.bsgimp_halt_missing
	del bpy.types.Scene.bsgimp_create_parent

#This is required in order for the script to run in the text editor   
if __name__ == "__main__":
	register()  