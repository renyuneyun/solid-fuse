#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Entrypoint of the SolidFUSE filesystem.

Credit the example filesystem from pyfuse3 which this file is based on.
'''

from argparse import ArgumentParser
import logging
import pyfuse3
import trio
from config import load_config
from fsimpl import SolidFs

try:
    import faulthandler
except ImportError:
    pass
else:
    faulthandler.enable()

log = logging.getLogger(__name__)


def init_logging(debug=False):
    formatter = logging.Formatter('%(asctime)s.%(msecs)03d %(threadName)s: '
                                  '[%(name)s] %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    if debug:
        handler.setLevel(logging.DEBUG)
        root_logger.setLevel(logging.DEBUG)
    else:
        handler.setLevel(logging.INFO)
        root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)


def parse_args():
    '''Parse command line'''

    parser = ArgumentParser()

    parser.add_argument('config', type=str,
                        help='Config file')
    parser.add_argument('mountpoint', type=str,
                        help='Where to mount the file system')
    parser.add_argument('--debug', action='store_true', default=False,
                        help='Enable debugging output')
    parser.add_argument('--debug-fuse', action='store_true', default=False,
                        help='Enable FUSE debugging output')

    return parser.parse_args()


def main():
    options = parse_args()
    init_logging(options.debug)
    config = load_config(options.config)

    testfs = SolidFs(config.pod,
                     config.idp, config.username, config.password)
    fuse_options = set(pyfuse3.default_options)
    fuse_options.add('fsname=solidfuse')
    if options.debug_fuse:
        fuse_options.add('debug')
    pyfuse3.init(testfs, options.mountpoint, fuse_options)
    try:
        trio.run(pyfuse3.main)
    except:
        pyfuse3.close(unmount=False)
        raise

    pyfuse3.close()


if __name__ == '__main__':
    main()
