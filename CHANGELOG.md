# Changelog

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