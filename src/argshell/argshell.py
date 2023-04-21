import argparse
import cmd
import shlex
import sys
from functools import wraps
from typing import Any, Callable


class Namespace(argparse.Namespace):
    """Wrapping argparse.Namesapce for convenience."""


class ArgShellParser(argparse.ArgumentParser):
    """Wrapping argparse.ArgumentParser for convenience
    and to prevent exit on '-h/--help' switch."""

    def exit(self, status=0, message=None):
        """Override to prevent shell exit when passing -h/--help switches."""
        if message:
            self._print_message(message, sys.stderr)

    def parse_args(self, *args, **kwargs) -> Namespace:
        """Just making the type checker hush."""
        parsed_args: Namespace = super().parse_args(*args, **kwargs)
        return parsed_args


class ArgShell(cmd.Cmd):
    intro = "Entering argshell..."
    prompt = "argshell>"

    def do_quit(self, command: str):
        """Quit shell"""
        return True


def with_parser(
    parser: Callable[..., ArgShellParser],
    post_parsers: list[Callable[[Namespace], Namespace]] = [],
) -> Callable[[Callable[[Any, Namespace], Any]], Callable[[Any, str], Any]]:
    """Decorate a 'do_*' function in an argshell.ArgShell class with this function to pass an argshell.Namespace object to the decorated function instead of a string.

    :param parser: A function that creates an argshell.ArgShellParser instance, adds arguments to it, and returns the parser.

    :param post_parsers: An optional list of functions to execute where each function takes an argshell.Namespace instance and returns an argshell.Namespace instance.
        Functions are executed in the order they are supplied.

    >>> def get_parser() -> argshell.ArgShellParser:
    >>>     parser = argshell.ArgShellParser()
    >>>     parser.add_argument("names", type=str, nargs="*", help="A list of first and last names to print.")
    >>>     parser.add_argument("-i", "--initials", action="store_true", help="Print the initials instead of the full name.")
    >>>     return parser
    >>>
    >>> # Convert list of first and last names to a list of tuples
    >>> def names_list_to_tuples(args: argshell.Namespace) -> argshell.Namespace:
    >>>     args.names = [(first, last) for first, last in zip(args.names[::2], args.names[1::2])]
    >>>     if args.initials:
    >>>         args.names = [(name[0][0], name[1][0]) for name in args.names]
    >>>     return args
    >>>
    >>> def capitalize_names(args: argshell.Namespace) -> argshell.Namespace:
    >>>     args.names = [name.capitalize() for name in args.names]
    >>>     return args
    >>>
    >>> class NameShell(ArgShell):
    >>>     intro = "Entering nameshell..."
    >>>     prompt = "nameshell>"
    >>>
    >>>     @with_parser(get_parser, [capitalize_names, names_list_to_tuples])
    >>>     def do_printnames(self, args: argshell.Namespace):
    >>>         print(*[f"{name[0]} {name[1]}" for name in args.names], sep="\\n")
    >>>
    >>> NameShell().cmdloop()
    >>> Entering nameshell...
    >>> nameshell>printnames karl marx fred hampton emma goldman angela davis nestor makhno
    >>> Karl Marx
    >>> Fred Hampton
    >>> Emma Goldman
    >>> Angela Davis
    >>> Nestor Makhno
    >>> nameshell>printnames karl marx fred hampton emma goldman angela davis nestor makhno -i
    >>> K M
    >>> F H
    >>> E G
    >>> A D
    >>> N M"""

    def decorator(
        func: Callable[[Any, Namespace], Any | None]
    ) -> Callable[[Any, str], Any]:
        @wraps(func)
        def inner(self: Any, command: str) -> Any:
            args = parser().parse_args(shlex.split(command))
            for post_parser in post_parsers:
                args = post_parser(args)
            return func(self, args)

        return inner

    return decorator
