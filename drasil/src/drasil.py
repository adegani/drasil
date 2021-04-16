import os.path
import time 
import sys
import argparse
import importlib
import pkgutil
import copy
import logging

from . import drasil_plugins as pns

VERSION = '0.1'
SCRIPT_FILE = os.path.realpath(__file__)
SCRIPT_ROOT = os.path.dirname(SCRIPT_FILE)

PLUGIN_DIR = SCRIPT_ROOT + '/drasil_plugins'

logging.basicConfig(level=logging.CRITICAL,
                    # filename='example.log',
                    format='%(asctime)s:DRASIL:%(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
def main(argv):
    start_time = time.time()

    bifrost = DrasilContext()
    args = parse_args(argv)

    if args.v:
        logging.getLogger().setLevel(logging.WARNING)
    if args.vv:
        logging.getLogger().setLevel(logging.INFO)
    if args.vvv:
        logging.getLogger().setLevel(logging.DEBUG)

    mod_time = time.ctime(os.path.getmtime(SCRIPT_FILE))
    print("This is Drasil!! (v%s - %s)" % (VERSION, mod_time))

    if args.version:
        exit(0)

    # Plugins will be a list of dict
    # The list is automatically populated with all the modules in PLUGIN_DIR folder
    # Each entry of the list is a dict with two fields:
    #   - 'class' that is the pointer to the DrasilPlug() class
    #   - 'hooks' that are the keywords used for triggering the plugin 
    plugins = parse_plugins(PLUGIN_DIR)

    if args.plugin_list:
        print('The following plugin are available:')
        for p in plugins:
            print(' -> %s - %s' % (p['class'].name, p['class'].description))
        exit(0)
    
    if args.plugin_help is not None:
        for p in plugins:
            if args.plugin_help.lower() == p['class'].name.lower():
                print()
                print('%s - %s' % (p['class'].name, p['class'].description))
                print('-')
                print(p['class'].help_str)
                print('-')
                print('hooks: %s' % ', '.join(p['class'].hooks))
        exit(0)

    src_root = args.src

    if not os.path.exists(src_root):
        err_str = 'The path %s does not exists' % src_root
        print(err_str)
        logging.error(err_str)
        exit(1)

    output_dir = args.out
    if not args.y:
        if os.path.exists(output_dir):
            resp = input('The path %s already exists. Overwrite? [Y/n] ' % output_dir)
            if not (len(resp) == 0 or resp.lower() == 'y'):
                exit(0)
    else:
        logging.warning('The path %s already exists and will be overwritten' % output_dir)

    if src_root == output_dir:
        err_str = 'The src and the output path cannot be the same (%s)' % src_root
        print(err_str)
        logging.error(err_str)
        exit(1)

    bifrost.output_dir = output_dir
    bifrost.src_root = src_root
    bifrost.current_node = src_root

    logging.info('Building website "%s" into folder "%s"' % (src_root, output_dir))

    print('YGGDRASIL roots are in %s' % src_root)

    bifrost_walk(bifrost)

    exec_time = time.time() - start_time
    print('\n%d steps walked on the Bifrost in %.2f seconds' % (DrasilContext.tot_steps, exec_time))
    logging.info('Drasil job completed in %f seconds' % exec_time)

    exit(0)

def bifrost_walk(bifrost):
    DrasilContext.tot_steps += 1
    root = bifrost.current_node
    level = bifrost.current_level

    step = copy.copy(bifrost)
    step.current_level += 1

    step.brothers = [n for n in os.listdir(root) if n[0] is not '_']

    if level == 0:
        print('+')
    print('='*(level+1))
    for node in os.listdir(root):
        # print('NODE: %s' % node)
        if node[0] == '_':
            continue
        new_path = os.path.join(root, node)
        step.current_node = new_path
        if os.path.isfile(new_path):
            print('|'*(level+1))
        if os.path.isdir(new_path):
            bifrost_walk(step)

        str_tpl = (step.current_node, ', '.join(step.brothers))
        logging.debug('I\'m %s and my brothers are: %s' % str_tpl)
        node_render(step)

def node_render(leaf, *argv):
    level = leaf.current_level
    node = leaf.current_node
    
    append_extension = False
    if os.path.isdir(node):
        append_extension = True

    file_name = os.path.split(node)[-1]
    if append_extension:
        file_name += '.html'
    file_path = os.path.join(leaf.output_dir, file_name).replace(' ', '_')
    file_dir = os.path.dirname(file_path)

    logging.info('Rendering [level %d page] %s' % (level, file_path))
    if not os.path.exists(file_dir):
        logging.warning('%s folder not exist. Creating...' % file_dir)
        os.makedirs(file_dir)

    f = open(file_path, 'w')
    # f.write("Woops! I have deleted the content!")
    f.close()

def parse_plugins(plugin_dir):
    plugin_list = []
    logging.debug('Parsing plugins (%s)' % plugin_dir)

    for _, name, _ in pkgutil.iter_modules(pns.__path__, pns.__name__ + "."):
        logging.debug('Plugin found: %s' % name)
        pluggo = importlib.import_module(name)
        Plug = pluggo.DrasilPlug()
        hooks = Plug.hooks
        my_plug = {'class': Plug, 'hooks': hooks}
        plugin_list.append(my_plug)
    
    return plugin_list

def parse_args(argv):
    """CLI arguments parsing

    Args:
        argv (list): list of args to be parsed

    Returns:
        ArgumentParser: Parsed arguments
    """    
    parser = argparse.ArgumentParser(
        description='Drasil, static HTML website generator V.' + VERSION,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-l', '--plugin-list', action='store_true',
                        help='Print the list of the installed plugins')
    parser.add_argument('--plugin-help', help='print the help of a given plugin')
    parser.add_argument('--src', help='Website root path to be compiled',
                        default='.')
    parser.add_argument('--out', help='Compiled website output dir',
                        default='../build')
    parser.add_argument('-y', action='store_true',
                        help='Forces YES [Y] to all questions')
    parser.add_argument('-v', action='store_true',
                        help='verbosity level: WARNINGS')
    parser.add_argument('-vv', action='store_true',
                        help='verbosity level: INFO')
    parser.add_argument('-vvv', action='store_true',
                        help='verbosity level: DEBUG')
    parser.add_argument('--version', action='store_true',
                        help='Print the version and exits')
    res = parser.parse_args(argv[1:])

    return res

if __name__ == '__main__':
    main(sys.argv)

class DrasilContext(object):
    def __init__(self):
        super(DrasilContext, self).__init__()
        DrasilContext.tot_steps = 0
        
        self.src_root = None
        self.output_dir = None
        self.current_node = None
        self.current_level = 0

        self.brothers = None
        self.prev_menu_elements = []
