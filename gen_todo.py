from glob import glob
import re


def main():
    RE_TODO = re.compile(r"TODO: (.*)")

    todos = []
    for filename in glob("./pyvolt/**.py", recursive=True):
        with open(filename, "r") as fp:
            for line in fp:
                todos.extend(RE_TODO.findall(line))

    with open("TODO.md", "w") as todo_md:
        todo_md.write("# TODO\n\n")
        for todo in todos:
            todo_md.write(f"- {todo}\n")


if __name__ == "__main__":
    main()
