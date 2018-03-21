#Server for receiving messages from a client
import http.server, threading
from socketserver import ThreadingMixIn
from time import sleep


TIME_INTERVAL = 1 #1 second
MISSED_MESSAGES = 20 #How many TIME_INTERVALs a client can miss before we consider them gone
PORT = 4434 #Random port we listen on

class Handler(ThreadingMixIn, http.server.BaseHTTPRequestHandler):
  #Mapping of [Unique ID: dict of data about user]
  users = {}
  
  #These are users that left themselves signed in, so we don't show them any more.
  ignoredUsers = []
  
  dictLock = threading.Lock()
  
  #On a post request, this comes from a user reporting that it they're system is still in use
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
          self.wfile.write(bytes(t["user"] + ": {} hours, {} minutes<br>".format(int(t["time"])//60**2, int(t["time"])//60), "utf-8"))
      print("Done")
  
  def onUpdate(self):
    with Handler.dictLock:
      print("Checking all users:", self.users)
      for user in {i:self.users[i] for i in self.users}:
        num = self.users[user]["countdown"]
        if num == 0: #If missed too many messages, remove them from consideration
          del self.users[user]
          if user in self.ignoredUsers:
            self.ignoredUsers.remove(user)
        else: #If they can still miss a message
          self.users[user]["countdown"] -= 1

STOP_SIGNAL = True
def continueUpdates():
  while STOP_SIGNAL: #Can signal this to stop
    Handler.onUpdate(Handler)
    sleep(TIME_INTERVAL)
    
  
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