from typing import List
from collections import defaultdict
from .preprocessors import *

class PreProcessor():
  
  def __init__(self, gcode):
    
    self.gcode = []
    
    with open(gcode, 'r', encoding='utf-8', errors='replace') as f:
      for line in f:
        self.gcode.append(line.strip())
      
    self.sections = [Sections.TOP_COMMENT_SECTION,
                    Sections.STARTUP_SCRIPT_SECTION,
                    Sections.GCODE_MOVEMENTS_SECTION,
                    Sections.END_SCRIPT_SECTION,
                    Sections.BOTTOM_COMMENT]
    
    self.gcode_sections = defaultdict(list)
    self.section_processors = [] # Add default processors into this list
    self.gcode_layers = []
    
    self.parse_sections()
    # print(self.parse_layers()[1])
    
  def parse_sections(self):
    """Parses the gcode into the different sections"""
    
    current_index = 0
    current_section_index = 0
    
    while current_index < len(self.gcode):
      line = self.gcode[current_index]
      self.gcode_sections[self.sections[current_section_index]].append(line)
      
      if line.strip() in [";top metadata end", 
                          ";startup script end", 
                          ";gcode movements end", 
                          ";end script end"] :
        current_section_index += 1
        current_index += 1
        continue
      elif line.strip() == ";bottom comment end": 
        break
  
      current_index += 1
    
  def run_processors(self, processors: List[ProcessorInterface] = None):
    """Runs the processors (Startup - End script only) excluding layer parser
    Args:
      processors (List[ProcessorInterface], optional): _description_. If specified, will run only those processors.
                  Otherwise, will run all processors defeind in section_processors
    """
    
    # Run processors in order
    # Order: STARTUP_SCRIPT, GCODE_MOVEMENTS, END_SCRIPT
    
    if processors == None:
      processors = self.section_processors
      
    processed_gcode = []
    
    # Iterates through the thre sections 
    for section in self.sections[1:-1]:
      section_gcode = self.gcode_sections[section]
      
      # Processes the section using the processors 
      for processor in processors:
        if processor.type == section:
          section_gcode = processor.process(section_gcode)
        
      processed_gcode.append(section_gcode)
      
    return processed_gcode
  
  def parse_layers(self):
    parser = LayerParser()
    layers = parser.process(self.gcode_sections[Sections.GCODE_MOVEMENTS_SECTION])
    return layers
