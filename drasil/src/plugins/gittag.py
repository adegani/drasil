import subprocess as subprocess


class DrasilPlug():
    hooks = ['gittag']
    name = 'GIT_tag'
    description = 'Print the current tag fpr the website repository'
    help_str = 'The plugin has no args. When the trigger is found,'
    help_str += 'it retrieve the current tag of the git repository of the'
    help_str += 'src website. If the website is not a git repo, it fails.'

    def pre(self, *argv):
        pass

    def run(self, *argv):
        in_dir = argv[1].src_root
        cmd = 'git describe --tags'
        output = '[gittag: ERROR, NOT A GIT REPO]'
        try:
            output = subprocess.check_output(cmd.split(), cwd=in_dir).decode()
        except:
            pass
        return output

    def post(self, *argv):
        pass
