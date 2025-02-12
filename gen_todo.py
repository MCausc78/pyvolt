from glob import glob
import re
import subprocess
import sys


def get_branch() -> str:
    proc = subprocess.run("git status", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc.check_returncode()

    RE_BRANCH = re.compile(rb"On branch ([0-9A-Za-z/]+)\n", re.MULTILINE)

    match = RE_BRANCH.search(proc.stdout)
    if match is None:
        print(f"Unable to get Git branch! Stdout:")
        sys.stdout.write(proc.stdout.decode())
        sys.exit(1)

    return match.group(1).decode()

def get_latest_commit():
    proc = subprocess.run("git log -n1 --format=%H", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc.check_returncode()
    return proc.stdout.decode().strip()


def main():
    commit = get_latest_commit()

    RE_TODO = re.compile(r"TODO: (.*)")

    todos = {}
    for filename in glob("./pyvolt/**.py", recursive=True):
        with open(filename, "r") as fp:
            todos.setdefault(filename, [])
            for i, line in enumerate(fp):
                match = RE_TODO.search(line)
                if match:
                    span = match.span()
                    span = (span[0] + 1, min(len(line), span[1] + 1))

                    todos[filename].append((i + 1, span, match[0]))

    with open("TODO.md", "w") as todo_md:
        todo_md.write("# TODO\n\n")
        for file, items in todos.items():
            if not items:
                continue

            for item in items:
                file = file[file.find("pyvolt") :].replace("\\", "/")
                span = item[1]
                fragment = f"L{item[0]}C{span[0]}-L{item[0]}C{span[1]}"
                todo_md.write(
                    f"* {item[2]}\n\n"
                    f"  Source: https://github.com/MCausc78/pyvolt/blob/{commit}/{file}#{fragment}\n\n"
                )


if __name__ == "__main__":
    main()
