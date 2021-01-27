import bpy
import os

# This class contains a list of methods to generate materials. I'll be adding more
# material generation classes later. For stuff like canon muzzle flashes, smoke and etc
class MaterialList():

	@staticmethod
	# source: https://blenderartists.org/t/rgb2hsv-convert-rgb-to-hsv/433186/4
	def RGBtoHSV(R,G,B):
		# min, max, delta;
		min_rgb = min( R, G, B )
		max_rgb = max( R, G, B )
		V = max_rgb

		delta = max_rgb - min_rgb
		if not delta:
			H = 0
			S = 0
			V = R # RGB are all the same.
			return H,S,V
			
		elif max_rgb: # != 0
			S = delta / max_rgb
		else:
			R = G = B = 0 # s = 0, v is undefined
			S = 0
			H = 0 # -1
			return H,S,V

		if R == max_rgb:
			H = ( G - B ) / delta # between yellow & magenta
		elif G == max_rgb:
			H = 2 + ( B - R ) / delta # between cyan & yellow
		else:
			H = 4 + ( R - G ) / delta # between magenta & cyan

		H *= 60 # degrees
		if H < 0:
			H += 360
		
		return H,S,V

	@staticmethod
	def ReturnPreExisting(material_name):
		try: return bpy.data.materials[material_name]
		except KeyError: return False
		
	@staticmethod
	def DefaultMaterial(block, texture_path, skin_name, replace_material=""):
		"""
		This is the default skin for the blocks. Just a simple texture node hooked up to 
		a Principled BDSF shader.
		"""
		material_name = skin_name
		lookup =  MaterialList.ReturnPreExisting(material_name)
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

	@staticmethod
	def NodeGroupSurfaceMaterial(texture_path, material_name, node_group, surface):
		glass = surface.MaterialType == 2
		if glass: material_name += "Glass"
		

		if surface.UsePaint: material_name += surface.guid
		lookup = MaterialList.ReturnPreExisting(material_name)
		if lookup: return lookup
		m = bpy.data.materials.new(name=material_name)
		m.use_nodes = True
		nodes = m.node_tree.nodes
		nodes.clear()

		image_texture_node = nodes.new('ShaderNodeTexImage')
		node_group_node = nodes.new('ShaderNodeGroup')
		mix_node = nodes.new('ShaderNodeMixRGB')
		hsv_node = nodes.new("ShaderNodeCombineHSV")

		node_group_node.node_tree = node_group
		node_group_node.inputs[2].default_value = 1 if glass else 0
		image_texture_node.image = bpy.data.images.load(texture_path)
		mix_node.inputs[0].default_value = 0.95 if surface.UsePaint else 0
		mix_node.blend_type = 'OVERLAY'
		hue_val = MaterialList.RGBtoHSV(surface.col_rgb[0], surface.col_rgb[1], surface.col_rgb[2])[0]
		hsv_node.inputs[0].default_value = hue_val / 360
		hsv_node.inputs[1].default_value = surface.saturation
		hsv_node.inputs[2].default_value = surface.luminosity

		m.node_tree.links.new(image_texture_node.outputs[0], mix_node.inputs[1])
		m.node_tree.links.new(mix_node.outputs[0], node_group_node.inputs[0])
		m.node_tree.links.new(hsv_node.outputs[0], mix_node.inputs[2])
		m.node_tree.links.new(image_texture_node.outputs[1], node_group_node.inputs[1])

		return m


	@staticmethod
	def NodeGroupMaterial(texture_path, skin_name, node_group):
		material_name = skin_name + "-NodeGrouped"
		lookup = MaterialList.ReturnPreExisting(material_name)
		if lookup: return lookup
		m = bpy.data.materials.new(name=material_name)
		m.use_nodes = True
		nodes = m.node_tree.nodes
		nodes.clear()

		image_texture_node = nodes.new('ShaderNodeTexImage')
		node_group_node = nodes.new('ShaderNodeGroup')

		image_texture_node.location = (0, 0)
		node_group_node.location = (300, 0)
		node_group_node.node_tree = node_group
		image_texture_node.image = bpy.data.images.load(texture_path)
		m.node_tree.links.new(node_group_node.inputs[0], image_texture_node.outputs[0])
		m.node_tree.links.new(node_group_node.inputs[1], image_texture_node.outputs[1])
		return m

class NodeGroups():
	@staticmethod
	def SimplePrincipledBDSF(name='BasicPrincipledShader'):
		# create a group
		shader_group = bpy.data.node_groups.new(name, 'ShaderNodeTree')

		# create group inputs
		group_inputs = shader_group.nodes.new('NodeGroupInput')
		shader_group.inputs.new('NodeSocketColor','Color')
		shader_group.inputs.new('NodeSocketFloat','Alpha')

		# create group outputs
		principled_bdsf_node = shader_group.nodes.new("ShaderNodeBsdfPrincipled")
		output_node = shader_group.nodes.new("ShaderNodeOutputMaterial")

		group_inputs.location = (-50,0)
		principled_bdsf_node.location = (150, 0)
		output_node.location = (500, 0)
		shader_group.links.new(principled_bdsf_node.inputs[0], group_inputs.outputs[0])
		shader_group.links.new(principled_bdsf_node.outputs[0], output_node.inputs[0])
		return shader_group

	@staticmethod
	def SurfaceBlockPrincipledBDSF(name="SimpleSurfaceBlockPrincipledBDSF", custom_block_dir=""):
		shader_group = bpy.data.node_groups.new(name,  'ShaderNodeTree')

		group_inputs = shader_group.nodes.new('NodeGroupInput')
		shader_group.inputs.new('NodeSocketColor', 'Color')
		shader_group.inputs.new('NodeSocketFloat', 'Alpha')
		shader_group.inputs.new('NodeSocketFloat', 'Glass')

		principled_bdsf = shader_group.nodes.new('ShaderNodeBsdfPrincipled')
		glass_node = shader_group.nodes.new('ShaderNodeBsdfGlass')
		mix_shader = shader_group.nodes.new('ShaderNodeMixShader')
		image_texture_node = shader_group.nodes.new('ShaderNodeTexImage')
		output_node = shader_group.nodes.new('ShaderNodeOutputMaterial')
		math_node = shader_group.nodes.new('ShaderNodeMath')

		principled_bdsf.location = (-140, -80)
		glass_node.location = (-60, 100)
		mix_shader.location = (160, 0)
		image_texture_node.location = (-540, 160)
		output_node.location = (320, 0)
		math_node.location = (-240, 100)
		group_inputs.location = (-330, -120)

		image_texture_node.image = bpy.data.images.load(os.path.join(custom_block_dir, 'BuildSurface', 'GlassTex.png'))
		math_node.operation = 'MULTIPLY'
		math_node.inputs[1].default_value = 3

		shader_group.links.new(group_inputs.outputs[0], principled_bdsf.inputs[0])
		shader_group.links.new(image_texture_node.outputs[0], math_node.inputs[0])
		shader_group.links.new(math_node.outputs[0], glass_node.inputs[1])
		shader_group.links.new(glass_node.outputs[0], mix_shader.inputs[2])
		shader_group.links.new(group_inputs.outputs[2], mix_shader.inputs[0])
		shader_group.links.new(principled_bdsf.outputs[0], mix_shader.inputs[1])
		shader_group.links.new(mix_shader.outputs[0], output_node.inputs[0])

		return shader_group

