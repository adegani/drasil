import time
import sys
import argparse
import logging
import re
from importlib.metadata import PackageNotFoundError, version as installed_version
from pathlib import Path
import shutil

from .drasil_bifrost import DrasilBifrost
from .drasil_plugins import DrasilPlugin

SCRIPT_FILE = Path(__file__).resolve()
PYPROJECT_FILE = SCRIPT_FILE.parents[2] / 'pyproject.toml'

TEMPLATE_FILE = '_template.html'

LOG_FORMAT = '%(asctime)s:DRASIL:%(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def get_version():
    """Return the installed distribution version or the local project version.

    Returns:
        Version declared in installed package metadata, falling back to the
        local ``pyproject.toml`` when running directly from the checkout.

    Raises:
        RuntimeError: If no version declaration can be found.
    """
    try:
        return installed_version('drasil')
    except PackageNotFoundError:
        project_config = PYPROJECT_FILE.read_text(encoding='utf-8')
        match = re.search(r'^version\s*=\s*["\']([^"\']+)["\']\s*$', project_config, re.MULTILINE)
        if match:
            return match.group(1)
    raise RuntimeError(f'Unable to determine Drasil version from {PYPROJECT_FILE}')


VERSION = get_version()


def configure_logging(verbosity):
    """Configure the root logger from a CLI verbosity count.

    Args:
        verbosity: Number of ``-v`` flags supplied by the user.
    """
    levels = (logging.CRITICAL, logging.WARNING, logging.INFO, logging.DEBUG)
    logging.basicConfig(
        level=levels[min(verbosity, len(levels) - 1)],
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
    )


def paths_overlap(first, second):
    """Return whether two resolved paths are identical or nested.

    Args:
        first: First resolved path to compare.
        second: Second resolved path to compare.

    Returns:
        True when either path is the other path or one contains the other.
    """
    return first == second or first in second.parents or second in first.parents


def clean_output(output_dir):
    """Remove generated output, retaining regular ``thumb_*`` files and parents."""
    for entry in output_dir.iterdir():
        if entry.is_symlink():
            entry.unlink()
        elif entry.is_dir():
            clean_output(entry)
            if not any(entry.iterdir()):
                entry.rmdir()
        elif not (entry.is_file() and entry.name.startswith('thumb_')):
            entry.unlink()


def main(argv=None):
    """Run the static-site build command and return its process exit code.

    Args:
        argv: Command arguments excluding the executable name. Uses ``sys.argv``
            when omitted.

    Returns:
        Zero on success, otherwise a non-zero process exit code.
    """
    args = parse_args(argv)
    configure_logging(args.verbose)

    mod_time = time.ctime(SCRIPT_FILE.stat().st_mtime)
    print(f'This is Drasil!! (v{VERSION} - {mod_time})')

    if args.version:
        return 0

    plugins = DrasilPlugin()
    bifrost = DrasilBifrost(VERSION, plugins)

    if args.plugin_list:
        plugins.print_list()
        return 0

    if args.plugin_help is not None:
        plugins.print_help(args.plugin_help)
        return 0

    src_root = Path(args.src).expanduser().resolve()
    output_dir = Path(args.out).expanduser().resolve()

    if not src_root.is_dir():
        err_str = f'The source path is not a directory: {src_root}'
        print(err_str)
        logging.error(err_str)
        return 1

    if paths_overlap(src_root, output_dir):
        err_str = f'Source and output paths must not overlap ({src_root}, {output_dir})'
        print(err_str)
        logging.error(err_str)
        return 1

    if output_dir.exists():
        if output_dir.is_symlink() or not output_dir.is_dir():
            err_str = f'Output path must be a real directory: {output_dir}'
            print(err_str)
            logging.error(err_str)
            return 1
        if not args.y:
            response = input(f'The path {output_dir} already exists. Clean and overwrite (keeping thumbnails)? [Y/n] ')
            if response.strip().lower() not in ('', 'y', 'yes'):
                return 0
        logging.warning('Cleaning output folder before build (keeping thumbnails): %s', output_dir)
        clean_output(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    bifrost.output_dir = str(output_dir)
    bifrost.src_root = str(src_root)
    bifrost.current_node = str(src_root)

    start_time = time.perf_counter()
    logging.info('Building website "%s" into folder "%s"', src_root, output_dir)

    print(f'YGGDRASIL roots are in {src_root}')
    template_file = src_root / TEMPLATE_FILE
    if template_file.exists():
        bifrost.template_file = str(template_file)
        logging.info('Global template found: %s', template_file)

    # Running the pre processing method of each plugins
    plugins.run_pre()

    # Walking on the Bifrost (i.e. recursively generate the website)
    bifrost.walk()

    # Running the post processing method of each plugins
    plugins.run_post()

    exec_time = time.perf_counter() - start_time
    print(f'\n{DrasilBifrost.tot_steps} steps walked on the Bifrost in {exec_time:.2f} seconds')
    logging.info('Drasil job completed in %f seconds', exec_time)

    src_assets = src_root / 'assets'
    dest_assets = output_dir / 'assets'
    if src_assets.is_dir():
        logging.info('Copying assets %s -> %s', src_assets, dest_assets)
        shutil.copytree(src_assets, dest_assets, dirs_exist_ok=True)
    else:
        logging.warning('No assets folder found: %s', src_assets)

    return 0


def parse_args(argv=None):
    """Parse command-line arguments and validate arguments required for a build.

    Args:
        argv (list | None): command arguments, excluding the executable name.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Drasil, static HTML website generator V.' + VERSION,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-o', '--out', help='Compiled website output dir', required=False)
    parser.add_argument('-l', '--plugin-list', action='store_true',
                        help='Print the list of the installed plugins')
    parser.add_argument('--plugin-help', help='print the help of a given plugin')
    parser.add_argument('--src', help='Website root path to be compiled',
                        default='.')
    parser.add_argument('-y', action='store_true',
                        help='Forces YES [Y] to all questions')
    parser.add_argument('-v', dest='verbose', action='count', default=0,
                        help='increase verbosity: -v warning, -vv info, -vvv debug')
    parser.add_argument('--version', action='store_true',
                        help='Print the version and exits')
    args = parser.parse_args(argv)
    if args.out is None and not (args.plugin_list or args.plugin_help or args.version):
        parser.error('the following arguments are required: -o/--out')
    return args


if __name__ == '__main__':
    sys.exit(main())
