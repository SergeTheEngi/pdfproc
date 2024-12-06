# pdfproc

This is a toolset for processing final assessment roll data. Currently it is built on top of pymupdf, but it can be quickly adapted to use other pdf processing engines.

## State of the project

Currently this is in early beta. A ton of functionality haven't been expressed in the module yet and is scattered around in scripts.

Development goal right now is to create big enough codebase to be able to confidently process most pdfs. Upon noticing a somewhat reliable generic function I pack it into the module. So I'm just figuring out how to process specific datasets from the state of NY.

The module itself consists of submodules for processing data in different forms. Presently, `as_dict` is the most developed one. It processes data returned by pymupdf's `.get_text('dict')` function.

### How to use; Documentation

There are no documentation and barely any comments. I will add it once the module will get somewhat stable.

On the other hand, right now the project is pretty small. You probably can figure everything out yourself.

## Current tasks

> Processing data as dict doesn't work with datasets like mamaroneck and greenburgh. Expect delays.

- [x] Fix northcastle

Process Greenburgh:
- [x] Inspect the data
- [x] Find new data extraction method
    - pdftotext does the job?
- Collect data:
    - [x] Get headers
    - [x] Assemble headers
    - [x] Collect page data
        - New data layout: one block of line pieces
    - [x] Extract entries from pages
- Create new function to infer data from a randomly ordered list of lines:
    - Main elements:
        - [ ] Infer owner names
        - [ ] Infer owner address
        - [ ] Infer property type
        - [ ] Infer property address
        - [ ] Infer zoning
        - [x] Infer acreage
        - [ ] Infer market value
        - [ ] Infer taxables
            - [x] County
            - [x] Town
            - [x] School
    - Additional:
        - [x] delim
        - [x] id
        - [x] account
        - [x] village taxable
- [ ] Assemble output
- [ ] Review the data, fix the errors

- Mamaroneck:
    - Process data:
        - [ ] Access owner names
        - [ ] Access owner address
        - [x] Access property type
        - [x] Access property address
        - [x] Access zoning
        - [x] Access acreage
        - [x] Access market value
        - [x] Access taxables
