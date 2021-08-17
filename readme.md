![](https://img.shields.io/badge/Latest%20Compatible%20Build-2.93-green) ![](https://img.shields.io/badge/Surface%20Blocks-Stable-green) 

<img src="readme.assets/thumbnail_skin_update_git.png" alt="thumbnail_skin_update_git" style="zoom: 67%;" />

# Besiege Creation Import Addon for Blender

This is an addon for Blender to import Besiege Creations. Currently it works for Blender 2.90.1. I'm not sure if it works on older versions of Blender. I've had some people report issues with rotation of certain blocks on Blender 2.8, But I haven't tested it.

> **Note:** All models are imported from the Besiege game data directory and steam workshop folder, so its highly recommended that you get a copy of the game from Steam. 



### Installation
You can download a build from the [releases](https://github.com/arkangel-dev/BesiegeCreationImporter/releases) section, go to Blender `>` Top Bar `>` Edit `>` Add-ons `>` Install and navigate to the downloaded file. Then you can enable the addon from the Preferences window. If you want to install the addon from the current commit, you can open the files `__init__.py`, `bsgreader.py` and `blenapi.py` and set the variable `dev_mode` to False. You can find the variable at the beginning of each file. Then you can zip it all up and install

> **Note :** The latest commit may not work correctly or might not even register at all. 



### Usage

1. Download and install the addon

2. Once installed you'll see a new tab called Besiege in the 3D viewport toolbar (Press N). Expand the settings section and you'll find 3 fields. `Game Folder`, `Workshop Folder` and `Backup Folder`.
   - Game folder is the Skins directory that is located in the `Besiege_Data` directory. 
   - Workshop folder is the workshop content directory for Besiege.
   - Backup is the skin pack to use in case the addon failed to find a skin specified in the BSG file. By default its set to the Template skin that is packed with Besiege.
   - You can now click `Save Global Configuration` to save this configuration globally, as in the configuration will persist with new Blend files
   
3. When importing you'll have a few settings you can tweak. Check the [settings](#Settings) section to see what each setting does.

4. Select a BSG file with the field labelled `BSG File`.

   > **Note:**  You'll notice a label called `Block Count`. This shows how many blocks are going to be imported. Also might notice a label called `Skipped Count` with some BSG files. These come from blocks that cannot be imported. Blocks such as cameras and mod blocks.

5. Click import

   > **Note:** If you get an error message when trying to import, please check that the file paths are configured correctly and they are accessible by Blender. If you think this is not the cause of the issue, please [create a new issue](https://github.com/arkangel-dev/BesiegeCreationImporter/issues/new/choose) in the repository

6. Hope everything imported correctly



### Surface Blocks

I couldn't have implemented surface blocks without the help of [ProNou](https://github.com/Pro-Nou/). Check out his own version of the importer [here](https://github.com/Pro-Nou/BsgToOBJ). The surface block import code is not simply a one to one recreation of Pro-Nous code. The code in this repository was written from scratch to fit an object oriented style of coding. Also note that material sharing behavior is different. Surface block materials have 3 group types. Wooden type, Glass Type and Painted. Currently each painted surface will have their own material. So if you have a lot of surfaces with paint enabled, you'll have a lot materials to deal with. Glass and Wooden surfaces will have shared materials as usual. Another thing to note is that the offset for the solidifier modifier is behaving strangely. You'll have to fix this manually after importing.



## Settings

### General Settings

- **`Create Parent`** : This checkbox doesn't do anything. I didn't implement it, because I'm too lazy
- **`Merge Decor Components`** : This will merge the decoration components with the base mesh. Decoration components are stuff like the levers on the logic block etc.
- **`Notify on completion `** : If checked the addon will play a little sound upon completion if the import process took over 5 seconds
- **`Select Import`** : Pressing this button will select all imported blocks. Its useful if you have a lot of other stuff in your scene



### Skin Settings

- **`Use Vanilla Block`** : If checked the addon will import the blocks with the vanilla skins (Read from the template skin folder)
- **`Generate materials`** : If not checked the addon will generate no materials for the blocks. Shocker
- **`Use node groups for materials`** : If checked the addon will generate node groups and use said node groups in the materials of the blocks
- **`Grouping Method`** : This defines how the materials are grouped if we are using node groups. It has 3 options
  - **`Same Group`** : This will use the same node group for all materials (Except surface block materials)
  - **`By Block`** : This create a unique node group for each type of block
  - **`By Skin`** : This will create a unique node group for each skin group
- **`Purge Materials`** : This will delete all materials created by the addon. This will be useful if the addon is generating materials with outdated textures, etc.



### Line Type Blocks

- **`Delete Threshold`** : This defines the minimum length of a brace or other line type block, before its end and mid sections get deleted
- **`Join Components`** : If checked the addon will join the start, mid and end sections of the block after importing. Its useful to leave this unchecked if you want to move the points of the block after importing
- **`Cleanup Action`** : This defines how the addon will deal with the empties after importing line type blocks
  - **`Delete Empties`** : This will delete the empties
  - **`Hide the Empties`** : This will hide the empties. Not sure why I implemented this, but it eez what it eez
  - **`Do Nothing`** : This will do absolutely nothing



### Surface Blocks

- **`Resolution`** : Resolution of the surface block. I recommend you leave this at 0.1 and try not to go below 0.05 unless your rig can handle it
- **`Thickness Multiplier`** : This value will be multiplied with the thickness value read from the BSG file before being used in the solidify modifier
- **`Skip Surfaces`** : Pretty self explanatory



### Addon Settings

- **`Game Folder`** : This should be the skins folder in the games data folder. As in `Besiege_Data\Skins`
- **`Workshop Folder`** : This should be the workshop folder for Besiege. The addon will read the workshop skins from here
- **`Backup`** : This should be a skin folder. The addon will use this skin folder if it fails to find a texture or object file. By default it will be using the `Template` skin folder

