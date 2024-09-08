# Airfoil to line

## This skript adds an airfoil to Fusion 360 from dat-file fitting to selected sketchlines.

<picture>

  <img alt="Illustrates usage of airfoil to line script" src="https://github.com/bluenote79/airfoil_to_line/blob/main/pics/demo.gif">

</picture>

Everyone using Fusion 360 probably knows this error message: *“The selected rail dos not touch all of the profiles.”*
To avoid this when lofting airfoils I am working on this tool to import airfoils to Fusion 360 in a way that they are placed exactly where I want them to be.
Two construction lines are necessary for that to work, one that will go from the nose to the tail or the point right between the endpoints if the airfoil is not closed. The second lines starting point must be coincident to the first lines starting point and the lines. The lines must have perpendicular constraints. The coincidence shows the script where to put the nose, the second line directs towards the upper side of the airfoil.

The size of the gab at the tail can also be modified by the script, so you can get a constant size if you want to.
Also you can decide to generate new points by cubic iteration. Here the tool uses [**pyfoil**](https://github.com/airgproducts/pyfoil) by [**airgproducts**](https://github.com/airgproducts)
I tried to do cubic iteration with standard python library only bit didn’t get satisfying results. So I would be glad if somebody could help with that. Also I only got it to run on Windows but not on Mac.
The problem with external libraries is that Fusion 360 changes the python path with every update so there are two possible ways to handle it:
You can either reinstall the requirements each time an update comes up or use relative paths to a different folder with the modules. Unfortunately this doesn’t work with numpy so the directory must be inserted of appended to path.

To set it up I wrote another script that provides the paths and writhes them to bat-files on the desktop. In some cases you can install using the text commands in Fusion but in some cases Fusion then restarts an it doesn’t work.

### Here are the steps to get it run:
1. In Fusion 360 go to Utilities > ADD-INS > Skripts and Add-Ins.
2. Create a new script (chose Script, Python and airfoil_to_line as Script Name
3. Right click on the script > Open file location
4. Rename the “make_bat_for_module_install_to_subfolder.py” to “airfoil_to_line.py” an insert it in the script folder.
5. Run the script to get the bat-file. It includes:
start cmd /K <path to Fusions python>\python -m pip install --target <path to lib folder in scriptfolder> --upgrade pyfoil
6. Shut down Fusion 360.
7. Check the code in the bat file. Sometimes it happens that it gets the path to fusion360.exe. In that case you have to susbstitute fusion360.exe by Python\python
8. Run the bat file
9. Run Fusion an overwrite the script with the aiforil_to_line.py script.
