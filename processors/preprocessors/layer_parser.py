from processor_interface import Sections, ProcessorInterface

class LayerParser(ProcessorInterface):

  def __init__(self):
    self.layers = []
    
  def process(self, gcode: list[str]) -> list[str]:
    """Parses the gcode into layers"""
    
    current_layer = []
    
    for line in gcode:
      if Sections.CURA_LAYER in line:
        if len(current_layer) > 0:
          self.layers.append(current_layer)
          current_layer = []
      current_layer.append(line)
      
    if len(current_layer) > 0:
      self.layers.append(current_layer)
    
    return self.layers
    
  def type(self):
    return Sections.GCODE_MOVEMENTS_SECTION