from __future__ import annotations

import aiohttp
import argparse
import asyncio
import platform
import pyvolt
import sys


def show_version() -> None:
    entries = []

    entries.append('- Python v{0.major}.{0.minor}.{0.micro}-{0.releaselevel}'.format(sys.version_info))
    entries.append('- pyvolt v{}'.format(pyvolt.__version__))

    entries.append(f'- aiohttp v{aiohttp.__version__}')
    uname = platform.uname()
    entries.append('- system info: {0.system} {0.release} {0.version}'.format(uname))
    print('\n'.join(entries))


async def login(email: str, password: str, friendly_name: str | None):
    session = aiohttp.ClientSession()

    state = pyvolt.State()
    http = pyvolt.HTTPClient(session=session, state=state)

    state.setup(http=http)

    async with session:
        resp = await http.login_with_email(email, password, friendly_name=friendly_name)
        if isinstance(resp, pyvolt.MFARequired):
            print('--- MFA required. ---')
            print('---------------------')
            print('|  Whats available  |')
            methods = resp.allowed_methods

            if pyvolt.MFAMethod.recovery in methods:
                print('|   Recovery code   |')
            if pyvolt.MFAMethod.totp in methods:
                print('|     TOTP code     |')
            print('---------------------')
            print("| Choose what you want to use. Choices: 'recovery', 'totp': ")
            method = input('> ').casefold()
            if method in ('recovery', 'recover'):
                code = input('Recovery code > ')
                resp = await resp.use_recovery_code(code)
            elif method in ('2fa', 'mfa', 'totp'):
                code = input('TOTP code > ')
                resp = await resp.use_totp(code)
            else:
                print("Invalid choice, available choices are: 'recovery', 'totp'", file=sys.stderr)
                sys.exit(1)

        if isinstance(resp, pyvolt.AccountDisabled):
            print('Account disabled. Your user ID is', resp.user_id)
            sys.exit(1)

        print('Logged in successfully! Here is session data:')
        print('Session ID:', resp.id)
        print('User ID:', resp.user_id)

        subscription = resp.subscription
        if subscription:
            print('You also have Web Push subscription:')
            print('> Endpoint:', subscription.endpoint)
            print('> P256DH:', subscription.p256dh)
            print('> Auth:', subscription.auth)

        print('Token:', resp.token)


def _login(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    asyncio.run(login(args.email, args.password, args.friendly_name))


def add_login_args(subparser: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparser.add_parser('login', help='log in to account')
    parser.set_defaults(func=_login)

    parser.add_argument('email', help='account email')
    parser.add_argument('password', help='account password')
    parser.add_argument('--friendly-name', nargs=1, required=False, help='device name')


def core(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.version:
        show_version()
    else:
        parser.print_help()


def parse_args() -> tuple[argparse.ArgumentParser, argparse.Namespace]:
    parser = argparse.ArgumentParser(prog='pyvolt', description='Tools for helping with pyvolt')
    parser.add_argument('-v', '--version', action='store_true', help='shows the library version')
    parser.set_defaults(func=core)

    subparser = parser.add_subparsers(dest='subcommand', title='subcommands')
    add_login_args(subparser)

    return parser, parser.parse_args()


def main() -> None:
    parser, args = parse_args()
    args.func(parser, args)


if __name__ == '__main__':
    main()
