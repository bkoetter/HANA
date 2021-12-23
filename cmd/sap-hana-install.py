#!/usr/bin/env python3

"""Install SAP HANA Database"""
import subprocess
from getpass import getpass
from os import getenv
from os.path import isfile
from re import match
from subprocess import run, CalledProcessError

import sys
from grp import getgrnam


def prereqcheck():
    is_missing = False
    os_packages = ('libatomic1', 'libltdl7')
    for package in os_packages:
        try:
            subprocess.run(f'rpm -q {package}', check=True, shell=True)
        except CalledProcessError as err:
            print(f'WARNING: {err}')
            is_missing = True
    if is_missing:
        sys.exit(1)


def get_opts():
    opts = {}
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print(f'Usage: {sys.argv[0]} <SID> [<Instance-Nr.>]')
        sys.exit(1)

    if not match('[A-Z][A-Z0-9]{2}$', sys.argv[1]):
        print(f'Syntax-Error. Invalid SID: {sys.argv[1]}')
        sys.exit(1)
    opts['sid'] = sys.argv[1]

    if len(sys.argv) > 2:
        if not match(r'\d{2}$', sys.argv[2]):
            print(f'Syntax-Error. Invalid instance number: {sys.argv[2]}')
            sys.exit(1)
        opts['number'] = sys.argv[2]

    return opts


def get_passwd():
    """Retrieve password from env or user input, compile password xml input"""
    password = getenv('HANA_PASSWORD')
    if password is None:
        password = getpass("Enter master password: ")
    xml_pass = (
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<Passwords>',
        f'<password><![CDATA[{password}]]></password>',
        f'<sapadm_password><![CDATA[{password}]]></sapadm_password>',
        f'<system_user_password><![CDATA[{password}]]></system_user_password>',
        f'<root_password><![CDATA[{password}]]></root_password>',
        '</Passwords>'
    )
    return bytes("".join(xml_pass), encoding='ascii')


def get_hdblcm():
    """get_hdblcm tries to determin the location of the hdblm program"""
    hdblcm_locations = (
        '/opt/install/02-extracted/hana/SAP_HANA_DATABASE/hdblcm',
        f'{getenv("HOME")}/sap-install/SAP_HANA_DATABASE/hdblcm',
        f'{getenv("HOME")}/hdblcm',
    )
    for hdblcm in hdblcm_locations:
        if isfile(hdblcm):
            return hdblcm
    print('Failed to find hdblcm at the following locations:')
    for hdblcm in hdblcm_locations:
        print(hdblcm)
    sys.exit(1)


def get_cmdexe(opts: dict, hdblcm: str, groupid: int):
    """get_command builds the command string for OS execution"""
    return " ".join([
        'sudo',
        hdblcm,
        '--batch',
        '--action=install',
        f'--sid={opts.get("sid")}',
        f'--number={opts.get("number", "00")}',
        f'--groupid={groupid}',
        '--sapmnt=/hana/shared',
        f'--datapath=/hana/data/{opts.get("sid")}',
        f'--logpath=/hana/log/{opts.get("sid")}',
        '--components=server,client',
        '--read_password_from_stdin=xml'
    ])


def cmdrun(cmdexe: str, passwd: bytes):
    print(cmdexe)
    try:
        run(cmdexe, input=passwd, check=True, shell=True)
    except CalledProcessError as err:
        print('WARNING: Command exited with non-zero return code')
        sys.exit(err.returncode)


def get_groupid():
    """Determine GID for sapsys or query GID input for new group sapsys"""
    try:
        return getgrnam("sapsys").gr_gid
    except KeyError:
        print('Warning: Group "sapsys" does not exist')
        try:
            return int(input('Enter a GID number to create "sapsys" or any non-numeric input to abort: '))
        except ValueError:
            print('Program execution aborted')
            sys.exit(0)


def main():
    opts: dict = get_opts()
    prereqcheck()
    hdblcm: str = get_hdblcm()
    passwd: bytes = get_passwd()
    groupid: int = get_groupid()
    cmdexe: str = get_cmdexe(opts, hdblcm, groupid)
    cmdrun(cmdexe, passwd)


if __name__ == '__main__':
    main()
