#Server for receiving messages from a client
import json, http.server, threading
from socketserver import ThreadingMixIn
from time import localtime, sleep, strftime, time


TIME_INTERVAL = 1 #in second
MISSED_MESSAGES = 20 #How many TIME_INTERVALs a client can miss before we consider them gone
PORT = 4434 #Random port we listen on
LOG_FILE = "userlog.log"
HISTORY_LENGTH = 10

class Handler(ThreadingMixIn, http.server.BaseHTTPRequestHandler):
  #Mapping of [Unique ID: dict of data about user]
  users = {}
  
  #These are users that left themselves signed in, so we don't show them any more.
  ignoredUsers = []
  
  recentHistory = []
  
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
    if self.path == "/":
      print("Starting GET Method")
      self.send_response(200)
      self.end_headers()
      self.wfile.write(bytes("<html>People on Laser:<br>", "utf-8"))
      print("Starting writing")
      with Handler.dictLock:
        for user in self.users:
          print("Writing user:",user)
          t = self.users[user]
          self.wfile.write(bytes(t["user"] + ": {} hours, {} minutes, started at {}<br>".format(int(t["time"])//60**2, int(t["time"])//60%60, strftime("%I:%M %p, %x", localtime(time() - int(t["time"])))), "utf-8"))
        self.wfile.write(bytes("<br>Recent Users List:<br>", "utf-8"))
        for i in range(len(self.recentHistory)):
          self.wfile.write(bytes("{}: {}<br>".format(i+1, self.recentHistory[i]), "utf-8"))
        
      print("Done")
  
  @classmethod
  def onUpdate(cls):
    with Handler.dictLock:
      print("Checking all users:", cls.users)
      for user in {i:cls.users[i] for i in cls.users}:
        num = cls.users[user]["countdown"]
        if num == 0: #If missed too many messages, remove them from consideration, log data
          t = cls.users[user]
          with open(LOG_FILE, "a") as file: #Write their statistics to file
            tFile = {i:t[i] for i in t if i != "countdown"}
            tFile.update({"end":int(time())})
            file.write(json.dumps(tFile))
            file.write("\r\n")
          #Add in a descriptor of recent user to history table
          if len(cls.recentHistory) > 10:  
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
  print("Waiting for updater thread to quit")
  STOP_SIGNAL = False
  updateThread.join() #Wait for this to finish