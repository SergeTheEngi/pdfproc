import re
import copy

class Extractor:
    ''' Extracting tool for a pdf represented as a list of lines '''

    def __init__(self,
                 re_id = '[0-9\\.\\-/A-Z]+',
                 re_separator = f"\\*+ [0-9\\.\\-/A-Z]+ \\*+",
                 re_page_end = "\\*+",
                 re_hs = 'STATE OF NEW YORK|TAX MAP PARCEL'):
        ''' Cretate a new list of lines extractor instance '''

        self.re_id = re_id
        self.re_separator = re_separator
        self.re_page_end = re_page_end
        self.re_hs = re_hs

    def get_header(self,list_of_lines,verbose=False):
        ''' Find first header in the data '''
        header = {
            'start':None,
            'end':None
        }
        for ln,line in enumerate(list_of_lines):
            if bool(re.search(self.re_hs,line)) \
                and header['start'] == None:
                if verbose: print(line)
                header['start'] = ln
            elif bool(re.search(self.re_separator,line)) \
                and header['end'] == None \
                and header['start'] != None:
                if verbose: print(line)
                header['end'] = ln
            elif header['start'] != None and header['end'] != None:
                assert header['start'] != None
                assert header['end'] != None
                return header
        raise ValueError(f"Cannot find header")
    
    def get_page_data(self,list_of_lines,strip_lines=True,verbose=False):
        ''' Pass page data without header, returns dictionary of elements '''
        page_data = {}; harvest = False
        collect = False
        for line in list_of_lines:
            separator = None
            separator = re.fullmatch(self.re_separator,line)
            if separator:
                entry_id = re.search(self.re_id,separator.group()).group()
                page_data[entry_id] = [[]]
                harvest = True
            if harvest and bool(re.fullmatch(self.re_page_end,line)):
                harvest = False
                continue
            if harvest and strip_lines:
                page_data[entry_id].append(line.strip())
            elif harvest and not strip_lines:
                page_data[entry_id].append(line)
        if verbose: print(start,end)
        return page_data

    def get_data(self,source,verbose=True):
        ''' Extract entries from a poppler source '''
        failed = []
        entries = {}
        for i in range(source.pages):
            page = source.create_page(i)
            page_text = page.text()
            page_text = page_text.split('\n')
            try:
                header = self.get_header(page_text)
                entries.update(self.get_page_data(page_text[header['end']:]))
            except:
                failed.append(i+1) # Poppler indexes pages from 0
        if verbose:
            print(f"failed to extract {len(failed)} pages:\n{failed}")
        return entries

    def get_pages(self,list_of_lines,verbose=False):
        ''' Returns list of pages as lists of lines. '''

        # Find all formfeed characters
        formfeed_loc = []
        for ln,line in enumerate(dataset):
            if bool(re.search(b'\x0c',line)):
                formfeed_loc.append(ln)

        # Record pages
        pages = []
        prev_loc = None
        for loc in formfeed_loc:
            if prev_loc != None:
                pages.append(dataset[prev_loc:loc])
            else:
                pages.append(dataset[0:loc])
            prev_loc = loc

        return pages
