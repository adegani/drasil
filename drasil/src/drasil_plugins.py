import importlib
import pkgutil
import logging

from .drasil_context import DrasilContext
from . import plugins as pns

class DrasilPlugin(object):
    # Plugins will be a list of dict
    # The list is automatically populated with all the modules in PLUGIN_DIR folder
    # Each entry of the list is a dict with two fields:
    #   - 'class' that is the pointer to the DrasilPlug() class
    #   - 'hooks' that are the keywords used for triggering the plugin
    def __init__(self):
        super(DrasilPlugin, self).__init__()

        self.plugin_list = self._parse_plugins()

    def _parse_plugins(self):
        plugin_list = []
        logging.debug('Parsing plugins')

        for _, name, _ in pkgutil.iter_modules(pns.__path__, pns.__name__ + "."):
            logging.debug('Plugin found: %s' % name)
            pluggo = importlib.import_module(name)
            Plug = pluggo.DrasilPlug()
            hooks = Plug.hooks
            my_plug = {'class': Plug, 'hooks': [h.lower() for h in hooks]}
            plugin_list.append(my_plug)
        
        return plugin_list

    def print_list(self):
        print('The following plugin are available:')
        for p in self.plugin_list:
            print(' -> %s - %s' % (p['class'].name, p['class'].description))
    
    def print_help(self, plugin_name):
        for p in self.plugin_list:
            if plugin_name.lower() == p['class'].name.lower():
                print()
                print('%s - %s' % (p['class'].name, p['class'].description))
                print('-')
                print(p['class'].help_str)
                print('-')
                print('hooks: %s' % ', '.join(p['class'].hooks))
    
    def run_hooks(self, hook, context):
        logging.debug('Running hook \"%s\"' % hook)
        for p in self.plugin_list:
            if hook in p['hooks']:
                return p['class'].run()