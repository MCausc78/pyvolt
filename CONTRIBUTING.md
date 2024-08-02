## Contributing to pyvolt

First off, thanks for taking the time to contribute. It makes the library muuuuch better.

The following is a set of guidelines for contributing to the repository. These are guidelines, not hard rules.

## Submitting a Pull Request

Submitting a pull request is fairly simple, just make sure it focuses on a single aspect and doesn't manage to have scope creep and it's probably good to go. It would be incredibly lovely if the style is consistent to that found in the project. This project follows PEP-8 guidelines (mostly) with a column limit of 125.

### Git Commit Guidelines

- Use present tense (e.g. "Add feature" not "Added feature")
- Limit all lines to 72 characters or less.
- Reference issues or pull requests outside of the first line.
    - Please use the shorthand `#123` and not the full URL.
- Commits regarding the commands extension must be prefixed with `[commands]`

If you do not meet any of these guidelines, don't fret. Chances are they will be fixed upon rebasing but please do try to meet them to remove some of the workload.

### Code Style

Use following order in models:
```py
@define(slots=True)
class Foo(Base):
    # ... attrs properties
    # ... getters (``get_x``)
    # ... dunder methods (eq, hash, str), in alphabet order
    # ... internal methods (`_update`, `_react`)
    # ... properties
    # ... async methods, in alphabet order
    # ... methods
```