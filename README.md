# argshell

Integrates the argparse and cmd modules to create custom shells with argparse functionality. 

## Installation

Install with:

<pre>
pip install argshell
</pre>



## Usage

Custom shells are created by subclassing the ArgShell class and adding functions of the form `do_*()`, just like the cmd.Cmd class.<br>

<pre>
class MyShell(argshell.ArgShell):
    def do_echo(self, line:str):
        """ Print command """
        print(line)
</pre>
Then create a function that instantiates an ArgShellParser instance, adds arguments, and then returns the ArgShellParser object
(similarly to how you would create a parser with argparse).
<pre>
def get_parser()->argshell.Namespace:
    parser = argshell.ArgShellParser()
    parser.add_argument("text", type=str, help="The text to print")
    parser.add_argument("-u", "--uppercase", action="store_true", help="Convert text to uppercase.")
    return parser
</pre>

For do_* functions that require args instead of just a string,
decorate the function with `with_parser()` and pass your function that creates and returns an ArgShellParser
instance to `with_parser` as a parameter.
<pre>
class MyShell(argshell.ArgShell):
    @argshell.with_parser(get_parser)
    def do_echo(self, args:argshell.Namespace):
        """ Print command """
        print(args.text.upper() if args.uppercase else args.text)
</pre>
In terminal:
<pre>
argshell>echo "howdy y'all"
howdy y'all
argshell>echo "howdy y'all" -u
HOWDY Y'ALL
</pre>

`with_parser` also accepts an optional list of functions that accept and return an argshell.Namespace object.<br>
These functions will be executed in order after the parser function parses the arguments.
<pre>
def toggle_uppercase(args: argshell.Namespace)->argshell.Namespace:
    """ If args.uppercase is True, make it False. If it's False, make it True."""
    args.uppercase = not args.uppercase
    return args

class MyShell(argshell.ArgShell):
    @argshell.with_parser(get_parser, [toggle_uppercase])
    def do_echo(self, args:argshell.Namespace):
        """ Print command """
        print(args.text.upper() if args.uppercase else args.text)
    
    @argshell.with_parser(get_parser, [toggle_uppercase, toggle_uppercase])
    def do_echo_double_toggle(self, args.argshell.Namespace):
        self.do_echo(args)
</pre>
In terminal:
<pre>
argshell>echo "howdy y'all"
HOWDY Y'ALL
argshell>echo "howdy y'all" -u
howdy y'all
argshell>echo_double_toggle "howdy y'all"
howdy y'all
argshell>echo_double_toggle "howdy y'all" -u
HOWDY Y'ALL
</pre>


When using your shell, entering `help command` will, in addition to the command's doc string,
print the help message of the parser that decorates it, if it is decorated.<br>
The parser help for a decorated command can also be printed by entering the command with the -h/--help flag.

### Example

A shell script that takes a list of first and last names and either prints a full name per line or prints first and last initials per line.

In a .py file:
<pre>
from argshell import ArgShell, ArgShellParser, Namespace, with_parser

def get_parser() -> ArgShellParser:
    parser = ArgShellParser(prog="")
    parser.add_argument(
        "names", type=str, nargs="*", help="A list of first and last names to print."
    )
    parser.add_argument(
        "-i", "--initials", action="store_true", help=""" Print initials only. """
    )
    return parser

# Post parser function to convert list of first and last names to a list of tuples of first and last names
def names_list_to_tuples(args: Namespace) -> Namespace:
    args.names = [
        (first, last) for first, last in zip(args.names[::2], args.names[1::2])
    ]
    if args.initials:
        args.names = [(name[0][0], name[1][0]) for name in args.names]
    return args

# Post parser function to capitalize names
def capitalize_names(args: Namespace) -> Namespace:
    args.names = [name.capitalize() for name in args.names]
    return args

class NameShell(ArgShell):
    intro = "Entering nameshell...\nType 'help' or '?' to list commands"
    prompt = "nameshell>"

    # Decorated command that gets a parser from get_parser
    # The parsed arguments will be processed by capititalize_names and then names_list_to_tuples
    # before being passed to do_printnames
    @with_parser(get_parser, [capitalize_names, names_list_to_tuples])
    def do_printnames(self, args: Namespace):
        """Print a list of first and last names, one per line."""
        print(*[f"{name[0]} {name[1]}" for name in args.names], sep="\n")

    # Undecorated command that behaves like a standard cmd.Cmd command function
    def do_echo(self, line: str):
        """Print the received text."""
        print(line)

if __name__ == "__main__":
    NameShell().cmdloop()
</pre>

Launch the file in a terminal:
<pre>
Entering nameshell...
Type 'help' or '?' to list commands
nameshell>help

Documented commands (type help <topic>):
========================================
echo  help  printnames  quit

nameshell>echo yeet
yeet
nameshell>printnames karl marx fred hampton emma goldman angela davis nestor makhno
Karl Marx
Fred Hampton
Emma Goldman
Angela Davis
Nestor Makhno
nameshell>printnames karl marx fred hampton emma goldman angela davis nestor makhno -i
K M
F H
E G
A D
N M
nameshell>help echo
Print the received text.
nameshell>help printnames
Print a list of first and last names, one per line.
Parser help for printnames:
usage: [-h] [-i] [names ...]

positional arguments:
  names           A list of first and last names to print.

options:
  -h, --help      show this help message and exit
  -i, --initials  Print initials only.
nameshell>printnames -h
usage: [-h] [-i] [names ...]

positional arguments:
  names           A list of first and last names to print.

options:
  -h, --help      show this help message and exit
  -i, --initials  Print initials only.
nameshell>quit
</pre>