#Server for receiving messages from a client
import io, json, http.server, os.path, re, threading
from socketserver import ThreadingMixIn
from time import localtime, sleep, strftime, time
from urllib.parse import urlsplit


TIME_INTERVAL = 1 #in second
MISSED_MESSAGES = 20 #How many TIME_INTERVALs a client can miss before we consider them gone
PORT = 4434 #Random port we listen on

def getFile(fileName, locals = None):
  if type(locals) != dict: locals = {} #Set it to a new dict every time
  #There should only be files in the base directory, and they should be html files
  if any(char in fileName for char in ['/', '\\']) or os.path.splitext(fileName)[1] not in [".html", ".css"]:
    raise FileNotFoundError()
    
  with open(fileName) as file:
    data = file.read()
  #Now, this is like being a really shitty PHP, but here we go
  def terrible_PHP_replace(match):
    outputObj = io.StringIO()
    #Execute the code with print output being captured
    def newPrint(*arg, **kwarg):
      kwargs = {"file": outputObj, "end": "\n"}
      kwargs.update(kwarg)
      print(*arg, **kwargs)
    exec(match.group(1), {"print": newPrint, "debug": print}, locals)
    return outputObj.getvalue()
  #This will just search for instances of <?py print("Python code is here") ?> in the html and execute it
  try:
    return re.sub("<\?py\s+(.+?(?!\?>))\s+\?>", terrible_PHP_replace, data, flags = re.DOTALL)
  except Exception as e:
    print("ERROR!", e.args)
    raise RuntimeError() #Whatever error in here: It will just be considered a runtime error


class Handler(ThreadingMixIn, http.server.BaseHTTPRequestHandler):
  #Mapping of [Unique ID: dict of data about user]
  users = {}
  
  #These are users that left themselves signed in, so we don't show them any more.
  ignoredUsers = []
  
  recentHistory = []
  
  HISTORY_LENGTH = 10
  LOG_FILE = "userlog.log"
  
  dictLock = threading.Lock()
  
  #On a post request, this comes from a user reporting that it they're system is still in use
  #EXPECTED FORMAT (comma separated)
  def do_POST(self):
    print("Got update!")
    parts = self.rfile.read().decode("utf-8").split(",")
    print("Parts: ", parts)
    
    self.send_response(200)
    self.end_headers()
    
    #Add in entry (whether it already exists or not). Add in other parts as dict entries
    with Handler.dictLock:
      self.users[parts[0]] = dict(zip(["countdown", "time", "user"], [MISSED_MESSAGES] + parts[1:]))
    
      print("Users:", self.users)
  
  def do_GET(self):
    print("Starting GET Method for path '"+self.path+"'")
    url = urlsplit(self.path)
    path = "mainPage.html" if url.path == "/" else url.path.lstrip("/")

    try:
      responseText = getFile(path, locals = {"lock": Handler.dictLock, "self": self}) #Try getting the requested file, passing in a few data objects
      #Then we properly send the response
      self.send_response(200)
      self.end_headers()
      self.wfile.write(bytes(responseText, "utf-8"))
    except FileNotFoundError:
      self.send_response(404)
      self.end_headers()
      self.wfile.write(bytes("404: Page not found", "utf-8"))
    except RuntimeError: #This is if eval errors
      self.send_response(500)
      self.end_headers()
      self.wfile.write(bytes("500: Internal Server Error", "utf-8"))
    """except: #Everything else. Maybe I'll differentiate them someday
      self.send_response(500)
      self.end_headers()
      self.wfile.write(bytes("500: Internal Server Error Error", "utf-8"))"""
      
  
  @classmethod
  def onUpdate(cls):
    with Handler.dictLock:
      print("Checking all users:", cls.users)
      for user in {i:cls.users[i] for i in cls.users}:
        num = cls.users[user]["countdown"]
        if num == 0: #If missed too many messages, remove them from consideration, log data
          t = cls.users[user]
          with open(self.LOG_FILE, "a") as file: #Write their statistics to file
            tFile = {i:t[i] for i in t if i != "countdown"}
            tFile.update({"end":int(time())})
            file.write(json.dumps(tFile))
            file.write("\r\n")
          #Add in a descriptor of recent user to history table
          if len(cls.recentHistory) >= self.HISTORY_LENGTH:  
            cls.recentHistory.pop()
          cls.recentHistory.insert(0, 'User "{}" on laser for {}h {}m, signed off at {}'.format(t["user"], int(t["time"])//60**2, int(t["time"])//60%60, strftime("%I:%M %p, %x")))
          del cls.users[user]
          if user in cls.ignoredUsers:
            cls.ignoredUsers.remove(user)
        else: #If they can still miss a message
          cls.users[user]["countdown"] -= 1

STOP_SIGNAL = True
def continueUpdates():
  while STOP_SIGNAL: #Can signal this to stop
    startTime = time()
    Handler.onUpdate()   #Update all active users
    sleep(max(0, startTime - time() + TIME_INTERVAL)) #Then wait until the time interval has passed before updating again
    
  
#Start the actual server
server = http.server.HTTPServer(("", 4434), Handler)

updateThread = threading.Thread(target = continueUpdates)
updateThread.start()

try:
  server.serve_forever()
except KeyboardInterrupt:
  pass
finally:
  print("Waiting for updater thread to quit")
  STOP_SIGNAL = False
  updateThread.join() #Wait for this to finish