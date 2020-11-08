![](https://img.shields.io/badge/Code%20Quality-Crappy-orange) 

<img src="readme.assets/thumbnail_skin_update_git.png" alt="thumbnail_skin_update_git" style="zoom: 67%;" />

# Besiege Creation Import Addon for Blender

This is an addon for Blender to import Besiege Creations. Currently it works for Blender 2.90.1. I'm not sure if it works on older versions of Blender. I've had some people report issues with rotation of certain blocks on Blender 2.8, But I haven't tested it. Also blocks that come from mods will not be imported. duh.

**Note:** All models are imported from the Besiege game data directory and steam workshop folder, so its highly recommended that you get a copy of the game from Steam. 

### Usage

1. Download and install the addon
2. Once installed you'll see a new tab called Besiege in the 3D viewport toolbar (Press N). Expand the settings section and you'll find 3 fields. `Game Folder`, `Workshop Folder` and `Backup Folder`.
   - Game folder is the Skins directory that is located in the `Besiege_Data` directory. 
   - Workshop folder is the workshop content directory for Besiege.
   - Backup is the skin pack to use in case the addon failed to find a skin specified in the BSG file. By default its set to the Template skin that is packed with Besiege.
3. When importing you'll have a few options
   - **Generate Materials:** If not checked, materials will not be generated for the block. 
   - **Create Parent:** If checked, all the blocks will be parented to an empty after importing
   - **Use vanilla blocks:** If checked the addon will ignore all skin definitions from the BSG file and use the Template skin instead
   - **Stop import on missing skin**: If checked the addon will stop the import process and throw an exception if a skin could not be found. However if not checked, the addon will use the template skin instead of the missing skin (`To be removed`)
   - **Join components**: This applies to line type objects. If checked, their components will be joined into a single mesh
   - **Hide parent empties**: If checked, all empties used will be hidden
   - **Brace Threshold**: Defines the minimum distance between the start and end point of a line type before the end point and connector gets deleted (`Needs to be tuned`) Note that this applies to other line type objects
4. Select a BSG file with the field labelled `BSG File`
5. Click import
6. Hope everything imported correctly



### Things that are not working

- Surface blocks
- Short wooden poles and blocks