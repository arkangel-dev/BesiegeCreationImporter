from math import radians, pi

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
		return val * pi / 180