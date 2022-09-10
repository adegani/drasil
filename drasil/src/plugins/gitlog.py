import subprocess as subprocess


class DrasilPlug():
    hooks = ['gitlog']
    name = 'GIT_log'
    description = 'Print the current git log of the website repository'
    help_str = 'The plugin has no args. When the trigger is found,'
    help_str += 'it retrieve the commit log of the git repository of the'
    help_str += 'src website. If the website is not a git repo, it fails.'

    def pre(self, *argv):
        pass

    def run(self, *argv):
        in_dir = argv[1].src_root
        cmd = 'git log --pretty=oneline'
        output = '[gitlog: ERROR, NOT A GIT REPO]'
        hash_str = '<span class="git_hash">{}</span>'
        msg_str = '<span class="git_commit_msg">{}</span>'
        try:
            output = subprocess.check_output(cmd.split(), cwd=in_dir).decode()
            decoded_txt = output.split('\n')
            for n, line in enumerate(decoded_txt):
                if len(line.split()) > 0:
                    line = self._sanitize_html(line)
                    decoded_txt[n] = hash_str.format(line.split()[0]) + ' ' +\
                                     msg_str.format(' '.join(line.split()[1:]))\
                                     + '<br>\n'
            output = ''.join(decoded_txt)
        except Exception as e:
            print(e)
        return output

    def post(self, *argv):
        pass

    def _sanitize_html(self, string):
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
