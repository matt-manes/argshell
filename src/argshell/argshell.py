import argparse
import cmd
import shlex
import sys
from functools import wraps
from typing import Any, Callable


class Namespace(argparse.Namespace):
    """Simple object for storing attributes.

    Implements equality by attribute names and values, and provides a simple string representation."""


class ArgShellParser(argparse.ArgumentParser):
    """***Overrides exit, error, and parse_args methods***

    Object for parsing command line strings into Python objects.

    Keyword Arguments:
        - prog -- The name of the program (default:
            ``os.path.basename(sys.argv[0])``)
        - usage -- A usage message (default: auto-generated from arguments)
        - description -- A description of what the program does
        - epilog -- Text following the argument descriptions
        - parents -- Parsers whose arguments should be copied into this one
        - formatter_class -- HelpFormatter class for printing help messages
        - prefix_chars -- Characters that prefix optional arguments
        - fromfile_prefix_chars -- Characters that prefix files containing
            additional arguments
        - argument_default -- The default value for all arguments
        - conflict_handler -- String indicating how to handle conflicts
        - add_help -- Add a -h/-help option
        - allow_abbrev -- Allow long options to be abbreviated unambiguously
        - exit_on_error -- Determines whether or not ArgumentParser exits with
            error info when an error occurs
    """

    def exit(self, status=0, message=None):
        """Override to prevent shell exit when passing -h/--help switches."""
        if message:
            self._print_message(message, sys.stderr)

    def error(self, message):
        raise Exception(f"prog: {self.prog}, message: {message}")

    def parse_args(self, *args, **kwargs) -> Namespace:
        parsed_args: Namespace = super().parse_args(*args, **kwargs)
        return parsed_args


class ArgShell(cmd.Cmd):
    """Subclass this to create custom ArgShells."""

    intro = "Entering argshell..."
    prompt = "argshell>"

    def do_quit(self, command: str):
        """Quit shell."""
        return True

    def do_help(self, arg):
        """List available commands with "help" or detailed help with "help cmd".
        If using 'help cmd' and the cmd is decorated with a parser, the parser help will also be printed."""
        if arg:
            # XXX check arg syntax
            try:
                func = getattr(self, "help_" + arg)
            except AttributeError:
                try:
                    func = getattr(self, "do_" + arg)
                    doc = func.__doc__
                    if doc:
                        self.stdout.write("%s\n" % str(doc))
                    # Check for decorator and call decorated function with "--help"
                    if hasattr(func, "__wrapped__"):
                        self.stdout.write(
                            f"Parser help for {func.__name__.replace('do_','')}:\n"
                        )
                        func("--help")
                    if doc or hasattr(func, "__wrapped__"):
                        return
                except AttributeError:
                    pass
                self.stdout.write("%s\n" % str(self.nohelp % (arg,)))
                return
            func()
        else:
            names = self.get_names()
            cmds_doc = []
            cmds_undoc = []
            topics = set()
            for name in names:
                if name[:5] == "help_":
                    topics.add(name[5:])
            names.sort()
            # There can be duplicates if routines overridden
            prevname = ""
            for name in names:
                if name[:3] == "do_":
                    if name == prevname:
                        continue
                    prevname = name
                    cmd = name[3:]
                    if cmd in topics:
                        cmds_doc.append(cmd)
                        topics.remove(cmd)
                    elif getattr(self, name).__doc__:
                        cmds_doc.append(cmd)
                    else:
                        cmds_undoc.append(cmd)
            self.stdout.write("%s\n" % str(self.doc_leader))
            self.print_topics(self.doc_header, cmds_doc, 15, 80)
            self.print_topics(self.misc_header, sorted(topics), 15, 80)
            self.print_topics(self.undoc_header, cmds_undoc, 15, 80)


def with_parser(
    parser: Callable[..., ArgShellParser],
    post_parsers: list[Callable[[Namespace], Namespace]] = [],
) -> Callable[[Callable[[Any, Namespace], Any]], Callable[[Any, str], Any]]:
    """Decorate a 'do_*' function in an argshell.ArgShell class with this function to pass an argshell.Namespace object to the decorated function instead of a string.

    :param parser: A function that creates an argshell.ArgShellParser instance, adds arguments to it, and returns the parser.

    :param post_parsers: An optional list of functions to execute where each function takes an argshell.Namespace instance and returns an argshell.Namespace instance.
        'post_parser' functions are executed in the order they are supplied.

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
            try:
                args = parser().parse_args(shlex.split(command))
            except Exception as e:
                # On parser error, print help and skip post_parser and func execution
                print(e)
                command = "--help"
                # Parsers with required positional arguments will crash shell
                # without wrapping this in a try/except
                try:
                    args = parser().parse_args(shlex.split(command))
                except Exception as e:
                    ...
                return None
            # Don't execute function, only print parser help
            if "-h" in command or "--help" in command:
                return None
            for post_parser in post_parsers:
                args = post_parser(args)

            return func(self, args)

        return inner

    return decorator
