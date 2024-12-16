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
    ''' Extracting tool for a dictionary created by pymupdf '''

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
        ''' TODO: rewrite get_header to use actual errors instead of printing bs in my tty '''
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
                if verbose:
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

        if verbose:
            if header_start == None and separator == None:
                print("W: Failed to find header")
            elif header_start == None and separator != None:
                print("W: Failed to find header start")
            elif header_start != None and separator == None:
                print("W: Failed to find header end")
        return None,None
        

    def assemble_header(self,page_text,header_start,header_end):
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

    def get_page_data(self,page_text,header_end,strip_lines=True):
        page_data = {}; n = 0; harvest = False
        for bn,block in enumerate(page_text[self.key_block][header_end[0]:]):
            for line in block[self.key_line]:
                line_text = line['spans'][0]['text']
                separator = re.search(
                    self.re_separator,
                    line_text
                )
                if separator:
                    entry_id=re.search(self.re_id,separator.group()).group()
                    page_data[entry_id] = [[]]
                    harvest = True
                    n = 0
                else:
                    page_end = re.search(
                        self.re_page_end,
                        line_text
                    )
                    if page_end: return page_data
                if harvest and strip_lines:
                    page_data[entry_id][n].append(line_text.strip())
                elif harvest and not strip_lines:
                    page_data[entry_id][n].append(line_text)
            if harvest: page_data[entry_id].append([])
            n += 1

    def get_data(self,args:list):
        '''
        Input list of argument dictionaries containing arguments for the worker
        function as:
        ```
        {'source':dataset, 'name':'dataset_name', 'columns':['col1','col2']}`
        ```
        Input datasets are final assessment roll pdfs:
        `dataset = pymupdf.open('myfa.pdf')`

        Returns dictionary of extracted datasets as {'dataset_name':dataset}
        Returned dataset is a dictionary of raw entries. Each entry is a list
        of blocks. Each block is a list of lines in whatever arrangement it is
        in the pdf:
        ```
        dataset = {
            'id':[ # Entry level
                [ # Block level
                    'text is here','another piece of text'
                ],
                ['This is the second block, but it contains only one line']
            ]
        }
        ```

        Sometimes line displayed in a pdf structurally is a block, sometimes
        entry consists of a single block, and each line in the block is an
        actual line.
        '''
        import multiprocessing
        
        def worker(q,
                   source,
                   name,
                   from_page=0,
                   columns=None,
                   strip_lines=True,
                   verbose=False,
                   print_failed=True):
            data = {}
            failed = []
            
            for p in range(from_page,source.page_count):
                page = source.load_page(p)
                page_text = page.get_text('dict')
            
                hs,he = self.get_header(page_text)
            
                if hs != None and he != None:
                    page_data = self.get_page_data(page_text,he,strip_lines)
                    if verbose: print("page",p,page_data.keys())
                    if columns != None:
                        header = self.assemble_header(page_text,hs,he)
                        column_positions = get_columns(header,columns)
                        for id in page_data:
                            data[id] = {
                                'data':page_data[id],
                                'columns':column_positions
                            }
                    else:
                        for id in page_data:
                            data[id] = page_data[id]
                else:
                    failed.append(p+1)
                    if verbose: print("page",p)

                
            if print_failed: print("failed to find headers:",failed)
            q.put((data,name))

        with multiprocessing.Manager() as manager:
            q = manager.Queue()
            processes = []
            results = {}

            for item in args:
                arguments = {'q':q}
                arguments.update(item)
                p = multiprocessing.Process(
                        target=worker,
                        kwargs=arguments
                )
                p.start()
                processes.append(p)

            for p in processes:
                p.join()

            while not q.empty():
                result,key = q.get()
                results[key] = result

            # TODO: Doesn't work. Why?
            #q.close()
        
        return results

    def get_generic(self,entry,pattern,verbose=False):
        entry = copy.deepcopy(entry)
        for line in entry:
            result = None
            if type(line) == list:
                line = ' '.join(line)
            result = re.search(pattern,line)
            if result != None:
                return result.group()
            elif verbose:
                print(line)
        raise ValueError(f"Cannot find '{pattern}'")

    def get_owner_names(self,entry,key,verbose=False):
        ''' Pass entry as list of strings from an appropriate column'''
        entry = list(filter(None,entry))
        try:
            entry_id = max([i for i,item in enumerate(entry) if key in item])
        except:
            # If there is no key, print a warning and take the best guess
            if verbose: print(f"WARN: {key} has no entry id in the first column")
            entry_id = 2
        owner_names = []
        for item in entry[entry_id + 1:-2]:
            owner_names.append(item.strip())
        for item in entry[-2:]:
            company = re.search('(l ?l ?c)|(L ?L ?C)',item)
            if company:
                owner_names.append(item.strip())
                company = None
        return owner_names
    
    def get_owner_address(self,entry,key=None):
        ''' Pass entry as list of strings from an appropriate column '''
        company = None
        entry = list(filter(None,entry))
        owner_addr = entry[-2:]
        for i,name in enumerate(owner_addr):
            if '   ' in owner_addr[i]:
                owner_addr[i] = name.split('   ')[0]
        out = []
        for name in owner_addr:
            if name == key: continue
            else: out.append(' '.join(name.split()))
        return ', '.join(out)


# Helper functions
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

def get_columns(header,columns:list):
    ''' Pass an extracted header (as a list of blocks containing a single block
    with actual lines) and list of column patterns to look for, and it return
    their starting positions'''
    assert len(header) == 1, "Header length is not 1"
    positions = {}
    for line in header[0]:
        for pattern in columns:
            pos = line.find(pattern)
            if pos == -1: continue
            else: positions[pattern] = pos
    diff = set(columns).symmetric_difference(set(positions))
    assert len(diff) == 0, f"Failed to find columns: {list(diff)}"
    return positions

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

def unwrap_sublists_recursive(entry):
    data = copy.deepcopy(entry)
    go = True
    while go:
        if type(data) == list:
            data = unwrap_sublists(data)
            if not any(isinstance(i, list) for i in data):
                go = False
        else:
            print("Entry is not a list. Exiting")
            go = False
    return data
