import bpy

# This class contains a list of methods to generate materials. I'll be adding more
# material generation classes later. For stuff like canon muzzle flashes, smoke and etc
class MaterialList():

		
	def DefaultMaterial(self, block, texture_path, skin_name, replace_material=""):
		"""
		This is the default skin for the blocks. Just a simple texture node hooked up to 
		a Principled BDSF shader.
		"""
		material_name = skin_name
		lookup = self.ReturnPreExisting(material_name)
		if lookup: return lookup
		m = bpy.data.materials.new(name=material_name)
		m.use_nodes = True
		nodes = m.node_tree.nodes
		nodes.clear()
		image_texture_node = nodes.new("ShaderNodeTexImage")
		principled_bdsf_node = nodes.new("ShaderNodeBsdfPrincipled")
		output_node = nodes.new("ShaderNodeOutputMaterial")

		image_texture_node.location = (0,0)
		principled_bdsf_node.location = (300,0)
		output_node.location = (600,0)

		image_texture_node.image = bpy.data.images.load(texture_path)
		m.node_tree.links.new(principled_bdsf_node.inputs[0], image_texture_node.outputs[0])
		m.node_tree.links.new(output_node.inputs[0], principled_bdsf_node.outputs[0])
		return m

	def ReturnPreExisting(self, material_name):
		for m in bpy.data.materials:
			if material_name.__eq__(m.name):
				return m
		return False
	
	def NodeGroupMaterial(self, block, texture_path, skin_name, node_group):
		material_name = skin_name + "NodeGrouped"
		lookup = self.ReturnPreExisting(material_name)
		if lookup: return lookup
		m = bpy.data.materials.new(name=material_name)
		m.use_nodes = True
		nodes = m.node_tree.nodes
		nodes.clear()

		image_texture_node = nodes.new('ShaderNodeTexImage')
		node_group_node = nodes.new('ShaderNodeGroup')
		# output_node = nodes.new("ShaderNodeOutputMaterial")

		image_texture_node.location = (0, 0)
		node_group_node.location = (300, 0)
		# output_node.location = (500, 0)

		node_group_node.node_tree = node_group
		image_texture_node.image = bpy.data.images.load(texture_path)

		m.node_tree.links.new(node_group_node.inputs[0], image_texture_node.outputs[0])
		m.node_tree.links.new(node_group_node.inputs[1], image_texture_node.outputs[1])
		return m

class NodeGroups():
	def SimplePrincipledBDSF(self, name='BasicPrincipledShader'):
		# create a group
		shader_group = bpy.data.node_groups.new(name, 'ShaderNodeTree')

		# create group inputs
		group_inputs = shader_group.nodes.new('NodeGroupInput')
		shader_group.inputs.new('NodeSocketColor','Color')
		shader_group.inputs.new('NodeSocketFloat','Alpha')

		# create group outputs
		# group_outputs = shader_group.nodes.new('NodeGroupOutput')
		# shader_group.outputs.new('NodeSocketShader','Shader')
		principled_bdsf_node = shader_group.nodes.new("ShaderNodeBsdfPrincipled")
		output_node = shader_group.nodes.new("ShaderNodeOutputMaterial")

		group_inputs.location = (-50,0)
		principled_bdsf_node.location = (150, 0)
		output_node.location = (500, 0)

		shader_group.links.new(principled_bdsf_node.inputs[0], group_inputs.outputs[0])
		shader_group.links.new(principled_bdsf_node.outputs[0], output_node.inputs[0])
		return shader_group