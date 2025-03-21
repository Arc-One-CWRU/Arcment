import time
import threading

# Import modules - adjust paths if needed
from processors.preprocessor import PreProcessor
from processors.postprocessor import PostProcessor
from sender import Sender  # Direct import since it's in the root folder
from collection.laserstreamer import LaserStreamer

class Main:
  
    def __init__(self, gcode_file):
        """
        Initialize the WAAM system controller
        
        Args:
            gcode_file (str): Path to the G-code file to process
        """
        self.gcode_file = gcode_file
        
        print(f"Initializing with G-code file: {gcode_file}")
        
        # Initialize components
        self.preprocessor = PreProcessor(gcode_file)
        self.scanner = LaserStreamer()
        self.postprocessor = PostProcessor(scanner=self.scanner)
        self.sender = Sender()
        
        # Parse layers
        print("Parsing G-code layers...")
        self.layers = self.preprocessor.parse_layers()
        
        # Set layers in postprocessor
        self.postprocessor.set_layers(self.layers)
        
        self.current_layer = 0
        self.total_layers = len(self.layers)
        
        print(f"Initialization complete: {self.total_layers} layers parsed")
    
    def scan_layer(self):
        """
        Scan the current layer using laser scanner
        
        Returns:
            bool: True if scan was successful, False otherwise
        """
        print(f"Generating scan path for layer {self.current_layer}...")
        scan_commands = self.postprocessor.collect_laser(self.current_layer)
        
        if not scan_commands:
            print("Warning: Could not generate scan commands")
            return False
        
        # Set up threading for laser scanner
        def stream_function():
            print("Starting laser data collection...")
            self.scanner.stream_until_stop()
        
        def stop_function():
            # Calculate approximate time based on scan path complexity
            # Simple estimate - adjust based on your scan path and printer speed
            num_commands = len(scan_commands)
            scan_time = max(5, num_commands * 0.5)  # At least 5 seconds
            
            print(f"Scanner will stop in approximately {scan_time:.1f} seconds...")
            time.sleep(scan_time)
            
            print("Stopping laser scanner...")
            self.scanner.stop_stream()
        
        # Create threads
        stream_thread = threading.Thread(target=stream_function)
        stop_thread = threading.Thread(target=stop_function)
        
        # Start scanner thread
        stream_thread.start()
        
        # Brief delay to ensure scanner is initialized
        time.sleep(0.5)
        
        # Send scan path commands to printer
        print("Executing scan path...")
        self.sender.send_layer(scan_commands)
        
        # Start stop thread after commands are sent
        stop_thread.start()
        
        # Wait for both threads to complete
        stream_thread.join()
        stop_thread.join()
        
        # Process scan data
        print("Processing scan data...")
        results = self.postprocessor.process_scan_data()
        
        if results:
            print(f"Scan complete - Measured deviation: {results['deviation']:.3f}mm")
            return True
        else:
            print("Scan failed - No valid data collected")
            return False
    
    def run(self):
        """
        Process and print a single layer with adaptive control
        
        Returns:
            bool: True if all layers are complete, False otherwise
        """ 
        
        if self.current_layer >= self.total_layers:
            raise Exception("Layer index exceeds total layers")
        
        # Print current layer
        print(f"\n=== PRINTING LAYER {self.current_layer} ===")
        self.sender.send_layer(self.layers[self.current_layer])
        print(f"Layer {self.current_layer} printed.")
        
        # After printing, scan the layer (unless it's the last layer)
        scan_success = False
        if self.current_layer < self.total_layers - 1:
            print(f"\n=== SCANNING LAYER {self.current_layer} ===")
            scan_success = self.scan_layer()
        
        # Advance to next layer
        self.current_layer += 1
        
        if self.current_layer == self.total_layers:
            # If all layers are done, exit
            print("\n=== ALL LAYERS COMPLETED ===")
            return True
        else:
            # Otherwise, generate next layer and replace in queue
            if scan_success:
                print(f"\n=== GENERATING MODIFIED LAYER {self.current_layer} ===")
                # Advance postprocessor layer index to match main's
                self.postprocessor.advance_layer()
                # Generate modified next layer based on scan results
                modified_layer = self.postprocessor.gen_next_layer()
                if modified_layer:
                    self.layers[self.current_layer] = modified_layer
                    print(f"Layer {self.current_layer} modified with {len(modified_layer)} commands")
                else:
                    print(f"Using original G-code for layer {self.current_layer} (no modifications needed)")
            else:
                print(f"\n=== USING ORIGINAL LAYER {self.current_layer} ===")
                print("No scan data available for adaptive adjustment")
                # Still need to advance postprocessor's layer index
                self.postprocessor.advance_layer()
            
            return False
      
    def run_all(self):
        """
        Process all layers until complete
        """
        print(f"\n=== STARTING PRINT JOB WITH {self.total_layers} LAYERS ===")
        
        while True:
            complete = self.run()
            if complete:
                break
            
            # Pause between layers to ensure everything is ready
            time.sleep(0.5)
        
        print("Print job complete")

# Example usage
if __name__ == "__main__":
    main = Main("test.gcode")
    main.run_all()