import re
import copy

class Extractor:
    ''' Extracting tool for a pdf represented as a list of lines '''

    def __init__(self,
                 re_id = '[0-9\\.\\-/A-Z]+',
                 re_separator = f"\\*+ [0-9\\.\\-/A-Z]+ \\*+",
                 re_hs = 'STATE OF NEW YORK|TAX MAP PARCEL'):
        ''' Cretate a new list of lines extractor instance '''

        self.re_id = re_id
        self.re_separator = re_separator
        self.re_hs = re_hs

    def get_header(self,dataset,verbose=False):
        ''' Find first header in the data '''
        header = {
            'start':None,
            'end':None
        }
        for ln in range(len(dataset)):
            if bool(re.search(self.re_hs,dataset[ln])) \
                and header['start'] == None:
                if verbose: print(dataset[ln])
                header['start'] = ln
            elif bool(re.search(self.re_separator,dataset[ln])) \
                and header['end'] == None \
                and header['start'] != None:
                if verbose: print(dataset[ln])
                header['end'] = ln
            elif header['start'] != None and header['end'] != None:
                assert header['start'] != None
                assert header['end'] != None
                return header
    
    def get_page_data(self,dataset,strip_lines=True,verbose=False):
        page_data = {}; harvest = False
        collect = False
        for line in dataset:
            separator = None
            separator = re.search(self.re_separator,line)
            if separator:
                entry_id = re.search(self.re_id,separator.group()).group()
                page_data[entry_id] = [[]]
                harvest = True
            if harvest and strip_lines:
                page_data[entry_id].append(line.strip())
            elif harvest and not strip_lines:
                page_data[entry_id].append(line)
        if verbose: print(start,end)
        return page_data

    def get_pages(self,file,verbose=False):
        ''' Reads a file and returns list of pages as lists of lines.
        Input filename to read from. '''

        # Read file as list of binary strings, find all formfeed characters
        with open(file, 'br') as f:
            dataset = f.readlines()
        formfeed_loc = []
        for ln,line in enumerate(dataset):
            if bool(re.search(b'\x0c',line)):
                formfeed_loc.append(ln)

        # Read file as list of common strings, record pages
        with open(file, 'r') as f:
            dataset = f.readlines()

        pages = []
        prev_loc = None
        for loc in formfeed_loc:
            if prev_loc != None:
                pages.append(dataset[prev_loc:loc])
            else:
                pages.append(dataset[0:loc])
            prev_loc = loc

        return pages
