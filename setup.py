from distutils.core import setup
import py2exe
import shutil
from os import chdir
from os.path import join, exists
from sys import argv, path


#If the argument is present, returns true and removes it from the arguments list
def getArg(arg):
  if arg in argv:
    argv.remove(arg)
    return True
  return False
  
def log(*arg, **kwarg):
  return print("[BUILD]", *arg, **kwarg)
  
def debug(*arg, **kwarg):
  if DEBUG:
    return print("[DEBUG]", *arg, **kwarg)

DEBUG = getArg("--debug") #Check if we are in debug
OUTPUT_FOLDER   = "build"
INNO_SETUP_PATH = '"C:\Program Files (x86)\Inno Setup 5\Compil32.exe"'

VERSION = None
try:
  with open("version.txt") as file:
    VERSION = file.read()
except FileNotFoundError:
  pass
finally:
  VERSION = VERSION or "0.0.0"
  print("CURRENT VERSION: ", VERSION)


#All the version updating code
if not DEBUG: #If a release, we should increment the version number
  v = [int(i) for i in VERSION.split(".")]
  if len(v) != 3:
    raise RuntimeError("Version number had {} parts, 3 expected".format(len(v)))
  if getArg("--major"): #Increment major version, leave others
    v = [v[0]+1, 0, 0] 
  elif getArg("--minor"):
    v = [v[0], v[1]+1, 0]
  else:
    v[2] += 1
  newVersion = ".".join([str(i) for i in v])
  debug("NEXT VERSION:",newVersion)
  with open("version.txt", "w") as file:
    file.write(newVersion)

log("Starting build process")
#Do all the actual building
path.append("src_client") #Allows all modules in this folder to be imported
setup(**{
  "name": "Check_In_Program",
  "version": VERSION,
  "description": "Check-in Program for the GLAM Lab at S&T",
  "author": "Daniel Klinger",
  "data_files": [(".", ["C:/Windows/System32/msvcr100.dll"])], #This is to ensure Python works correctly on the target system
  "options": {"py2exe":{
    "dist_dir": OUTPUT_FOLDER,
    "compressed": (not DEBUG), #If not debug, compress the exe to make it smaller
    "includes": ["imp"], #Needed for some bull with Tkinter iirc
    #"dll_includes": ["MSVCR100.dll"],
    "excludes": ["pydoc", "doctest", "inspect"],
    "bundle_files": (3 if DEBUG else 2),
    }
  },
  ("console" if DEBUG else "windows"): [{
    "script": "src_client/client.py",
    "icon_resources": [(1, "src_client/img/icon.ico")],
    "version": VERSION + ".0" #Because windows version has 4 parts
  }]
})

#Remove this folder as it is gigantic and unneeded
#For whatever reason, having pillow includes this
if exists(join("build","tcl")):
  shutil.rmtree(join("build","tcl"))

#Now make the installer
if not DEBUG:
  from os import system
  log("Running Inno Setup File")
  system(INNO_SETUP_PATH+' /cc Build.iss')