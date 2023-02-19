#!/usr/bin/env python3

"""Update SAP Web Dispatcher"""
from glob import glob
from os import path

from lib.cmd_run import cmd_run
from lib.flags import get_opts


def get_update() -> str:
    """get_update tries to determine the latest available SAP Web Dispatcher update file"""
    files: list = []
    update_file = 'SAPWEBDISP_SP_*-*.SAR'
    update_locations = (
        '/catalog/media/01-media/sap-web-dispatcher/',
    )
    for directory in update_locations:
        files = glob(path.join(directory, update_file))

    if len(files) > 1:
        print('More than one update file found:')
        for file in files:
            print(file)
        exit(1)
    return files[0]


def control_webdisp(opts: dict, function: str):
    cmd: str = " ".join([
        f'sudo -niu {opts["sid"].lower()}adm',
        f'/usr/sap/hostctrl/exe/sapcontrol',
        f'-nr {opts["number"]} -function {function}'
    ])
    cmd_run(cmd, no_exit=(0, 3, 4))


def extract_update(opts: dict, file):
    cmd: str = " ".join([
        f'sudo -niu {opts["sid"].lower()}adm',
        f'/usr/sap/hostctrl/exe/SAPCAR',
        f'-R /usr/sap/{opts["sid"]}/SYS/exe/run',
        f'-crl /catalog/media/95-automation/sapcar/crlbag.p7s',
        f'-manifest SIGNATURE.SMF',
        f'-xVf {file}'
    ])
    cmd_run(cmd)


def main():
    opts: dict = get_opts()
    file: str = get_update()
    extract_update(opts, file)
    control_webdisp(opts, 'RestartSystem')
    control_webdisp(opts, 'GetProcessList')


if __name__ == '__main__':
    main()
