# pdfproc

This is a toolset for processing final assessment roll data. Currently it is built to work with pymupdf and poppler, but it can be quickly adapted to use other pdf processing engines.

## State of the project

Currently this is in early beta. A ton of functionality haven't been expressed in the module yet and is scattered around in scripts.

Development goal right now is to create a codebase big enough to confidently process most pdfs. Upon noticing a somewhat reliable generic function I pack it into the module. So I'm just figuring out how to process specific datasets from the state of NY.

The module itself consists of submodules for processing data in different forms. Presently, `as_dict` is the most developed one. It processes data returned by pymupdf's `.get_text('dict')` function.

### How to use; Documentation

There are no documentation and barely any comments. I will add it once the module will get somewhat stable.

On the other hand, right now the project is pretty small. You probably can figure everything out yourself.

### Dependencies

For python dependencies, see `requirements.txt`.

## Current tasks

Process Mamaroneck:
- Collect data:
    - [x] Get headers
    - [x] Collect page data
    - [x] Extract entries from pages
- Extract data:
    - [x] Access owner names
    - [x] Access owner address
    - [x] Access property type
    - [x] Access property address
    - [x] Access zoning
    - [ ] Access acreage
    - [ ] Access market value
    - [ ] Access taxables
