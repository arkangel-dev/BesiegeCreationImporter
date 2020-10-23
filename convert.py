import json

object_atlas = {}
converted = {}

with open('object_transform_data_converted.json') as json_file:
    object_atlas = json.load(json_file)

for x in object_atlas.keys():
	print(x)
	base = object_atlas[x]
	template = {
		'display_name': base['display_name'],
        'code_name': base['code_name'],
        'components': [{
            'base_source': base['components'][0]['base_source'],
            'group': 'BASE',
			'line_type_blocks' : False,
			'override_purge_materials' : False,
			'update_materials' : [],
            'offset': {
                'position': {
                    'x': base['components'][0]['offset']['position']['x'],
                    'y': base['components'][0]['offset']['position']['y'],
                    'z': base['components'][0]['offset']['position']['z']
                },
                'rotation': {
                    'x': base['components'][0]['offset']['rotation']['x'],
                    'y': base['components'][0]['offset']['rotation']['y'],
                    'z': base['components'][0]['offset']['rotation']['z']
                },
                'scale': {
                    'x': base['components'][0]['offset']['scale']['x'],
                    'y': base['components'][0]['offset']['scale']['y'],
                    'z': base['components'][0]['offset']['scale']['z']
                }
            }
        }]
	}

	converted.update({x : template})


with open('object_transform_data_converted_v2.json', 'w') as f:
    json.dump(converted, f, indent=4)