#NOTE: Stolen and adapted from Tooyunes

#This file deals with updating the installation
import json, os, subprocess
from io import BytesIO
from shutil import copyfileobj
from urllib.error import URLError
from urllib.request import Request, urlopen
from zipfile import ZipFile
join = os.path.join #Alias for time saving

from log import log
from msgBox import errorBox, questionBox, FileDLProgressBar

#CONSTANTS
UPDATE_LINK = "https://api.github.com/repos/civilwargeeky/Tooyunes/releases/latest"
FFMPEG_LINK = "http://ffmpeg.zeranoe.com/builds/win64/static/ffmpeg-3.3.2-win64-static.zip"
YT_DL_LINK  = "https://yt-dl.org/downloads/latest/youtube-dl.exe"

UPDATE_FILE = "Updater.exe"

#Checks if this is a first-time installation (we need to install ffmpeg, ffprobe, and youtube-dl)
#Returns true if the installation is up to date, false otherwise
def checkInstall():
  if not os.path.isdir("resources"):
    os.mkdir("resources")
  
  progress = FileDLProgressBar("Performing first-time installation. Please wait")
  try:
  
    #Do youtube check ahead of time in order to make good indicator box
    ytNeeded = not os.path.exists(join("resources", "youtube-dl.exe"))
    if ytNeeded:
      progress.add("Downloading youtube-dl.exe", "Done!")
    
    fileList = ["ffmpeg.exe", "ffprobe.exe"]
    for file in fileList:
      if not os.path.exists(join("resources",file)):
        progress.addStart("Downloading ffmpeg .zip file (this one can take a while)", *["Writing " + i for i in fileList])
        progress.start()
        log.warning("Resources file:", file,"does not exist, downloading")
        #Well great, now we have to download and parse the zip file
        zipURL = Request(FFMPEG_LINK,
          headers = {"User-Agent": "Python Agent"} #Apparently the agent just has to exist
          )
        with urlopen(zipURL) as response:
          log.debug("Writing response to Bytes")
          dlZip = ZipFile(BytesIO(response.read()))
          log.debug("File downloaded")
        for descriptor in dlZip.namelist():
          file = os.path.basename(descriptor)
          if file in fileList:
            progress.next() #Go to the next progress bar action
            log.debug("Found file:", descriptor)
            fileList.pop(fileList.index(file))
            with dlZip.open(descriptor) as source, open(join("resources", file), "wb") as dest:
              copyfileobj(source, dest)
            log.debug("File write successful")
        break
    if ytNeeded:
      progress.start()
      log.warning("Resources file: youtube-dl.exe does not exist, downloading")
      with urlopen(YT_DL_LINK) as source, open(join("resources", "youtube-dl.exe"), "wb") as dest:
        copyfileobj(source, dest)
      log.debug("Write Success")
      progress.next() #Say "Done!"
  except URLError:
    log.warning("Not connected to the internet")
    errorBox("Not connected to the internet!", title="Fatal Error")
    raise RuntimeError("No internet")
  finally: #Close the window regardless
    progress.close()
  return True #If rest of program succeeded in updating

#Downloads a new program installer if the github version is different than ours
#Returns true on successful update (installer should be running), false otherwise
#If there is no internet, raises a RuntimeError stating so
def updateProgram():
  try:
    if os.path.exists(UPDATE_FILE):
      os.remove(UPDATE_FILE)
  except PermissionError:
    log.error("Cannot remove installer exe, must be open still")
    return False
  
  try: #Get our version so we see if we need to update
    with open("version.txt") as file:
      versionCurrent = file.read()
      log.debug("Current Version:", versionCurrent)
  except:
    versionCurrent = None
    log.warning("Version file not found")
    
  try:
    log.info("Beginning update check")
    with urlopen(UPDATE_LINK) as response:
      updateData = json.loads(response.read().decode("utf-8"))
      newVersion = updateData["tag_name"]
      log.debug("Good data received")
      log.debug("Most Recent:", newVersion,"| Our Version:", versionCurrent)
      if newVersion != versionCurrent: #The tag should be the released version
        if questionBox("Version "+newVersion+" now available! Would you like to update?", title="Update"):
          try: #After this point, we want another exception handler that will stop the program with error, because the user expects a download to be happening
            log.info("Updating to version", newVersion)
            fileData = updateData["assets"][0]
            webAddress = fileData["browser_download_url"]
            #                                used to be 'fileData["name"]'
            with urlopen(webAddress) as webfile, open(UPDATE_FILE, "wb") as file:
              progress = FileDLProgressBar("Downloading new update")
              progress.start()
              log.debug("Downloading new file from", webAddress)
              #Both file and webfile are automatically buffered, so this is fine to do
              copyfileobj(webfile, file)
              progress.close()
            subprocess.Popen(UPDATE_FILE) #Call this file and then exit the program
          except IndexError: #No binary attached to release -- no assets (probably)
            #In future we might check updates before this one, to ensure we are somewhat updated
            log.error("No binary attached to most recent release!")
          except BaseException as e: #BaseException because return statement in finally stops anything from getting out
            log.error("Error in downloading new update!", exc_info = e)
          finally:
            return True #Notice: This stops any error propagation for other errors
        else:
         log.info("User declined update")
         
      else:
        log.info("We have the most recent version")
  except URLError:
    log.warning("Not connected to the internet!")
    errorBox("Not connected to the internet!", title="Fatal Error")
    raise RuntimeError("No internet")
  except Exception as e:
    #Log the error. We still want them to run the program if update was not successful
    log.error("Error in update!", exc_info = e) 
  #If we did not return in the function, we did not update properly
  return False