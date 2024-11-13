import re

class Inspector:
    ''' Probing tool for a dictionary of a pdf created by pymupdf '''

    def __init__(self,
                 key_block = 'blocks',
                 key_line = 'lines'):
        ''' Create a new pdf dictionary inspector instance '''
        self.key_block = key_block
        self.key_line = key_line

    def print_lines(self,text_block):
        ''' Print lines one by one '''
        for ln,line in enumerate(text_block[self.key_line]):
            print([ln,line['spans'][0]['text']])

    def print_blocks(self,page_text):
        ''' Print blocks one by one '''
        for bn,block in enumerate(page_text[self.key_block]):
            print(f"{self.key_block} ({bn})")
            self.print_lines(block[self.key_line])
            print()


class Extractor:
    ''' Extracting tool for a dictionary of a pdf crated by pymupdf '''

    def __init__(self,
                 re_id = '[0-9\\.\\-/A-Z]+',
                 re_separator = f"\\*+ [0-9\\.\\-/A-Z]+ \\*+",
                 re_page_end = '\\*+',
                 key_block = 'blocks',
                 key_line = 'lines'):
        ''' Create a new pdf dictionary extractor instance '''

        self.re_id = re_id
        self.re_separator = re_separator
        self.re_page_end = re_page_end
        self.key_block = key_block
        self.key_line = key_line

    def get_header(page_text):
        ''' UNDERBAKED tool for finding header in a US final assessment roll '''
        header_start = None
        for bn,block in enumerate(page_text[self.key_block]):
            for ln,line in enumerate(block[self.key_line]):
                line_text = line['spans'][0]['text']
                
                # Find first header line
                if 'TAX MAP PARCEL' in line_text:
                   header_start = (bn,ln)
                    
                # Find header end (first separator line)
                separator = re.search(
                    re_separator,
                    line_text
                )
                if header_start and separator:
                    header_end = (bn,ln)
                    return header_start, header_end

# Helper functions
import re as re

def find_line(entry,query):
    for bn,block in enumerate(entry):
        for ln,line in enumerate(block):
            temp = ' '.join(line.split())
            if query in temp: return bn,ln
    return 1

def normalize_data(entry):
    data = [[]]; n = 0; Skip = False
    for block in entry:
        for ln,line in enumerate(block):
            if Skip:
                Skip = False
                continue
            newline = re.search('[a-zA-Z ]+, [A-Z]{2} [0-9]{5}',line)
            if newline and ln > 0:
                print(f"Found a justification to jump the line: {newline.group()}")
                data.append([])
                n += 1; newline = None
                data[n].append(line)
                continue
            if ln < (len(block) - 1) and 'ACRES' in block[ln+1] and ln > 0:
                print(f"Found a justification to jump the line: {block[ln+1]}")
                data.append([])
                n += 1; newline = None
                data[n].append(line)
                continue
            if ln < (len(block) - 1) and 'FULL MARKET VALUE' in block[ln+1] and ln > 0:
                print(f"Found a justification to jump the line: {block[ln+1]}")
                data.append([])
                n += 1; newline = None
                data[n].append(line)
            newline = re.search('TAXABLE VALUE +?[0-9,]+',line)
            if newline and ln < (len(block) - 1):
                print(f"Found a justification to jump the line: {newline.group()}")
                data[n].append(line)
                data.append([])
                n += 1; newline = None
                continue
            newline = re.search('TAXABLE VALUE',line)
            if newline and ln < (len(block) - 2):
                print(ln, len(block) - 2)
                print(f"Found a justification to jump the line: {newline.group()}")
                data[n].append(block[ln+1])
                data.append([])
                n += 1; newline = None; Skip = True
            data[n].append(line)
        data.append([])
        n += 1
            
    return data
