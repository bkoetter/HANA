import os.path
from glob import glob
from os import getenv
from typing import Dict
from sys import argv

import sys


def get_opts() -> Dict[str, str]:
    if len(argv) != 3:
        print(f'Usage: {argv[0]} <archive-dir> <extract-dir>')
        sys.exit(1)

    return {'archive_dir': argv[1], 'extract_dir': argv[2]}


def check_dir(opts: Dict[str, str]) -> None:
    for media_dir in opts.values():
        if not os.path.isdir(media_dir):
            print(f'{media_dir} does not exist')
            sys.exit(1)


def get_hdblcm(opts: Dict[str, str]) -> Dict[str, str]:
    sid = getenv('SAPSYSTEMNAME', '[A-Z][A-Z0-9][A-Z0-9]')
    try:
        opts['hdblcm'] = glob(f'/hana/shared/{sid}/hdblcm/hdblcm')[0]
    except IndexError:
        print(f'Warning: No hdblm found at /hana/shared/{sid}/hdblcm/hdblcm')
        opts['hdblcm'] = ''
    return opts


def get_cmd_hdblcm(opts: Dict[str, str]) -> str:
    """get_cmd_hdblcm builds the command string for OS execution with hdblcm"""
    return " ".join([
        opts['hdblcm'],
        '--batch',
        '--action=extract_components',
        '--component_archives_dir=' + opts['archive_dir'],
        '--extract_temp_dir=' + opts['extract_dir'],
        '--overwrite_extract_dir',
    ])


def get_cmd_sapcar(opts: Dict[str, str]) -> str:
    """get_cmd_sapcar builds the command string for OS execution with sapcar"""
    return ''


# LD_LIBRARY_PATH=/catalog/media/95-automation/sapcar /catalog/media/95-automation/sapcar/SAPCAR -R /catalog/media/02-extracted/hana -crl /catalog/media/95-automation/sapcar/crlbag.p7s -manifest SAP_HANA_CLIENT/SIGNATURE.SMF -xVf /catalog/media/01-media/sap-hana-client/IMDB_CLIENT20_011_20-80002082.SAR
# LD_LIBRARY_PATH=/catalog/media/95-automation/sapcar /catalog/media/95-automation/sapcar/SAPCAR -R /catalog/media/02-extracted/hana -crl /catalog/media/95-automation/sapcar/crlbag.p7s -manifest SAP_HANA_DATABASE/SIGNATURE.SMF -xVf /catalog/media/01-media/sap-hana-database/IMDB_SERVER20_061_0-80002031.SAR
# chmod a+r /catalog/media/02-extracted/hana/*/*.SMF-extracted/hana/*/*.SMF


def main():
    opts: Dict[str, str] = get_opts()
    opts: Dict[str, str] = get_hdblcm(opts)
    check_dir(opts)
    if opts['hdblcm']:
        cmd = get_cmd_hdblcm(opts)
    else:
        cmd = get_cmd_sapcar(opts)
    print(cmd)
    # extract_archive(opts)


if __name__ == '__main__':
    main()
