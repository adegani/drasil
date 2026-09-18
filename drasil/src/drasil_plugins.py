import importlib
import pkgutil
import logging

from .drasil_context import DrasilContext
from . import plugins as pl


class DrasilPlugin(object):
    """Discover installed plugins and dispatch their lifecycle hooks."""
    # Plugins will be a list of dict
    # The list is automatically populated with all the modules in PLUGIN_DIR
    # folder. Each entry of the list is a dict with two fields:
    #   - 'class' that is the pointer to the DrasilPlug() class
    #   - 'hooks' that are the keywords used for triggering the plugin
    def __init__(self):
        """Load plugin metadata from the bundled plugin package."""
        super(DrasilPlugin, self).__init__()

        self.plugin_list = self._parse_plugins()

    def _parse_plugins(self):
        """Import each plugin module and collect its hook declarations.

        Returns:
            Plugin metadata dictionaries containing a plugin instance and hooks.
        """
        plugin_list = []
        logging.debug('Parsing plugins')

        for _, name, _ in pkgutil.iter_modules(pl.__path__, pl.__name__ + "."):
            logging.debug('Plugin found: %s' % name)
            plugin_module = importlib.import_module(name)
            plugin = plugin_module.DrasilPlug()
            hooks = plugin.hooks
            plugin_metadata = {'class': plugin, 'hooks': [hook.lower() for hook in hooks]}
            plugin_list.append(plugin_metadata)

        return plugin_list

    def print_list(self):
        """Print the name and description of every discovered plugin."""
        print('The following plugin are available:')
        for plugin_metadata in self.plugin_list:
            plugin = plugin_metadata['class']
            print(' -> %s - %s' % (plugin.name, plugin.description))

    def print_help(self, plugin_name):
        """Print usage information for a plugin matching ``plugin_name``.

        Args:
            plugin_name: Case-insensitive name of the requested plugin.
        """
        for plugin_metadata in self.plugin_list:
            plugin = plugin_metadata['class']
            if plugin_name.lower() == plugin.name.lower():
                print()
                print('%s - %s' % (plugin.name, plugin.description))
                print('-')
                print(plugin.help_str)
                print('-')
                print('hooks: %s' % ', '.join(plugin.hooks))

    def run_hooks(self, hook, context, template_empty):
        """Run the plugin registered for ``hook`` and return its replacement.

        Args:
            hook: Hook expression, optionally followed by colon-separated arguments.
            context: Rendering context made available to the plugin.
            template_empty: Template without page body, used by plugins that
                generate pages after the build.

        Returns:
            The replacement produced by the matching plugin, or ``None`` when
            no plugin handles the hook.
        """
        hook_name, *hook_args = hook.split(':')
        for plugin_metadata in self.plugin_list:
            if hook_name in plugin_metadata['hooks']:
                logging.debug('Running hook \"%s\" with args: %s' %
                              (hook_name, hook_args))
                return plugin_metadata['class'].run(hook_args, context, template_empty)

    def run_post(self):
        """Run post-build processing for every discovered plugin."""
        for plugin_metadata in self.plugin_list:
            logging.debug('Running post of \"%s\"', plugin_metadata)
            plugin_metadata['class'].post()

    def run_pre(self):
        """Run pre-build processing for every discovered plugin."""
        for plugin_metadata in self.plugin_list:
            logging.debug('Running pre of \"%s\"', plugin_metadata)
            plugin_metadata['class'].pre()
