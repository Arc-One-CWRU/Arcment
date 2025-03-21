"""
Example functionality of working modules
"""

import os
import time

# Importing modules from the project
from processors import *
from sender import Sender
from collection import *
import threading

def demo_preprocessing(gcode_file):
    preprocessor = PreProcessor(gcode_file)
    layers = preprocessor.parse_layers()
    print(f"Total layers parsed: {len(layers)}")
    return layers

def demo_sending(layer):
    sender = Sender()
    sender.send_layer(layer)

def demo_collection_functions():
    
    # Example usage of laserstreamer 
    ls = LaserStreamer()
    def stream():
        ls.stream_until_stop()

    def stop_stream():
        time.sleep(5)  # Stream for 5 seconds
        ls.stop_stream()

    stream_thread = threading.Thread(target=stream)
    stop_thread = threading.Thread(target=stop_stream)

    stream_thread.start()
    stop_thread.start()

    stream_thread.join()
    stop_thread.join()

    ls.plot_stream()

def main():
    gcode_file = "test2.gcode"

    # Example workflow: 

    # Preprocess gcode
    layers = demo_preprocessing(gcode_file)

    # Send each layer 
    for layer in layers:
        demo_sending(layer)

    # Demo collection functions
    demo_collection_functions()

if __name__ == "__main__":
    main()
