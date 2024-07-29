import os
import sys

if __name__ == '__main__':
    print('Hook ran')
    if sys.platform == 'win32':
        format_command = 'py -m ruff format pyvolt examples dev'
        check_command = 'py -m ruff check pyvolt examples dev'
    else:
        format_command = 'python -m ruff format pyvolt examples dev'
        check_command = 'python -m ruff check pyvolt examples dev'

    if os.system(format_command) == 0:
        if os.system(check_command) != 0:
            print(f'Linting failed, please run "{check_command} --fix" to fix them automatically.')
