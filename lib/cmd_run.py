from subprocess import run, CalledProcessError

from sys import exit


def main():
    print('This is a module and provides no standalone functionality.')


def cmd_run(cmd: str, stdin: bytes = None, no_exit: tuple = (0,)) -> None:
    """Execute an OS command with common and trivial error handling. Will terminate program flow in case of error.
    :param cmd: Command to execute on OS
    :param stdin: Input to command stdin channel
    :param no_exit: Do not terminate program flow on these exit codes
    """
    if no_exit is None:
        no_exit = [0, ]
    try:
        run(cmd, input=stdin, check=True, shell=True)
    except CalledProcessError as err:
        if err.returncode not in no_exit:
            print(f'WARNING: Command exited with non-zero return code:\n"{cmd}"')
            exit(err.returncode)


if __name__ == '__main__':
    main()
