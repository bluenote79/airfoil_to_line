"""
This skript reads the paths from Fusion 360 and creates bat-Files on windows desktop to install pyfoil. This version installs the modules to Fusion 360 python so you have
to repeat the process when the path is changed by an update.
"""

import adsk.core, adsk.fusion, adsk.cam, traceback

import sys
import os


app = adsk.core.Application.get()
ui = None
ui  = app.userInterface

import sys


# abslolute_path = os.path.abspath("~/lib").as_posix()

def run(context):

    # get path of skript
    script_path = os.path.dirname(os.path.abspath(__file__))
    
    py_ex = os.path.abspath(str(sys.executable))

    pyfoil_install = f'{py_ex} -m pip install --upgrade pyfoil'
 
    text = "start cmd /K " + pyfoil_install

    desktop = os.path.normpath(os.path.expanduser("~/Desktop"))

    filename = os.path.join(desktop, "pyfoil.bat")

    file = open(filename, 'w')
    file.close()
    file = open(filename, "a")
    file.write(text)


   
