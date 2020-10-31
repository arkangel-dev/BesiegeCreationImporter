import bpy

# This class contains a list of methods to generate materials. I'll be adding more
# material generation classes later. For stuff like canon muzzle flashes, smoke and etc
class DefaultMaterial():
	"""
	This is the default skin for the blocks. Just a simple texture node hooked up to 
	a Principled BDSF shader.
	"""
	texture_path = ""
	skin_name = ""
	material_name = ""
	replace_mat_name = ""
	block = None
	material = None

	def __init__(self, block, texture_path, skin_name, replace_material=""):
		"""
		Create Principled BDSF node setup
		"""
		self.replace_mat_name = replace_material
		self.texture_path = texture_path
		self.skin_name = skin_name
		self.block = block
		self.material_name = skin_name
		self.material = replace_material
		for m in bpy.data.materials:
			if self.material_name.__eq__(m.name):
				self.material = m
		self.Generate()
		

		
	def Generate(self):
		"""
		Generate node setup. Returns data type nodes
		"""
		m = bpy.data.materials.new(name=self.material_name)
		m.use_nodes = True
		nodes = m.node_tree.nodes
		nodes.clear()
		image_texture_node = nodes.new("ShaderNodeTexImage")
		principled_bdsf_node = nodes.new("ShaderNodeBsdfPrincipled")
		output_node = nodes.new("ShaderNodeOutputMaterial")
		image_texture_node.image = bpy.data.images.load(self.texture_path)
		m.node_tree.links.new(principled_bdsf_node.inputs[0], image_texture_node.outputs[0])
		m.node_tree.links.new(output_node.inputs[0], principled_bdsf_node.outputs[0])
		self.material = m
		return m
