from abc import abstractmethod

"""Copied from cura.py and sections.py, gcode-parser"""
class Sections:
  TOP_COMMENT_SECTION = "TOP_COMMENT"
  STOP_COMMENT_SECTION = "TOP_COMMENT"
  STARTUP_SCRIPT_SECTION = "STARTUP_SCRIPT"
  GCODE_MOVEMENTS_SECTION = "GCODE_MOVEMENTS"
  END_SCRIPT_SECTION = "END_SCRIPT"
  BOTTOM_COMMENT = "BOTTOM_COMMENT"
  
  CURA_LAYER = ";LAYER:"
  CURA_MESH_LAYER = ";MESH"
  CURA_OUTER_WALL = ";TYPE:WALL-OUTER"
  CURA_TYPE_LAYER = ";TYPE"

  END_OF_HEADER_SETTINGS_MARLIN = ";MAXZ:"
  END_OF_HEADER_SETTINGS_GRIFFIN = ";END_OF_HEADER"

  END_OF_TOP_METADATA = ";Generated with Cura"
  END_OF_STARTUP_SCRIPT = ";LAYER_COUNT:"
  END_OF_GCODE_MOVEMENTS = ";TIME_ELAPSED"
  END_OF_GCODE = ";End of Gcode"
  
class ProcessorInterface:

  @abstractmethod
  def process(self, gcode: str) -> str:
    """Processor should take in gcode and and return processed gcode"""
    raise NotImplementedError
    
  @abstractmethod
  def process_type(self):
    """Return processor type"""
    raise NotImplementedError