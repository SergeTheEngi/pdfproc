import re
import copy

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

    def get_header(self,page_text,verbose=False):
        ''' Tool for finding header in a US final assessment roll '''
        header_start = None
        if self.key_block not in page_text.keys():
            print(f"E: Page structure lacks '{self.key_block}'")
            return None,None
        for bn,block in enumerate(page_text[self.key_block]):
            if verbose:
                print(bn,type(block),end="")
                if type(block) == dict:
                    print(block.keys())
                else:
                    print()
            if self.key_line not in block.keys():
                print(f"E: Block structure lacks '{self.key_line}'")
                return None,None
            for ln,line in enumerate(block[self.key_line]):
                line_text = line['spans'][0]['text']
                
                # Find first header line
                if 'TAX MAP PARCEL' in line_text:
                   header_start = (bn,ln)
                    
                # Find header end (first separator line)
                separator = re.search(
                    self.re_separator,
                    line_text
                )
                if header_start and separator:
                    header_end = (bn,ln)
                    return header_start, header_end

        if header_start == None and separator == None:
            print("W: Failed to find header")
        elif header_start == None and separator != None:
            print("W: Failed to find header start")
        elif header_start != None and separator == None:
            print("W: Failed to find header end")
        return None,None
        

    def assemble_header(self, page_text, header_start, header_end):
        ''' Tool for assmebling header from a US final assessment roll '''
        header = []
        n = 0
        if header_start[0] == header_end[0]:
            header.append([])
            for line in page_text\
                    [self.key_block][header_start[0]][self.key_line]\
                    [header_start[1]:header_end[1]]:
                header[n].append(line['spans'][0]['text'])
            return header
        else:
            for bn in range(header_start[0],header_end[0]):
                header.append([])
                if bn == header_start[0]:
                    for ln in range(
                        header_start[1],
                        len(page_text[self.key_block][bn][self.key_line])
                    ):
                        header[n].append(page_text\
                                [self.key_block][bn][self.key_line][ln]\
                                ['spans'][0]['text'])
                elif bn > header_start[0] and bn < header_end[0]:
                    for line in page_text[self.key_block][bn][self.key_line]:
                        header[n].append(line['spans'][0]['text'])
                elif bn == header_end[0]:
                    for ln in range(header_end[1]):
                        header[n].append(page_text\
                                [self.key_block][bn][self.key_line][ln]\
                                ['spans'][0]['text'])
                else:
                    raise ValueError("How did you got here?")
                n += 1
            return header

# Helper functions
import re as re

def break_lines(entry):
    out = []
    for line in entry:
        out.append(re.split(' {2,}+',line))
    return out

def find_line(entry,query):
    for line in entry:
        temp = ' '.join(line)
        temp = ' '.join(temp.split())
        if query in temp: return temp
    return 1

def normalize_data(entry,verbose=False):
    data = [[]]; n = 0; Skip = False
    for block in entry:
        for ln,line in enumerate(block):
            if Skip:
                Skip = False
                continue
            newline = re.search('[a-zA-Z ]+, [A-Z]{2} [0-9]{5}',line)
            if newline and ln > 0:
                if verbose: print(f"Found a justification to jump the line: {newline.group()}")
                data.append([])
                n += 1; newline = None
                data[n].append(line)
                continue
            if ln < (len(block) - 1) and 'ACRES' in block[ln+1] and ln > 0:
                if verbose: print(f"Found a justification to jump the line: {block[ln+1]}")
                data.append([])
                n += 1; newline = None
                data[n].append(line)
                continue
            if ln < (len(block) - 1) and 'FULL MARKET VALUE' in block[ln+1] and ln > 0:
                if verbose: print(f"Found a justification to jump the line: {block[ln+1]}")
                data.append([])
                n += 1; newline = None
                data[n].append(line)
            newline = re.search('TAXABLE VALUE +?[0-9,]+',line)
            if newline and ln < (len(block) - 1):
                if verbose: print(f"Found a justification to jump the line: {newline.group()}")
                data[n].append(line)
                data.append([])
                n += 1; newline = None
                continue
            newline = re.search('TAXABLE VALUE',line)
            if newline and ln < (len(block) - 2):
                if verbose: print(ln, len(block) - 2)
                if verbose: print(f"Found a justification to jump the line: {newline.group()}")
                data[n].append(block[ln+1])
                data.append([])
                n += 1; newline = None; Skip = True
            data[n].append(line)
        data.append([])
        n += 1
            
    return data

def remove_spaces(string):
    string = re.sub( # Remove space groups
        r'\s{2,}',
        ' ',
        string
    )
    string = re.sub( # Remove trailing spaces
        r'(^\s+|\s+$)',
        '',
        string
    )
    return(string)

def unwrap_sublists(var:list):
    assert type(var) == list, "Input value must be a list"
    out = []
    for item in var:
        if type(item) != list:
            out.append(item)
        else:
            out.extend(item)
    return out

def unwrap_sublists_recursive(data_source,key):
    data = copy.deepcopy(data_source[key])
    go = True
    while go:
        if type(data) == list:
            data = unwrap_sublists(data)
            if not any(isinstance(i, list) for i in data):
                go = False
        else:
            print(f"{key} is not a list. Exiting")
            go = False
    return data
