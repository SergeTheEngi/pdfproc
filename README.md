# Current tasks

> Processing data as dict doesn't work with datasets like mamaroneck and greenburgh. Expect delays.

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
            - [ ] School
    - Additional:
        - [x] delim
        - [x] id
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
