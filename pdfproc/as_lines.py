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
    
    def get_page_data(self,dataset,verbose=False):
        header = self.get_header(dataset)
        start = header['end']
        header = self.get_header(dataset[header['end']:])
        end = start + header['start']
        if verbose: print(start,end)
        return dataset[start:end]
