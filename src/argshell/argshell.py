import argparse
import cmd
import inspect
import os
import shlex
import subprocess
import sys
import traceback
from functools import wraps
from typing import Any, Callable, Generator, Sequence

import colorama
import rich.terminal_theme
import rich_argparse
from pathier import Pathier
from printbuddies import RGB, Gradient
from rich.console import Console
from rich.rule import Rule
from rich_argparse import (
    ArgumentDefaultsRichHelpFormatter,
    HelpPreviewAction,
    MetavarTypeRichHelpFormatter,
    RawDescriptionRichHelpFormatter,
)

colorama.init()
argshell_console = Console(style="pink1")


class ArgShellHelpFormatter(
    RawDescriptionRichHelpFormatter,
    MetavarTypeRichHelpFormatter,
    ArgumentDefaultsRichHelpFormatter,
):
    """ """

    def __init__(
        self,
        prog: str,
        indent_increment: int = 2,
        max_help_position: int = 24,
        width: int | None = None,
        console: Console | None = None,
    ) -> None:
        super().__init__(prog, indent_increment, max_help_position, width, console)
        self._console = argshell_console

    def format_help(self) -> str:
        with self.console.capture() as capture:
            self.console.print(
                self,
                crop=False,
                style="turquoise2",
            )
        return rich_argparse._fix_legacy_win_text(self.console, capture.get())  # type: ignore


ArgShellHelpFormatter.styles |= {
    "argparse.args": "deep_pink1",
    "argparse.groups": "sea_green1",
    "argparse.help": "pink1",
    "argparse.text": "turquoise2",
    "argparse.prog": (RGB(name="sea_green2") - RGB(50, 0, 50)).as_style(),
    "argparse.metavar": (RGB(name="turquoise2") * 0.7).as_style(),
    "argparse.syntax": "orchid1",
    "argparse.default": "cornflower_blue",
}


class Namespace(argparse.Namespace):
    """Simple object for storing attributes.

    Implements equality by attribute names and values, and provides a simple string representation.
    """


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

    def __init__(
        self,
        prog: str | None = None,
        usage: str | None = None,
        description: str | None = None,
        epilog: str | None = None,
        parents: Sequence[argparse.ArgumentParser] = [],
        formatter_class: argparse.HelpFormatter = ArgShellHelpFormatter,  # type: ignore
        prefix_chars: str = "-",
        fromfile_prefix_chars: str | None = None,
        argument_default: Any = None,
        conflict_handler: str = "error",
        add_help: bool = True,
        allow_abbrev: bool = True,
        exit_on_error: bool = True,
    ) -> None:
        super().__init__(
            prog,
            usage,
            description,
            epilog,
            parents,
            formatter_class,  # type: ignore
            prefix_chars,
            fromfile_prefix_chars,
            argument_default,
            conflict_handler,
            add_help,
            allow_abbrev,
            exit_on_error,
        )

    def add_help_preview(self, path: str = "cli_help.svg"):
        """Add a `--generate-help-preview` switch for generating an `.svg` of this parser's help command."""
        if not path.endswith((".svg", ".SVG")):
            raise ValueError(f"`{path}` is not a `.svg` file path.")

        self.add_argument(
            "--generate-help-preview",
            action=HelpPreviewAction,
            path=path,
            export_kwds={"theme": rich.terminal_theme.MONOKAI},
        )

    def exit(self, status: int = 0, message: str | None = None):  # type: ignore
        """Override to prevent shell exit when passing -h/--help switches."""
        if message:
            self._print_message(message, sys.stderr)

    def error(self, message: str):
        raise Exception(f"prog: {self.prog}, message: {message}")

    def parse_args(self, *args: Any, **kwargs: Any) -> Namespace:
        parsed_args: Namespace = super().parse_args(*args, **kwargs)
        return parsed_args


def get_shell_docs_parser() -> ArgShellParser:
    parser = ArgShellParser(
        prog="shell_docs",
        description="""Generate `.svg` files for this shell's command list.
                            The font size is proportional to the terminal width when this command is executed.""",
    )
    parser.add_argument(
        "path",
        nargs="?",
        type=str,
        default="shell_docs.svg",
        help=""" The base file path to save the svg to.""",
    )
    parser.add_argument(
        "-i",
        "--individual",
        action="store_true",
        help=""" 
    Save each command as a separate `.svg` instead of one continuous one.
    Each file be saved as `{base_file_stem}_{command}.svg`""",
    )
    parser.add_help_preview("shell_doc_help.svg")
    return parser


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
                if "the following arguments are required" not in str(e):
                    print(f"ERROR: {e}")
                if "-h" not in command and "--help" not in command:
                    try:
                        args = parser().parse_args(["--help"])
                    except Exception as e:
                        pass
                return None
            # Don't execute function, only print parser help
            if "-h" in command or "--help" in command:
                return None
            for post_parser in post_parsers:
                args = post_parser(args)

            return func(self, args)

        return inner

    return decorator


class ArgShell(cmd.Cmd):
    """Subclass this to create custom ArgShells."""

    intro = "Entering argshell..."
    prompt = "argshell>"
    console = argshell_console

    def do_quit(self, _: str) -> bool:
        """Quit shell."""
        return True

    def do_sys(self, command: str):
        """Execute command with `os.system()`."""
        os.system(command)

    def do_reload(self, _: str):
        """Reload this shell."""
        source_file = inspect.getsourcefile(type(self))
        if not source_file:
            raise FileNotFoundError(
                "Can't reload shell, this source file could not be found (somehow...)"
            )
        subprocess.run([sys.executable, source_file])
        sys.exit()

    def do_capture(self, arg: str):
        """
        Prepend any of this shell's commands with `capture` to save the execution output to `{command}.svg`.
        (Note: Only captures output printed with this instance's `self.console.print`.)
        e.g.
        >>> argshell> capture help

        will save the output of the `help` command to `help.svg`.
        """
        command = arg.split()[0].strip('"')
        self.console.record = True
        arg_ = arg.replace('"', "")
        self.console.print(f"{self.prompt} {arg_}")
        getattr(self, f"do_{command}")(" ".join(arg.split()[1:]))
        self.console.save_svg(
            f"{command}.svg",
            title=f"{command}",
            theme=rich.terminal_theme.MONOKAI,
        )
        self.console.record = False

    def get_commands(self) -> dict[str, list[str]]:
        """
        Returns the following dictionary for this instance:
          {
              "cmds_doc": list[documented commands],
              "topics": list[topics],
              "cmds_undoc": list[undocumented commands]
          }
        """
        names = self.get_names()
        cmds_doc: list[str] = []
        cmds_undoc: list[str] = []
        topics: set[str] = set()
        for name in names:
            if name[:5] == "help_":
                topics.add(name[5:])
        names.sort()
        # There can be duplicates if routines overridden
        prevname = ""
        for name in names:
            if name[:3] == "do_":
                if name == prevname or name == "do_shell_docs":
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
        return {
            "cmds_doc": cmds_doc,
            "topics": sorted(topics),
            "cmds_undoc": cmds_undoc,
        }

    @with_parser(get_shell_docs_parser)
    def do_shell_docs(self, args: Namespace):
        """Generate documentation as an `.svg` for this shell's commands."""
        base_path = Pathier(args.path)
        base_path.parent.mkdir()

        def save(title: str):
            self.console.save_svg(
                str(base_path.with_stem(f"{base_path.stem}_{title}")),
                title=title,
                theme=rich.terminal_theme.MONOKAI,
            )

        commands = self.get_commands()
        self.console.record = True
        self.print_commands(commands)
        title = self.__class__.__name__
        if args.individual:
            save(title)
        all_commands: list[str] = []
        for value in commands.values():
            all_commands.extend(value)
        for command in all_commands:
            self.console.print(Rule(style="deep_pink1"))
            self.console.print(f"[pink1]{self.prompt} {command}")
            self.console.print()
            self.console.print(f"[sea_green1]{title}::{command}")
            self.do_help(command)
            self.console.print("")
            if args.individual:
                save(command)
        self.console.record = False
        if not args.individual:
            self.console.save_svg(
                str(base_path), title=title, theme=rich.terminal_theme.MONOKAI
            )
            self.console.print(f"Documentation saved to `{base_path}`.")
        else:
            self.console.print(f"Documentation saved in `{base_path.parent}`.")

    def print_commands(self, commands: dict[str, list[str]]):
        """Display formatted help list for `commands`.
        `commands` should be:
        {
            "cmds_doc": list[documented commands],
            "topics": list[topics],
            "cmds_undoc": list[undocumented commands]
        }"""
        self.console.print(f"[turquoise2]{self.doc_leader}")
        self.print_topics(self.doc_header, commands["cmds_doc"], 15, 80)
        self.print_topics(self.misc_header, commands["topics"], 15, 80)
        self.print_topics(self.undoc_header, commands["cmds_undoc"], 15, 80)

    def do_help(self, arg: str):
        """
        List available commands with "help" or detailed help with "help cmd".
        If using 'help cmd' and the cmd is decorated with a parser, the parser help will also be printed.
        """
        if arg:
            # XXX check arg syntax
            try:
                func = getattr(self, "help_" + arg)
            except AttributeError:
                try:
                    func = getattr(self, "do_" + arg)
                    doc = func.__doc__
                    if doc:
                        lines = [line.strip() for line in doc.splitlines()]
                        colors = Gradient().get_sequence(len(lines))
                        doc = "\n".join(
                            f"{color}{line}[/]"
                            for color, line in zip(colors[::-1], lines)
                        )
                        self.console.print(f"[turquoise2]{doc}")
                    # Check for decorator and call decorated function with "--help"
                    if hasattr(func, "__wrapped__"):
                        self.console.print(
                            f"[pink1]Parser help for [deep_pink1]{func.__name__.replace('do_','')}"
                        )
                        func("--help")
                    if doc or hasattr(func, "__wrapped__"):
                        return
                except AttributeError:
                    pass
                self.console.print(f"[pink1]{self.nohelp % (f'[turquoise2]{arg}',)}")
                return
            func()
        else:
            commands = self.get_commands()
            self.print_commands(commands)

    def print_topics(
        self, header: str, cmds: list[str] | None, cmdlen: int, maxcol: int
    ):
        if cmds:
            self.console.print(f"[sea_green1]{header}")
            if self.ruler:
                self.console.print(f"[deep_pink1]{self.ruler * len(header)}")
            self.columnize(cmds, maxcol - 1)

    def columnize(self, list_: list[str] | None, displaywidth: int = 80):  # type: ignore
        """Display a list of strings as a compact set of columns.

        Each column is only as wide as necessary.
        Columns are separated by two spaces (one was not legible enough).
        """
        if not list_:
            self.console.print(f"[bright_red]<empty>")
            return

        nonstrings = [i for i in range(len(list_)) if not isinstance(list_[i], str)]  # type: ignore
        if nonstrings:
            raise TypeError(
                "list[i] not a string for i in %s" % ", ".join(map(str, nonstrings))
            )
        size = len(list_)
        if size == 1:
            self.console.print(f"[turquoise2]{list_[0]}")
            return

        def get_color() -> Generator[RGB, Any, Any]:
            colors = Gradient(["turquoise2", "pink1"]).get_sequence(size)
            for color in colors:
                yield color

        colors = get_color()
        # Try every row count from 1 upwards
        for nrows in range(1, len(list_)):
            ncols = (size + nrows - 1) // nrows
            colwidths: list[int] = []
            totwidth = -2
            for col in range(ncols):
                colwidth = 0
                for row in range(nrows):
                    i = row + nrows * col
                    if i >= size:
                        break
                    x = list_[i]
                    colwidth = max(colwidth, len(x))
                colwidths.append(colwidth)
                totwidth += colwidth + 2
                if totwidth > displaywidth:
                    break
            if totwidth <= displaywidth:
                break
        else:
            nrows = len(list_)
            ncols = 1
            colwidths = [0]
        for row in range(nrows):
            texts: list[str] = []
            for col in range(ncols):
                i = row + nrows * col
                if i >= size:
                    x = ""
                else:
                    x = list_[i]
                texts.append(x)
            while texts and not texts[-1]:
                del texts[-1]
            for col in range(len(texts)):
                texts[col] = texts[col].ljust(colwidths[col])
            self.console.print("  ".join(f"{next(colors)}{text}" for text in texts))

    def cmdloop(self, intro: str | None = None):
        """Repeatedly issue a prompt, accept input, parse an initial prefix
        off the received input, and dispatch to action methods, passing them
        the remainder of the line as argument."""

        self.preloop()
        if self.use_rawinput and self.completekey:
            try:
                import readline

                self.old_completer = readline.get_completer()  # type: ignore
                readline.set_completer(self.complete)  # type: ignore
                readline.parse_and_bind(self.completekey + ": complete")  # type: ignore
            except ImportError:
                pass
        try:
            if intro is not None:
                self.intro = intro
            if self.intro:
                self.console.print(f"[turquoise2]{self.intro}\n")
            stop = None
            while not stop:
                if self.cmdqueue:
                    line = self.cmdqueue.pop(0)
                else:
                    if self.use_rawinput:
                        try:
                            line = self.console.input(f"[deep_pink1]{self.prompt}")
                        except EOFError:
                            line = "EOF"
                    else:
                        self.console.print(f"[deep_pink1]{self.prompt}")
                        self.stdout.flush()
                        line = self.stdin.readline()
                        if not len(line):
                            line = "EOF"
                        else:
                            line = line.rstrip("\r\n")
                # ===========Modification start===========
                try:
                    line = self.precmd(line)
                    stop = self.onecmd(line)
                    stop = self.postcmd(stop, line)
                except Exception as e:
                    traceback.print_exc()
                # ===========Modification stop===========
            self.postloop()
        finally:
            if self.use_rawinput and self.completekey:
                try:
                    import readline

                    readline.set_completer(self.old_completer)  # type: ignore
                except ImportError:
                    pass

    def emptyline(self):  # type: ignore
        ...
