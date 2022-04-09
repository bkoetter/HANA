from re import match

from sys import argv, exit


def main():
    print('This is a module and provides no standalone functionality.')


def get_opts():
    opts = {}
    if len(argv) < 2:
        print(f'Usage: {argv[0]} <SID> [<Instance-Nr.>]')
        exit(1)

    if not match('[A-Z][A-Z0-9]{2}$', argv[1]):
        print(f'Syntax-Error. Invalid SID: {argv[1]}')
        exit(1)
    opts['sid'] = argv[1]

    if len(argv) > 2:
        if not match(r'\d{2}$', argv[2]):
            print(f'Syntax-Error. Invalid instance number: {argv[2]}')
            exit(1)
        opts['number'] = argv[2]
    else:
        opts['number'] = '00'

    return opts


if __name__ == '__main__':
    main()
