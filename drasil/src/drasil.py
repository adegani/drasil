import sys
import argparse
from ddate.base import DDate
import logging

VERSION = '0.1'


def main(argv):
    args = parse_args(argv)

    # logging.basicConfig(level=logging.DEBUG,
    #                     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    #                     datefmt='%m/%d/%Y %I:%M:%S %p')
    # print("This is Drasil!!")
    # print(DDate())
    # logging.info("INIT")
    # logging.warning('Watch out!')


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description='Drasil, static HTML website generator V.' + VERSION,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--in', help='Website root path to be compiled',
                        default='.')
    parser.add_argument('--out', help='Compiled website output dir',
                        default='../build')
    parser.add_argument('--version', action='store_true',
                        help='Print the version and exits')
    res = parser.parse_args(argv[1:])

    return res

if __name__ == '__main__':
    main(sys.argv)
