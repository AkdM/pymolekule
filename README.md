<h1 align=center>
PyMolekule
<br />
<img alt="Package state" src="https://img.shields.io/badge/state-alpha-red">
<img alt="Version" src="https://img.shields.io/badge/version-0.0.2-green">
<img alt="Python version" src="https://img.shields.io/badge/python->=3.6-blue">
<br />
<img alt="License" src="https://img.shields.io/github/license/AkdM/PyMolekule">
<img alt="Github issues" src="https://img.shields.io/github/issues/AkdM/PyMolekule">
</h1>


## About Molekule

See [their official website](https://molekule.com).

## About PyMolekule

**PyMolekule** is a simple wrapper around the Molekule API, so that it is easy to connect, view and control your Molekule air purifier.

## Installation

*TODO*

## Usage

*TODO*

## Documentation

*WIP*, but [here](https://damota.me/pymolekule/)

## Generate Documentation

### To install:

- `pip install setuptools`
- `pip install mkdocs`
- `pip install mkdocs-material`
- `pip install novella`
- `pip install pydoc-markdown`

### Generate

A makefile is available to do multiple things:
- .PHONY: using `make` will defaults to `make clean build_docs`
- `clean`: cleans docs folder
- `build_docs`: build the docs using mkdocs
- `serve_docs`: live documentation. Useful when actively working on the documentation!
- `publish_docs`: publish the docs to the gh-pages branch

## Dependencies
- [requests](https://github.com/psf/requests)
- [boto3](https://github.com/boto/boto3)
- [pycognito](https://github.com/pvizeli/pycognito)
- [loguru](https://github.com/Delgan/loguru)
- [pyjwt](https://github.com/jpadilla/pyjwt)
- [pydantic](https://github.com/pydantic/pydantic)

## Author
- **Anthony Da Mota** [[Website](https://damota.me)] / [[Twitter](http://twitter.com/AkdM_)] / [[LinkedIn](http://linkedin.com/in/anthonydamota/)]


## Contributing
Contributions, issues and feature requests are welcome!<br />Feel free to check [issues page](https://github.com/AkdM/PyMolekule/issues). I should add a `CONTRIBUTING.md` file too.
## Show your support
Give a ⭐️ if this project helped you! If you're interested in donating you can [buy me a hot chocolate right here](https://www.buymeacoffee.com/AkdM)!

## License

This open source project is [GNU Affero General Public License v3.0](https://github.com/AkdM/PyMolekule/blob/main/LICENSE) licensed.
