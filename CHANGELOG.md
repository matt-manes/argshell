# Changelog

## 1.0.0 (2023-04-27)

#### Fixes

* fix double printing parser help for parsers with positional args
#### Performance improvements

* override cmdloop so shell doesn't exit on exception


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

* build v1.0.0
* update with_parser doc string


## v0.0.0 (2023-04-20)

#### Others

* change name in docstring