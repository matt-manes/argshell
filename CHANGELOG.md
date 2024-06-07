# Changelog

## v1.6.4 (2024-06-06)

#### Fixes

* fix parser function not being called if `-h` is part of the command

## v1.6.3 (2024-02-24)

#### Fixes

* fix shell_docs parser description formatting

## v1.6.2 (2024-02-24)

#### Performance improvements

* when passing a parser to `with_parser`, the `prog` attribute will be set to the name of the decorated function

#### Docs

* increase font size of svgs

## v1.6.1 (2024-02-24)

#### Others

* add 'assets' to sdist excludes

## v1.6.0 (2024-02-23)

#### New Features

* implement command documentation generation

#### Fixes

* prevent missing required args message when using `-h/--help`

#### Refactorings

* change `ArgshellParser` inheritance

#### Docs

* rewrite readme

## v1.5.1 (2024-02-22)

#### Refactorings

* use gradient when displaying command list

## v1.5.0 (2024-02-22)

#### New Features

* implement `rich` based help formatter

#### Others

* move type ignore comment after formatting goofed it up

## v1.4.1 (2024-02-16)

#### Refactorings

* improve type annotation coverage

## v1.4.0 (2024-01-26)

#### New Features

* add reload command

#### Docs

* add missing version prefix

## v1.3.0 (2023-05-03)

#### New Features

* override emptyline so previous command isn't repeated

## v1.2.0 (2023-05-02)

#### New Features

* add do_sys command to built in commands

#### Others

* build v1.2.0
* update changelog

## v1.1.0 (2023-04-27)

#### Fixes

* fix double printing parser help for parsers with positional args

#### Performance improvements

* override cmdloop so shell doesn't exit on exception

#### Others

* build v1.1.0

## v1.0.0 (2023-04-23)

#### New Features

* print parser help and block decorated function execution on parser error
* print parser help when using 'help cmd' if cmd function is decorated

#### Fixes

* fix crash when printing parser help for parser with required positional args
* prevent false *** No help message on undecorated help cmd
* don't execute decorated function when -h/--help is passed to parser

#### Refactorings

* better type checker appeasement

#### Docs

* write readme
* update docstrings

#### Others

* test build
* build v1.0.0
* update with_parser doc string

## v0.0.0 (2023-04-20)

#### Others

* change name in docstring
