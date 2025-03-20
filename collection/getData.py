# Deprecated; Replaced by laserstreamer.py

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time
from oxapi import ox

# Initialize the stream
o_x = ox("192.168.0.250")
stream = o_x.CreateStream()
stream.Start()

x_data, y_data = [], []

fig, ax = plt.subplots()
line, = ax.plot([], [], 'ro-', label='Streaming Data')
ax.set_xlim(0, 1)
ax.set_ylim(5000, 15000)
ax.set_xlabel("X Axis")
ax.set_ylabel("Y Axis")
ax.legend()

def update(frame):
    if stream.GetProfileCount() > 0:
        # time.sleep(1)
        x_data[:] = stream.ReadProfile()[-3]  # Replacing x_data
        y_data[:] = stream.ReadProfile()[-2]  # Replacing y_data
        
        line.set_data(x_data, y_data)
        ax.set_xlim(min(x_data) - 0.1, max(x_data) + 0.1)
        # ax.set_ylim(min(y_data) - 0.1, max(y_data) + 0.1)
    return line,

ani = animation.FuncAnimation(fig, update, interval=10, blit=False)
plt.show()
