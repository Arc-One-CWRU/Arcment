from typing import List
from collections import defaultdict
from processor_interface import Sections, ProcessorInterface

class PreProcessor():
  
  def __init__(self, gcode):
    
    with open(gcode, 'r') as f: # Opens gcode file
      self.gcode = f.readlines()
      
    self.sections = [Sections.TOP_COMMENT_SECTION,
                    Sections.STARTUP_SCRIPT_SECTION,
                    Sections.GCODE_MOVEMENTS_SECTION,
                    Sections.END_SCRIPT_SECTION,
                    Sections.BOTTOM_COMMENT]
    
    self.gcode_sections = defaultdict(list)
    self.section_processors = defaultdict(list) # Add default processors into this dict 
    self.gcode_layers = []
    
    self.parse_sections()
    
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
    """Runs the processors (Startup - End script only)
    Args:
      processors (List[ProcessorInterface], optional): _description_. If specified, will run only those processors.
                  Otherwise, will run all processors defeind in section_processors
                  Processors must be in the format of [Sections.PROCESSORTYPE[ List[Processors] ]]
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
        section_gcode = processor.process(section_gcode)
        
      processed_gcode.append(section_gcode)
      
    return processed_gcode
  
    
if __name__ == "__main__":
  a = PreProcessor("test.gcode")
  a.run_processors()
    