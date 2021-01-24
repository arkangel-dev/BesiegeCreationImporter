from math import radians, pi
from mathutils import Quaternion

class Block():
	"""
	This class will define each block from the BSG file... 
	It will contain a list of components which contain actual blocks and will be used to define blocks with multiple obj files...
	It will also contain the position, rotation and scale defined by the 
	"""
	
	components = []
	block_id = ""
	guid = ""
	name = ""
	code_name = ""
	flipped = ""

	machine_rotation_quart_x = 0.0
	machine_rotation_quart_y = 0.0
	machine_rotation_quart_z = 0.0
	machine_rotation_quart_w = 0.0

	_translate_x, _translate_y, _translate_z = [0.0, 0.0, 0.0]
	_rotation_x, _rotation_y, _rotation_z, _rotation_w = [0.0, 0.0, 0.0, 0.0]
	_scale_x, _scale_y, _scale_z = [0.0, 0.0, 0.0]

	_spx, _spy, _spz = [0,0,0]
	_epx, _epy, _epz = [0,0,0]
	_srx, _sry, _srz = [0,0,0]
	_erx, _ery, _erz = [0,0,0]


	def __init__(self, translation:list, rotation:list, scale:list):
		"""
		Constructor
		Parameters : __init__([x,y,z], [x,y,z,w], [x,y,z])
		"""
		self._translate_x, self._translate_z, self._translate_y = translation
		self._rotation_x, self._rotation_y, self._rotation_z, self._rotation_w = rotation
		self._scale_x, self._scale_y, self._scale_z = scale
		self.components = []

	def getQuarternion(self):
		"""Get the rotation in quarternions in WXYZ"""
		return [self._rotation_w, self._rotation_x, self._rotation_z, self._rotation_y]

	def getVectorPosition(self):
		"""Get the location in a 3d vector in XYZ"""
		return (self._translate_x, self._translate_y, self._translate_z)

	def getScale(self):
		"""Get the scale in XYZ"""
		return (self._scale_x, self._scale_z, self._scale_y)

	def SetLineTypeGeometry(self, start_pos, end_pos, start_rot, end_rot):
		self._spx, self._spz, self._spy = [float(x) for x in start_pos]
		self._epx, self._epz, self._epy = [float(x) for x in end_pos]
		self._srx, self._sry, self._srz = [float(x) for x in start_rot]
		self._erx, self._ery, self._erz = [float(x) for x in end_rot]

	def GetLineStartPosition(self):
		return (self._spx, self._spy, self._spz)

	def GetLineEndPosition(self):
		return (self._epx, self._epy, self._epz)

	def GetLineStartRotation(self):
		return (self.Convert(self._srx), self.Convert(self._srz), self.Convert(self._sry))

	def GetLineEndRotation(self):
		return (self.Convert(self._erx), self.Convert(self._erz), self.Convert(self._ery))

	def Convert(self, val):
		return radians(val)

	def SetGlobalMachineRotation(self, x, y, z, w):
		self.machine_rotation_quart_w = w
		self.machine_rotation_quart_x = x
		self.machine_rotation_quart_y = y
		self.machine_rotation_quart_z = z

	def GetGlobalMachineRotation(self):
		return Quaternion((self.machine_rotation_quart_w, self.machine_rotation_quart_x, self.machine_rotation_quart_z, self.machine_rotation_quart_y))


# class Surface():
# 	# edge list
# 	block_id = "73"
# 	guid = ""
# 	edges = []

# 	# appearence data
# 	hue_col = [0,0,0]
# 	saturation = 0.0
# 	lum = 0.0
# 	skin = ""
# 	skin_id = ""

# 	IsQuad = True
# 	FalseIndex = 0

# 	U_Lines = []
# 	V_Lines = []

# 	def __init__(self, _guid):
# 		self.guid = _guid
# 		self.edges = []
# 		self.U_Lines = []
# 		self.V_Lines = []
# 		self.IsQuad = True

	# def GetTotalEdgePos(self) -> float:
	# 	total_x = 0
	# 	total_y = 0
	# 	total_z = 0
	# 	for edge in self.edges:
	# 		total_x += edge.x
	# 		total_y += edge.y
	# 		total_z += edge.z
	# 	return [total_x, total_y, total_z]

# 	def GetTotalPointPos(self):
# 		total_x = 0
# 		total_y = 0
# 		total_z = 0
# 		for edge in self.edges:
# 			total_x += edge.s_x
# 			total_y += edge.s_y
# 			total_z += edge.s_z



# 		if not self.IsQuad:
# 			total_x -= self.edges[self.FalseIndex].x
# 			total_y -= self.edges[self.FalseIndex].y
# 			total_z -= self.edges[self.FalseIndex].z

# 		return [total_x, total_y, total_z]

# 	def GetCenterControlPoint(self) -> list:
# 		center_point = [0,0,0]
# 		total_edges_pos = self.GetTotalEdgePos()
# 		total_points_pos = self.GetTotalPointPos()
# 		center_point[0] = 2 * (total_edges_pos[0] / 4) - (total_points_pos[0] / 4)
# 		center_point[1] = 2 * (total_edges_pos[1] / 4) - (total_points_pos[1] / 4)
# 		center_point[2] = 2 * (total_edges_pos[2] / 4) - (total_points_pos[2] / 4)
# 		return center_point

# 	def GetMidCurveU(self) -> list:
# 		center = self.GetCenterControlPoint()
# 		start = [self.V_Lines[0].x, self.V_Lines[0].y, self.V_Lines[0].z]
# 		end = [self.V_Lines[1].x, self.V_Lines[1].y, self.V_Lines[1].z]
# 		if not self.IsQuad:
# 			end = self.GetFalseEdge().GetStartLocation()
# 		return [start, center, end]

# 	def GetFalseEdge(self):
# 		for edge in self.edges:
# 			if edge.Skip:
# 				print("Found")
# 				return edge



	
class BuildSurfaceEdge():
	guid = ""
	IsFalseEdge = False
	sx, sy, sz = [0,0,0]
	mx, my, mz = [0,0,0]
	ex, ey, ez = [0,0,0]

	def __init__(self, guid:str) -> None:
		self.guid = guid
		self.sx, self.sy, self.sz = [0,0,0]
		self.mx, self.my, self.mz = [0,0,0]
		self.ex, self.ey, self.ez = [0,0,0]
		self.IsFalseEdge = False

	def GetStartPoint(self) -> list:
		return [self.sx, self.sy, self.sz]

	def SetStartPoint(self, points:list) -> None:
		self.sx = points[0]
		self.sy = points[1]
		self.sz = points[2]

	def GetMidPoint(self) -> list:
		return [self.mx, self.my, self.mz]

	def SetMidPoint(self, points:list) -> None:
		self.mx = points[0]
		self.my = points[1]
		self.mz = points[2]

	def GetEndPoint(self) -> list:
		return [self.ex, self.ey, self.ez]

	def SetEndPoint(self, points:list) -> None:
		self.ex = points[0]
		self.ey = points[1]
		self.ez = points[2]
	
	def GetCurveMidControlPoint(self) -> list:
		midpoint = [
			(self.GetEndPoint()[0] + self.GetStartPoint()[0]) / 2,
			(self.GetEndPoint()[1] + self.GetStartPoint()[1]) / 2,
			(self.GetEndPoint()[2] + self.GetStartPoint()[2]) / 2
		]
		return [
			midpoint[0] + (self.GetMidPoint()[0] - midpoint[0]) * 2,
			midpoint[1] + (self.GetMidPoint()[1] - midpoint[1]) * 2,
			midpoint[2] + (self.GetMidPoint()[2] - midpoint[2]) * 2
		]

	def InvertPointLocations(self) -> list:
		temp = self.GetEndPoint()
		self.SetEndPoint(self.GetStartPoint())
		self.SetStartPoint(temp)
	

class BuildSurface():
	block_id = "73"
	edge_a = BuildSurfaceEdge("")
	edge_b = BuildSurfaceEdge("")
	edge_c = BuildSurfaceEdge("")

	guid = ""
	IsQuad = True
	RawEdgeList = []

	def __init__(self, guid:str) -> None:
		self.guid = guid
		self.IsQuad = True
		self.EdgeList = []
	
	def SetEdgeData(self, edges:list) -> None:
		self.edge_a = edges[0]
		self.edge_b = edges[1]
		self.edge_c = edges[2]


