

class Component():
	"""
	This class defines the actual blocks.
	"""
	_offset_translate_x, _offset_translate_y, _offset_translate_z = 0.0, 0.0, 0.0
	_offset_rotation_x, _offset_rotation_y, _offset_rotation_z = 0.0, 0.0, 0.0
	_offset_scale_x, _offset_scale_y, _offset_scale_z = 0.0, 0.0, 0.0
	_line_start_pos_x, _line_start_pos_y, _line_start_pos_z = 0.0, 0.0, 0.0
	_line_start_rot_x, _line_start_rot_y, _line_start_rot_z = 0.0, 0.0, 0.0
	_line_end_pos_x, _line_end_pos_y, _line_end_pos_z = 0.0, 0.0, 0.0
	_line_end_rot_x, _line_end_rot_y, _line_end_rot_z = 0.0, 0.0, 0.0

	object_source = ""
	group = ""
	base_source = ""
	skin_name = ""
	skin_id = ""

	line_type_start = ""
	line_type_end = ""
	line_type_middle = ""
	line_type_block = False
	
	def __init__(self, translate:list, rotation:list, scale:list):
		self._offset_translate_x, self._offset_translate_z, self._offset_translate_y = translate
		self._offset_rotation_x, self._offset_rotation_y, self._offset_rotation_z = rotation
		self._offset_scale_x, self._offset_scale_z, self._offset_scale_y = scale

	def SetLineTypeGeometry(self, start_pos, start_rot, end_pos, end_rot):
		self._line_start_pos_x, self._line_start_pos_y, self._line_start_pos_z = start_pos
		self._line_start_rot_x, self._line_start_rot_y, self._line_start_rot_z = start_rot
		self._line_end_pos_x, self._line_end_pos_y, self._line_end_pos_z = end_pos
		self._line_end_rot_x, self._line_end_rot_y, self._line_end_rot_z = end_rot

		

