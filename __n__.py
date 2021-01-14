import bpy

bl_info = {
	'name': 'Material Git',
	'author': 'Sam Ramirez',
	'version': (1, 0, 0),
	'blender': (2, 90, 1),
	'location': 'View3D > Toolbar > ??',
	'description': 'Modifies the materials of selected objects to have a custom node group which will get fed a RGB node',
	'category': 'Materials',
	'tracker_url' : '',
	'wiki_url': '',
	'support' : 'COMMUNITY',
}


class MainPanel(bpy.types.Panel):
	bl_label = "Clone Material Color"
	bl_idname = "PT_CloneMaterial"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = ""
	
	def draw(self, context):
		layout = self.layout
		layout.scale_x = 0
		layout.row().prop(context.scene, 'node_group_name')
		layout.row().operator('material.clonevcolor', text='Clone')
		
class PerformOperation(bpy.types.Operator):
	'''Import the selected besiege file'''
	bl_idname = 'material.clonevcolor'
	bl_label = 'Process'
	
	def __init__(self):
		pass
	
	def execute(self, context):
		node_group = bpy.data.node_groups.new(context.scene.node_group_name, 'ShaderNodeTree')
		group_inputs = node_group.nodes.new('NodeGroupInput')
		node_group.inputs.new('NodeSocketColor','Color')
		principled_bdsf_node = node_group.nodes.new("ShaderNodeBsdfPrincipled")
		output_node = node_group.nodes.new("ShaderNodeOutputMaterial")
		node_group.links.new(principled_bdsf_node.inputs[0], group_inputs.outputs[0])
		node_group.links.new(principled_bdsf_node.outputs[0], output_node.inputs[0])

		
		for obj in context.selected_objects:
			for mat in obj.material_slots:
				tree = mat.material.node_tree
				mat.material.use_nodes = True
				tree.nodes.clear()

				
				rgb_node = tree.nodes.new('ShaderNodeRGB')
				rgb_node.outputs[0].default_value = obj.active_material.diffuse_color

				node_group_node = tree.nodes.new('ShaderNodeGroup')
				node_group_node.node_tree = node_group

				tree.links.new(rgb_node.outputs[0], node_group_node.inputs[0])

		return {'FINISHED'}
		
def register():
	bpy.utils.register_class(MainPanel)
	bpy.utils.register_class(PerformOperation)
	bpy.types.Scene.node_group_name = bpy.props.StringProperty(name='Name', default='Default')
	
	
def unregister():
	bpy.utils.unregister_class(MainPanel)
	bpy.utils.unregister_class(PerformOperation)
	del bpy.types.Scene.node_group_name
	
if __name__ == '__main__':
	register()