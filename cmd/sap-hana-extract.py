import os.path
from glob import glob
from os import getenv
from typing import Dict

import sys


def get_opts() -> Dict[str, str]:
    if len(sys.argv) != 3:
        print(f'Usage: {sys.argv[0]} <archive-dir> <extract-dir>')
        sys.exit(1)

    return {'archive_dir': sys.argv[1], 'extract_dir': sys.argv[2]}


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
        print(f'Error: No hdblm found at /hana/shared/{sid}/hdblcm/hdblcm')
        sys.exit(1)
    return opts


def get_cmd(opts: Dict[str, str]) -> str:
    """get_cmd builds the command string for OS execution"""
    return " ".join([
        opts['hdblcm'],
        '--batch',
        '--action=extract_components',
        '--component_archives_dir=' + opts['archive_dir'],
        '--extract_temp_dir=' + opts['extract_dir'],
        '--overwrite_extract_dir',
    ])

# LD_LIBRARY_PATH=/catalog/media/95-automation/sapcar /catalog/media/95-automation/sapcar/SAPCAR -R /catalog/media/02-extracted/hana -crl /catalog/media/95-automation/sapcar/crlbag.p7s -manifest SAP_HANA_CLIENT/SIGNATURE.SMF -xVf /catalog/media/01-media/sap-hana-client/IMDB_CLIENT20_011_20-80002082.SAR
# LD_LIBRARY_PATH=/catalog/media/95-automation/sapcar /catalog/media/95-automation/sapcar/SAPCAR -R /catalog/media/02-extracted/hana -crl /catalog/media/95-automation/sapcar/crlbag.p7s -manifest SAP_HANA_DATABASE/SIGNATURE.SMF -xVf /catalog/media/01-media/sap-hana-database/IMDB_SERVER20_061_0-80002031.SAR
# chmod a+r /catalog/media/02-extracted/hana/*/*.SMF-extracted/hana/*/*.SMF

def main():
    opts: Dict[str, str] = get_opts()
    opts: Dict[str, str] = get_hdblcm(opts)
    check_dir(opts)
    get_cmd(opts)
    # extract_archive(opts)
    print(opts['hdblcm'])


if __name__ == '__main__':
    main()
