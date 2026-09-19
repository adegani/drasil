import subprocess as subprocess


class DrasilPlug():
    """Render the current Git tag of the source repository."""
    hooks = ['gittag']
    name = 'GIT_tag'
    description = 'Print the current tag fpr the website repository'
    help_str = 'The plugin has no args. When the trigger is found,'
    help_str += 'it retrieve the current tag of the git repository of the'
    help_str += 'src website. If the website is not a git repo, it fails.'

    def pre(self, *argv):
        """Perform no pre-build work.

        Args:
            *argv: Lifecycle arguments supplied by the plugin dispatcher.
        """
        pass

    def run(self, *argv):
        """Return ``git describe --tags`` output or a fallback error message.

        Args:
            *argv: Dispatcher arguments; the rendering context is at index one.

        Returns:
            Current Git tag or an explanatory fallback string.
        """
        repository_dir = argv[1].src_root
        command = 'git describe --tags'
        tag_output = '[gittag: ERROR, NOT A GIT REPO]'
        try:
            tag_output = subprocess.check_output(command.split(), cwd=repository_dir).decode().split('-')[0]
        except:
            pass
        return tag_output

    def post(self, *argv):
        """Perform no post-build work.

        Args:
            *argv: Lifecycle arguments supplied by the plugin dispatcher.
        """
        pass
