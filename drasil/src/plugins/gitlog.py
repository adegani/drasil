import subprocess as subprocess


class DrasilPlug():
    """Render a compact Git commit log for the source repository."""
    hooks = ['gitlog']
    name = 'GIT_log'
    description = 'Print the current git log of the website repository'
    help_str = 'The plugin has no args. When the trigger is found,'
    help_str += 'it retrieve the commit log of the git repository of the'
    help_str += 'src website. If the website is not a git repo, it fails.'

    def pre(self, *argv):
        """Perform no pre-build work.

        Args:
            *argv: Lifecycle arguments supplied by the plugin dispatcher.
        """
        pass

    def run(self, *argv):
        """Return recent commits formatted as HTML, or an error placeholder.

        Args:
            *argv: Dispatcher arguments; the rendering context is at index one.

        Returns:
            HTML fragments for commits, or an error placeholder.
        """
        repository_dir = argv[1].src_root
        command = 'git log --pretty=oneline'
        log_html = '[gitlog: ERROR, NOT A GIT REPO]'
        entry_template = '<div class="git_log_entry">'
        entry_template += '    <span class="git_hash">2{}</span>'
        entry_template += '    <span class="git_commit_msg">{}</span>'
        entry_template += '</div>'

        try:
            log_output = subprocess.check_output(command.split(), cwd=repository_dir).decode()
            log_lines = log_output.split('\n')
            for index, line in enumerate(log_lines):
                if len(line.split()) > 0:
                    line = self._sanitize_html(line)
                    log_lines[index] = entry_template.format(line.split()[0], ' '.join(line.split()[1:]))
            log_html = ''.join(log_lines)
        except Exception as error:
            print(error)
        return log_html

    def post(self, *argv):
        """Perform no post-build work.

        Args:
            *argv: Lifecycle arguments supplied by the plugin dispatcher.
        """
        pass

    def _sanitize_html(self, string):
        """Escape characters that could alter generated commit-log markup.

        Args:
            string: Commit-log text to insert into HTML.

        Returns:
            Sanitised text safe for the plugin's generated markup.
        """
        spec_chars = {'\"': '&quot;',
                      '\'': '&#39;',
                    #   '<': '&lt;',
                    #   '>': '&gt;',
                      '%': '&#37;',
                      '$': '&#36;',
                      }
        # This is done first to prevent escaping other spec_chars.
        htmlstring = string.replace('&', '&amp;')
        for seq, esc in spec_chars.items():
            htmlstring = htmlstring.replace(seq, esc)
        return htmlstring
