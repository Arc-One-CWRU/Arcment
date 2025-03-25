from .postprocessors import *
from collections import defaultdict
import numpy as np

class PostProcessor:
    """
    PostProcessor for the Arcment WAAM system.
    Processes laser scan data and modifies G-code for adaptive layer control.
    """
    
    def __init__(self, scanner=None):
        """
        Initialize the PostProcessor
        
        Args:
            scanner: Optional reference to WeldScanner instance
        """
        # Core component references
        self.scanner = scanner
        self.layer_index = 0
        self.layers = []
        
        # Data storage for processing results
        self.scan_data = defaultdict(dict)
        self.height_deviations = {}
        
        # Configuration
        self.z_safety_offset = 5.0  # Safety distance for movement
        self.scan_speed = 500       # Speed for scan movements (mm/min)
        self.filter_outliers = True  # Whether to filter measurement outliers
        
        print("PostProcessor initialized")
    
    def set_layers(self, layers):
        """Set the G-code layers to be processed"""
        self.layers = layers
        print(f"Loaded {len(layers)} layers for processing")
        
    def collect_laser(self, layer_index=None):
        """
        Generate scanning path for the specified layer
        
        Args:
            layer_index: Index of layer to scan (defaults to current layer)
            
        Returns:
            list: G-code commands for scanning path
        """
        if layer_index is None:
            layer_index = self.layer_index
            
        if layer_index >= len(self.layers):
            print(f"Error: Layer index {layer_index} out of range")
            return None
            
        layer = self.layers[layer_index]
        
        # Extract bounding box coordinates from the layer
        min_x, max_x, min_y, max_y, z = self._extract_bounding_box(layer)
        
        if min_x is None or z is None:
            print("Warning: Could not extract geometry from layer")
            return []
            
        # Create scan path - simple rectangular path over the bounding box
        scan_commands = [
            f"; Scan path for layer {layer_index}",
            f"G0 F1000 Z{z + self.z_safety_offset}",  # Move up for safety
            f"G0 X{min_x - 2} Y{min_y - 2}",  # Move to start corner with margin
            f"G0 Z{z + 2}",  # Move down to scanning height
            f"G1 X{max_x + 2} Y{min_y - 2} F{self.scan_speed}",  # Scan first edge
            f"G1 X{max_x + 2} Y{max_y + 2}",  # Scan second edge
            f"G1 X{min_x - 2} Y{max_y + 2}",  # Scan third edge
            f"G1 X{min_x - 2} Y{min_y - 2}",  # Complete the rectangle
            f"G0 Z{z + self.z_safety_offset}"  # Move up for safety
        ]
        
        return scan_commands
    
    def process_scan_data(self):
        """
        Process scan data from the scanner and calculate height deviation
        
        Returns:
            dict: Scan results including deviation information
        """
        if not self.scanner or not hasattr(self.scanner, 'height_history'):
            print("Warning: Scanner not available or no height data")
            return None
            
        # Get raw height data
        height_data = self.scanner.height_history.copy() if self.scanner.height_history else []
        
        if not height_data:
            print("No height data available from scanner")
            return None
            
        # Apply filtering if enabled and sufficient data points
        if self.filter_outliers and len(height_data) > 3:
            filtered_data = self._filter_outliers(height_data)
        else:
            filtered_data = height_data
            
        if not filtered_data:
            print("No valid data points after filtering")
            return None
            
        # Extract expected Z height from the layer
        expected_z = self._extract_z_height(self.layers[self.layer_index])
        
        # Calculate statistics
        max_height = max(filtered_data)
        min_height = min(filtered_data)
        avg_height = sum(filtered_data) / len(filtered_data)
        
        # Store results
        scan_results = {
            'layer_index': self.layer_index,
            'expected_z': expected_z,
            'max_height': max_height,
            'min_height': min_height,
            'avg_height': avg_height,
            'num_points': len(filtered_data),
            'num_raw_points': len(height_data)
        }
        
        # Calculate deviation (positive means layer is higher than expected)
        deviation = avg_height - expected_z
        scan_results['deviation'] = deviation
        
        # Store in internal data structures
        self.scan_data[self.layer_index] = scan_results
        self.height_deviations[self.layer_index] = deviation
        
        print(f"Layer {self.layer_index} scan: " + 
              f"avg_height={avg_height:.3f}mm, " + 
              f"expected={expected_z:.3f}mm, " + 
              f"deviation={deviation:.3f}mm")
        
        return scan_results
        
    def gen_next_layer(self):
        """
        Generate the modified G-code for the next layer based on scan results
        
        Returns:
            list: Modified G-code lines for the next layer
        """
        # Check if we have a next layer
        next_layer_index = self.layer_index + 1
        if next_layer_index >= len(self.layers):
            print("No more layers to generate")
            return None
            
        # Get the next layer
        next_layer = self.layers[next_layer_index]
        
        # If no height deviation data available, return original layer
        if self.layer_index not in self.height_deviations:
            print(f"No height deviation data for layer {self.layer_index}")
            return next_layer
            
        # Get the measured deviation
        deviation = self.height_deviations[self.layer_index]
        
        # Too small to correct? (less than 0.01mm)
        if abs(deviation) < 0.01:
            print("Deviation too small for correction")
            return next_layer
            
        # Apply Z correction to next layer
        modified_layer = []
        adjustment_count = 0
        
        for line in next_layer:
            if line.startswith(('G0', 'G1')) and 'Z' in line:
                try:
                    # Extract Z value
                    parts = line.split('Z')
                    prefix = parts[0] + 'Z'
                    
                    # Split remaining parts to get Z value
                    z_parts = parts[1].split(' ', 1)
                    z_value = float(z_parts[0])
                    
                    # Adjust Z by subtracting the deviation
                    # (If layer was too high, deviation is positive, so we lower the next layer)
                    adjusted_z = z_value - deviation
                    adjusted_z = max(0.05, adjusted_z)  # Ensure Z is never too small
                    
                    # Reconstruct the G-code line
                    if len(z_parts) > 1 and z_parts[1]:
                        modified_line = f"{prefix}{adjusted_z:.3f} {z_parts[1]}"
                    else:
                        modified_line = f"{prefix}{adjusted_z:.3f}"
                        
                    modified_layer.append(modified_line)
                    adjustment_count += 1
                    
                except (ValueError, IndexError):
                    # Keep original line if parsing fails
                    modified_layer.append(line)
            else:
                # Keep original line for non-Z commands
                modified_layer.append(line)
                
        print(f"Modified layer {next_layer_index} with {adjustment_count} Z-height " +
              f"adjustments (deviation: {deviation:.3f}mm)")
              
        return modified_layer
        
    def advance_layer(self):
        """
        Advance to the next layer and return the new layer index
        
        Returns:
            int: New layer index
        """
        self.layer_index += 1
        return self.layer_index
        
    def _filter_outliers(self, data, threshold=2.0):
        """
        Filter outliers from height data
        
        Args:
            data: List of height measurements
            threshold: Standard deviation threshold for outlier detection
            
        Returns:
            list: Filtered height data
        """
        if not data:
            return []
            
        # Calculate mean and standard deviation
        mean = sum(data) / len(data)
        std_dev = (sum((x - mean) ** 2 for x in data) / len(data)) ** 0.5
        
        # Filter out values more than threshold standard deviations from mean
        filtered = [x for x in data if abs(x - mean) <= threshold * std_dev]
        
        # Report how many points were filtered
        filtered_count = len(data) - len(filtered)
        if filtered_count > 0:
            print(f"Filtered {filtered_count} outlier points from scan data")
            
        return filtered
        
    def _extract_z_height(self, layer):
        """
        Extract the Z height from a layer's G-code
        
        Args:
            layer: List of G-code lines
            
        Returns:
            float: Extracted Z height or 0.0 if not found
        """
        for line in layer:
            if line.startswith(('G0', 'G1')) and 'Z' in line:
                try:
                    z_value = float(line.split('Z')[1].split(' ')[0])
                    return z_value
                except (ValueError, IndexError):
                    continue
                    
        print("Could not find Z height in layer")
        return 0.0
        
    def _extract_bounding_box(self, layer):
        """
        Extract the bounding box of a layer
        
        Args:
            layer: List of G-code lines
            
        Returns:
            tuple: (min_x, max_x, min_y, max_y, z) or default values if not found
        """
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        z = None
        
        for line in layer:
            if not (line.startswith('G0') or line.startswith('G1')):
                continue
                
            # Extract X coordinate
            if 'X' in line:
                try:
                    x = float(line.split('X')[1].split(' ')[0].split(';')[0])
                    min_x = min(min_x, x)
                    max_x = max(max_x, x)
                except (ValueError, IndexError):
                    pass
                    
            # Extract Y coordinate
            if 'Y' in line:
                try:
                    y = float(line.split('Y')[1].split(' ')[0].split(';')[0])
                    min_y = min(min_y, y)
                    max_y = max(max_y, y)
                except (ValueError, IndexError):
                    pass
                    
            # Extract Z coordinate (first occurrence)
            if 'Z' in line and z is None:
                try:
                    z = float(line.split('Z')[1].split(' ')[0].split(';')[0])
                except (ValueError, IndexError):
                    pass
                    
        # Use reasonable defaults if bounds couldn't be extracted
        if min_x == float('inf') or min_y == float('inf'):
            print("Warning: Using default bounding box due to parsing issues")
            min_x, max_x = 0, 200
            min_y, max_y = 0, 200
        
        # Use default Z if not found
        if z is None:
            print("Warning: No Z height found in layer, using default")
            z = 0.2 * (self.layer_index + 1)  # Default layer height
        
        return min_x, max_x, min_y, max_y, z