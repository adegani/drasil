
class DrasilContext(object):
    def __init__(self, plugins=None):
        self.plugins = plugins
        self.src_root = None
        self.output_dir = None
        self.current_node = None
        self.current_level = 0

        self.brothers = None
        self.uncles = []
        self.childs = []
    
        self.template = None