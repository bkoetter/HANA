from subprocess import run, CalledProcessError

from sys import exit


def main():
    print('This is a module and provides no standalone functionality.')


def cmd_run(cmd: str, stdin: bytes = None) -> None:
    try:
        run(cmd, input=stdin, check=True, shell=True)
    except CalledProcessError as err:
        print(f'WARNING: Command "{cmd}" exited with non-zero return code')
        exit(err.returncode)


if __name__ == '__main__':
    main()
