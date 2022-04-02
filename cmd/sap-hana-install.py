#!/usr/bin/env python3

"""Install SAP HANA Database"""
import csv
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
    if len(sys.argv) < 2:
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


def get_os_release() -> dict:
    if sys.platform != 'linux':
        print(f'Error: Operating system {sys.platform} unsupported. Linux is supported exclusively.')
        sys.exit(1)

    os_release = {}
    os_release_file = '/etc/os-release'

    try:
        with open(os_release_file) as f:
            reader = csv.reader(f, delimiter='=')
            for row in reader:
                if len(row) >= 2:
                    os_release[row[0]] = row[1]
    except FileNotFoundError:
        print(f'Error: File {os_release_file} not found. Linux distribution possibly unsupported.')
        sys.exit(1)

    return os_release


def prereq_check_packages() -> None:
    is_missing = False
    os_packages = {
        'SLES': ('insserv-compat', 'libatomic1', 'libltdl7', 'uuidd'),
        'RHEL': ('libatomic', 'libtool-ltdl', 'compat-sap-c++-10', 'uuidd')
    }
    dist_name = get_os_release()["NAME"]

    if os_packages.get(dist_name, None) is None:
        print(f'Operating system "{dist_name}" not supported')
        sys.exit(1)

    for package in os_packages[dist_name]:
        try:
            run(f'rpm -q {package}', check=True, shell=True, stdout=DEVNULL)
        except CalledProcessError as err:
            print(f'Error: Operating system package {package} missing ({err})')
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


def get_passwd() -> (bytes, str):
    """Retrieve password from env or user input, compile password xml input"""
    password: str = getenv('HANA_PASSWORD')
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
    )), encoding='ascii'), password


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


def get_hdblcm() -> str:
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


def cmd_hdblcm_install(opts: dict, password_xml: bytes, hdblcm: str) -> None:
    """cmd_hdblcm_install executes command for SAP HANA installation"""
    cmd = " ".join([
        'sudo -n', hdblcm,
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
    cmd_run(cmd, password_xml)


def cmd_hdbuserstore_set(opts: dict, password: str, db: str, user: str, hdbuserstore: str = 'hdbuserstore') -> None:
    """cmd_hdbuserstore_set executes command for SAP HANA installation"""
    if db is None:
        return None

    fqdn = socket.getaddrinfo(socket.gethostname(), 0, flags=socket.AI_CANONNAME)[0][3]
    cmd = " ".join([
        'sudo -niu ' + f'{opts["sid"].lower}', hdbuserstore,
        'Set', fqdn + f':3{opts.get("number", 00)}13@{db.upper()}',
        user, f'{password}'
    ])
    cmd_run(cmd)


def cmd_run(cmd: str, password_xml: bytes = None) -> None:
    try:
        run(cmd, input=password_xml, check=True, shell=True)
    except CalledProcessError as err:
        print(f'WARNING: Command "{cmd}" exited with non-zero return code')
        sys.exit(err.returncode)


def main():
    opts: dict = get_opts()
    prereq_check_packages()
    prereq_check_hostagent()
    hdblcm: str = get_hdblcm()
    password_xml, password = get_passwd()
    cmd_hdblcm_install(opts, password_xml, hdblcm)
    cmd_hdbuserstore_set(opts, password, db='SYSTEMDB', user='BACKUP')
    cmd_hdbuserstore_set(opts, password, db='SYSTEMDB', user='SYSTEM_SYSTEMDB')
    cmd_hdbuserstore_set(opts, password, db=opts["sid"], user=f'SYSTEM_{opts["sid"]}')


if __name__ == '__main__':
    main()
