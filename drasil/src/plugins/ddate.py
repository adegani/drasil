from ddate.base import DDate

class DrasilPlug():
    """Render the current date using the Discordian calendar."""
    hooks = ['DDATE']
    name = 'DDate' 
    description = 'Print the current date in discordian format'
    help_str = 'The plugin has no args. When the trigger is found, prints the discordian date' 
    
    def pre(self, *argv):
        """Perform no pre-build work.

        Args:
            *argv: Lifecycle arguments supplied by the plugin dispatcher.
        """
        pass

    def run(self, *argv):
        """Return the current Discordian date without its introductory text.

        Args:
            *argv: Hook arguments supplied by the plugin dispatcher.

        Returns:
            Current date formatted by the ``ddate`` package.
        """
        return str(DDate()).replace('Today is', '')

    def post(self, *argv):
        """Perform no post-build work.

        Args:
            *argv: Lifecycle arguments supplied by the plugin dispatcher.
        """
        pass
