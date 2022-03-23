#!/usr/bin/env python3

"""Install SAP HANA Database"""
import platform
import socket
from getpass import getpass
from os import getenv
from os.path import isfile
from re import match
from subprocess import run, CalledProcessError, DEVNULL

import sys
from grp import getgrnam
from pwd import getpwnam


def get_opts():
    opts = {}
    if len(sys.argv) != 3:
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


def prereq_check_packages() -> None:
    is_missing = False
    os_packages = {
        'sles': ('insserv-compat', 'libatomic1', 'libltdl7', 'uuidd'),
        'Red Hat Enterprise Linux': ('libatomic', 'libtool-ltdl', 'compat-sap-c++-10', 'uuidd')
    }
    if os_packages.get(platform.linux_distribution()[0], None) is None:
        print(f'Operating system "{platform.linux_distribution()[0]}" not supported')
        sys.exit(1)
    for package in os_packages[platform.linux_distribution()[0]]:
        try:
            run(f'rpm -q {package}', check=True, shell=True, stdout=DEVNULL)
        except CalledProcessError as err:
            print(f'WARNING: {err}')
            is_missing = True
    if is_missing:
        sys.exit(1)


def prereq_check_hostagent(host="127.0.0.1", port=1129) -> None:
    try:
        socket.create_connection((host, port), timeout=20)
        print(f'Connection to {host} port {port} successful')
        return None
    except TimeoutError:
        print(f'Connection to {host} port {port} timed out')
        sys.exit(1)
    except ConnectionRefusedError:
        print(f'Connection to {host} port {port} refused')
        sys.exit(1)
    except socket.error as e:
        print(f'Connection to {host} port {port} failed: {e}')
        sys.exit(1)


def get_passwd():
    """Retrieve password from env or user input, compile password xml input"""
    password = getenv('HANA_PASSWORD')
    password_verify = ""
    if password is None:
        while password != password_verify:
            password = getpass("Enter master password: ")
            password_verify = getpass("Enter password to verify: ")
    return bytes("".join((
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<Passwords>',
        f'<password><![CDATA[{password}]]></password>',
        f'<sapadm_password><![CDATA[{password}]]></sapadm_password>',
        f'<system_user_password><![CDATA[{password}]]></system_user_password>',
        f'<root_password><![CDATA[{password}]]></root_password>',
        '</Passwords>'
    )), encoding='ascii')
    # return bytes("".join(xml_pass), encoding='ascii')


def get_userid(user: str) -> int:
    """Determine UID for <sid>adm or query UID for new user <sid>adm"""
    try:
        return getpwnam(user).pw_uid
    except KeyError:
        print(f'Warning: Group "{user}" does not exist')
        try:
            return int(input(f'Enter a UID number to create "{user}" or any non-numeric input to abort: '))
        except ValueError:
            print('Program execution aborted')
            sys.exit(0)


def get_groupid(group: str) -> int:
    """Determine GID for sapsys or query GID input for new group sapsys"""
    try:
        return getgrnam(group).gr_gid
    except KeyError:
        print(f'Warning: Group "{group}" does not exist')
        try:
            return int(input(f'Enter a GID number to create "{group}" or any non-numeric input to abort: '))
        except ValueError:
            print('Program execution aborted')
            sys.exit(0)


def get_hdblcm():
    """get_hdblcm tries to determine the hdblcm program location"""
    hdblcm_locations = (
        '/media/sap/02-extracted/hana/SAP_HANA_DATABASE/hdblcm',
        '/catalog/media/02-extracted/hana/SAP_HANA_DATABASE/hdblcm',
        '/opt/install/02-extracted/hana/SAP_HANA_DATABASE/hdblcm',
        f'{getenv("HOME")}/sap-install/SAP_HANA_DATABASE/hdblcm',
    )
    for hdblcm in hdblcm_locations:
        if isfile(hdblcm):
            return hdblcm
    print('Failed to find hdblcm at the following locations:')
    for hdblcm in hdblcm_locations:
        print(hdblcm)
    sys.exit(1)


def get_cmdexe(opts: dict, hdblcm: str):
    """get_command builds the command string for OS execution"""
    return " ".join([
        'sudo',
        hdblcm,
        '--batch',
        '--action=install',
        '--verify_signature',
        '--autostart=1',
        '--sid=' + opts.get("sid"),
        '--number=' + opts.get("number", "00"),
        '--userid=' + str(get_userid(f'{opts.get("sid").upper()}adm')),
        '--groupid=' + str(get_groupid('sapsys')),
        '--sapmnt=/hana/shared',
        '--datapath=/hana/data/' + opts.get("sid"),
        '--logpath=/hana/log/' + opts.get("sid"),
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


def main():
    opts: dict = get_opts()
    prereq_check_packages()
    prereq_check_hostagent()
    hdblcm: str = get_hdblcm()
    passwd: bytes = get_passwd()
    cmdexe: str = get_cmdexe(opts, hdblcm)
    cmdrun(cmdexe, passwd)


if __name__ == '__main__':
    main()
