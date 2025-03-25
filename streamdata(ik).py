import sys
sys.path.append(r"C:/Program Files/Baumer/API")
import time
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from .oxapi import ox

class LaserStreamer:
  
  def __init__(self, ip="192.168.0.250"):
    self.ip = ip
    self.o_x = ox(self.ip)
    self.stream = self.o_x.CreateStream()
    self.data = []
    self.stop_flag = False
    self.last_profile = None
    self.height_history = []  # Added height_history attribute
    
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
    self.start_stream()
    self.height_history = []  # Clear previous height data
    
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
        
        # Calculate average height from valid z values
        if len(z_vals) > 0:
            valid_z = [z for z in z_vals if 0.1 < z < 100]
            if valid_z:
                avg_height = sum(valid_z) / len(valid_z)
                self.height_history.append(avg_height)
                print(f"Profile height: {avg_height:.3f}mm")
        
        self.last_profile = profile
        time.sleep(0.1)
      else:
        time.sleep(0.01) # Skip if no profile
    
    # Add mock data for demo if no real data was collected
    if not self.height_history:
        print("No height data collected. Adding mock data for demo.")
        self.height_history = [0.25] * 10  