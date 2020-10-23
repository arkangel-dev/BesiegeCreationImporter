# :computer: Besiege Creation Import Addon for Blender

#### Fixing *"flippable"* object rotations

So there are some blocks that can be flipped. Most blocks when flipped get their physics engine behavior changed such as rotation. But some blocks like small propeller and propeller get their geometry updated. So normally their they are rotated 90 degrees in the Y axis. And in the code, if the block is defined as flipped, 23 degrees will be subtracted and if its not flipped 23 degrees will be added. Note that this modification to the Y axis should be applied to during the normalization stage (apply transformation stage)



#### Packing Up Addon for Skin Support Update

**Date : ** 10/11/2020

So today I'll be packing up the addon for the new update addon that supports skins. Gave it to Fnom for testing. Found some bugs. I'll be fixing them tomorrow, its getting late.



#### Skin Support for Block Components

**Date :** 10/10/2020

The addon now can import models with skins. But since I rewrote the object atlas structure, I had to rewrite the import code. And because I hate myself, I decided to make it object oriented. So that meant the code is in complete disarray and I'll have to rewrite the Blender UI code to make that thing OO too. So yeah, I think I'm making good progress

**Update : ** So I thought the new OO import code was working. Turns out it wasn't. The rotation is still weird. Once I fix that, I'll be able to make a release of the addon that supports importing skins. Hopefully I can make a polished version by next week

**Update :** So now the new import code is working fine. It turned out that my dumbass was using the position `xyz` data for the rotation offset step instead of the actual rotation data. So once I got that working, the addon was working perfectly. Yay.

#### Notes

```
- [X] Transform Offset : xzy
- [X] Rotation Offset : xyz
- [X] Scale Offset : xzy
- [X] Transform : xzy
- [X] Rotation : wxzy
- [X] Scale : xzy
```



### New Object Atlas Structure and XML Parser Bullshit

**Date :** 10/9/2020

The atlas is JSON file that defines how the OBJ files should be normalized. So in the previous version the atlas defines a single OBJ file and its offset data for each block. Its however it is a bit limiting, for example the Crossbow OBJ file doesn't include the arrow that it shoots in-game. 

In the new atlas, I suggest that for each model, multiple OBJ files, and their offset data be defined. From this point on, I will refer the OBJ files and their offset data as 'components'. So  with the new structure it allows stuff like arrows to be visible on cross bows, canon balls can be shown along with canons and fire textures. It just adds an extra layer of detail on top of the current bland version

But I'm getting ahead of myself. The new structure with multiple components can be also used to define the  starting and ending positions of the special blocks such as brace, contract spring block and rope'n'winch block. This part is super important because almost every single Besiege creation uses brace cubes, Sometimes for support and sometimes of aesthetic purposes. So the absence of brace cubes is pretty bad.

But lets look into how the new atlas is structured. Below is the atlas that is defining the speedometer block. The first keys in the root are pretty self-explanatory. As you can see the components key is an array. Each component has a `base_source` key which defines the folder the OBJ file is located at. The group key allows components to be groups. Because I wish for the effects such as crossbow bolts and canon fire to be toggleable when importing. Also the components define a key called `translation_src`. This part, I'm pretty excited for because those define `xpath` strings. This means that the source of translation data is not hardcoded. Which is a minor thing, but will be pretty useful incase the game developers decide to change the file format.

But all of this is just some ideas for the future. I don't think I'll be able to implement any time in the next few weeks. The priority now is getting the special cubes to work. Which might be a challenge

**Update** : so turns out I cannot use full `xpath` because Blender doesn't ship with the `lxml` module which is the only module that is usually shipped with Python. The only other xml parser is `xml.etree.ElementTree` but this module doesn't support fetching attributes without calling a separate method unlike the `lxml` module which allows fetching attributes from the tags with the `@` key like `//Transform/Position/@x`. So I'll be hardcoding the value paths into the Python for now. So I guess this didn't work out

> This means that the source of translation data is not hardcoded. 

```json
{
    "block_id": {
        "display_name": "Speedometer",
        "code_name": "Speedometer",
        "components": [{
            "base_source": "Speedometer",
            "obj_source": "GAME_SKIN_DIR",
            "group": "BASE",
            "offset": {
                "position": {
                    "x": 0.0,
                    "y": 0.0,
                    "z": 0.136
                },
                "rotation": {
                    "x": 90.0,
                    "y": 180.0,
                    "z": 0.0
                },
                "scale": {
                    "x": 0.3629585,
                    "y": 0.3629585,
                    "z": 0.3629585
                }
            },
            "translation_src": {
                "position": {
                    "x": "//Transform/Position/@x",
                    "y": "//Transform/Position/@y",
                    "z": "//Transform/Position/@z"
                },
                "rotation": {
                    "type": "QUARTERNION",
                    "x": "//Transform/Rotation/@x",
                    "y": "//Transform/Rotation/@y",
                    "z": "//Transform/Rotation/@z"
                },
                "scale": {
                    "x": "//Transform/Scale/@x",
                    "y": "//Transform/Scale/@y",
                    "z": "//Transform/Scale/@z"
                }
            }
        }]
    }
}
```

