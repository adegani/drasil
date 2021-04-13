import os.path
import time 
import sys
import argparse
import importlib
import pkgutil
import logging

from . import drasil_plugins as pns

VERSION = '0.1'
SCRIPT_FILE = os.path.realpath(__file__)
SCRIPT_ROOT = os.path.dirname(SCRIPT_FILE)

PLUGIN_DIR = SCRIPT_ROOT + '/drasil_plugins'

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')
def main(argv):
    args = parse_args(argv)

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
    output_dir = args.out

    logging.info('Building website "%s" in to folder "%s"' % (src_root, output_dir))
    # logging.warning('Watch out!')

def parse_plugins(plugin_dir):
    plugin_list = []
    logging.debug('Parsing plugins in folder %s' % plugin_dir)

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
    parser.add_argument('-v', '--version', action='store_true',
                        help='Print the version and exits')
    res = parser.parse_args(argv[1:])

    return res

if __name__ == '__main__':
    main(sys.argv)
