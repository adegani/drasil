import os.path
import time 
import sys
import argparse
import logging
from distutils.dir_util import copy_tree

from .drasil_bifrost import DrasilBifrost
from .drasil_plugins import DrasilPlugin

VERSION = '0.3'
SCRIPT_FILE = os.path.realpath(__file__)

TEMPLATE_FILE = '_template.html'

logging.basicConfig(level=logging.CRITICAL,
                    # filename='example.log',
                    format='%(asctime)s:DRASIL:%(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
def main(argv):

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

    plugins = DrasilPlugin()
    bifrost = DrasilBifrost(plugins)

    if args.plugin_list:
        plugins.print_list()
        exit(0)
    
    if args.plugin_help is not None:
        plugins.print_help(args.plugin_help)
        exit(0)

    src_root = args.src

    if not os.path.exists(src_root):
        err_str = 'The path %s does not exists' % src_root
        print(err_str)
        logging.error(err_str)
        exit(1)

    output_dir = args.OUTPUT_FOLDER
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

    start_time = time.time()
    logging.info('Building website "%s" into folder "%s"' % (src_root, output_dir))

    print('YGGDRASIL roots are in %s' % src_root)
    if os.path.exists(os.path.join(bifrost.src_root, TEMPLATE_FILE)):
        bifrost.template = os.path.join(bifrost.src_root, TEMPLATE_FILE)
        logging.info('Global template found: %s' % bifrost.template)

    bifrost.walk()

    exec_time = time.time() - start_time
    print('\n%d steps walked on the Bifrost in %.2f seconds' % (DrasilBifrost.tot_steps, exec_time))
    logging.info('Drasil job completed in %f seconds' % exec_time)

    src_assets = os.path.join(bifrost.src_root, 'assets')
    dest_assets = os.path.join(bifrost.output_dir, 'assets')
    if os.path.exists(src_assets):
        logging.info('Copying assets %s -> %s' % (src_assets, dest_assets))
        copy_tree(src_assets, dest_assets)
    else:
        logging.warning('No assets folder found: %s' % src_assets)

    exit(0)

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
    parser.add_argument('OUTPUT_FOLDER', help='Compiled website output dir')
    parser.add_argument('-l', '--plugin-list', action='store_true',
                        help='Print the list of the installed plugins')
    parser.add_argument('--plugin-help', help='print the help of a given plugin')
    parser.add_argument('--src', help='Website root path to be compiled',
                        default='.')
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
