from datetime import datetime

class DrasilPlug():
    """Render the current date in ISO-8601 format."""
    hooks = ['today']
    name = 'Today' 
    description = 'Print the current date YYYY-MM-DD'
    help_str = 'The plugin has no args. When the trigger is found, prints the current date' 
    
    def pre(self, *argv):
        """Perform no pre-build work.

        Args:
            *argv: Lifecycle arguments supplied by the plugin dispatcher.
        """
        pass

    def run(self, *argv):
        """Return today's date as ``YYYY-MM-DD``.

        Args:
            *argv: Hook arguments supplied by the plugin dispatcher.

        Returns:
            Current date in ISO-8601 calendar format.
        """
        return datetime.today().strftime('%Y-%m-%d')

    def post(self, *argv):
        """Perform no post-build work.

        Args:
            *argv: Lifecycle arguments supplied by the plugin dispatcher.
        """
        pass
