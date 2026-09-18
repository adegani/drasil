
class DrasilContext(object):
    """Mutable rendering context supplied to plugin hooks."""

    def __init__(self, plugins=None):
        """Initialise an empty context, optionally associated with plugins.

        Args:
            plugins: Plugin dispatcher available to hooks.
        """
        self.plugins = plugins
        self.src_root = None
        self.output_dir = None
        self.current_node = None
        self.current_level = 0

        self.siblings = None
        self.ancestor_siblings = []
        self.children = []
    
        self.template = None
