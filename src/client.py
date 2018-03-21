#GLAM Check In Client program
#Basically, while this is running, it just sends a POST request to the web server once every second.
#The rationale behind doing this and not just using websockets is:
# 1: This is easy. 2: There should only be 1 user at a time ever, so managing connections isn't important
# 3: This should be robust. If the websocket fails I don't want to worry about reconnecting and managing that

import tkinter as tk
from http.client import HTTPConnection
from os import getlogin
from os.path import join
from random import getrandbits
from time import time
from PIL import ImageTk, Image

IP_ADDRESS = "64.251.147.89:4434" #Home IP address at random port
#IP_ADDRESS = "192.168.0.10:4434" #Home IP address at random port

class MainWindow(tk.Tk):
  id = hex(getrandbits(64))[2:] #Generate a new random ID when the program is started
  startTime = time() #Record when program is started
  user = getlogin()
  
  active = True
  updatesSent = 0
  
  def __init__(self):
    super().__init__()
    self.title("AMOG Check-In System")
    self.resizable(False, False)
    self.iconbitmap(join("img","icon.ico"))
    
    self.labels = {}
    self.labels["user"] = tk.Label(text = "Current User: " + self.user)
    self.labels["messages"] = tk.Label(text = "Messages sent: " + str(self.updatesSent))
    self.labels["time"] = tk.Label(text = "Time Logged In: " + "{} hours, {} minutes".format(*divmod(int(time()-self.startTime), 60*60)))
    
    #Add in all the labels
    for label in self.labels:
      self.labels[label].config(anchor = "w")
      self.labels[label].pack(fill = "both", expand = "yes")
    
    
    self.imageLabel = tk.Label(self)
    self.imageLabel.pack(fill = "both", expand = "yes")
    self.setImage("active.png")
    
  
  def sendUpdate(self):
    try:
      conn = HTTPConnection(IP_ADDRESS, timeout = 0.5)
      #We'll send CSV of ID, and time logged as integer
      conn.request("POST", "", body=",".join([self.id, str(int(time()-self.startTime)), self.user]))
      conn.close()
      
      self.updatesSent += 1
      self.labels["messages"].config(text = "Messages sent: " + str(self.updatesSent))
    except OSError as e: #Catch socket failed to connect
      self.labels["messages"].config(text = "Messages sent: " + str(self.updatesSent) + " | Last Send Failed")
    
    
    currTime = int(time() - self.startTime)
    self.labels["time"].config(text = "Time Spent Logged In: " + "{} hours, {} minutes".format(currTime//60**2, currTime//60))
    
    self.after(1000, self.sendUpdate)
    
  def setImage(self, fileName):
    image = Image.open(join("img",fileName))
    self.image = ImageTk.PhotoImage(image.resize((200,200), Image.HAMMING)) #Have to store this locally or it is garbage collected
    self.imageLabel.config(image = self.image)

    
#The main program
root = MainWindow()
root.sendUpdate() #Start sending updates
root.mainloop()