import time
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from oxapi import ox

class LaserStreamer:
  
  def __init__(self, ip="192.168.0.250"):
    self.ip = ip
    self.o_x = ox(self.ip)
    self.stream = self.o_x.CreateStream()
    self.data = []
    self.stop_flag = False
    self.last_profile = None
    
  def start_stream(self):
    """Starts the stream"""
    self.stop_flag = False
    self.stream.Start()
    print("Stream started.")
    
  def stop_stream(self):
    """Stops the stream"""
    self.stop_flag = True
    self.stream.Stop()
    print("Stream stopped.")
    
  def stream_until_stop(self):
    """
    Streams data until stop signal is received 
    Reads from profile queue and stores x and z values with timestamps
    Returns:
      List[Dict]: List of dictionaries containing x, z, and timestamp values
    """
    
    print("Streaming data...")  
    while not self.stop_flag:
      if self.stream.GetProfileCount() > 0:
        profile = self.stream.ReadProfile()
        x_vals = profile[-3]
        z_vals = profile[-2]
        timestamp = profile[6]
        
        self.data.append({
          "x": x_vals,
          "z": z_vals,
          "timestamp": timestamp
        })
        
        self.last_profile = profile
      else:
        time.sleep(0.01) # Skip if no profile
    
    return self.data
  
  def current_profile(self):
    """Returns the last profile in queue"""
    if self.stream.GetProfileCount() > 0:
      profile = self.stream.ReadProfile()
      self.last_profile = profile
      return profile
    else:
      return self.last_profile
    
  def plot_stream(self):
    """Plots streamed data from self.data"""
    if not self.data:
      print("No data")
      return
    
    xs, zs, ts = [], [], []
    
    for profile in self.data:
      for x_val, z_val in zip(profile["x"], profile["z"]):
        xs.append(x_val)
        zs.append(z_val)
        ts.append(profile["timestamp"])
        
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(xs, ts, zs)
    ax.set_xlabel('X')
    ax.set_ylabel('Time')
    ax.set_zlabel('Z')
    plt.show()
    
  def clear_data(self):
    """Clears the data"""
    self.data = []
    print("Data cleared.")
    
  def get_last_scan(self):
    """Returns the last scan"""
    return self.last_profile
    
def stop_signal(laser_streamer, stop_time=5):
  """Sends stop signal to end stream data"""
  
  time.sleep(stop_time)
  laser_streamer.stop_stream()