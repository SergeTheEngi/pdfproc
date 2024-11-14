#!/usr/bin/env python
# coding: utf-8

# In[193]:


import time

import pymupdf
import re
import copy
from openpyxl import Workbook
from pdfproc.as_dict import find_line,normalize_data

bronxville = pymupdf.open('pdfproc/testing_data:2024FA_Bronxville.pdf')
cornwall = pymupdf.open('Cornwall Assessment Final Roll 2024.pdf')


# In[6]:


# Inspect the data
page = cornwall.load_page(0)
page_text = page.get_text('dict')


#for block in page_text['blocks']:
#    for line in block['lines']:
#        print(line['spans'][0]['text'])

header_start,header_end = get_header(page_text)
header = assemble_header(page_text, header_start, header_end)

print(header)


# ## Extracting the data
# 
# ### Splitting by text field location
# 
# Get header location by block and line number, assemble it into a new list of the same shape.

# In[7]:


re_id = '[0-9\\.\\-/A-Z]+'
re_separator = f"\\*+ ?{re_id} ?\\*+"
re_page_end = '\\*+'


# In[8]:


def get_header(page_text,verbose=False):
    header_start = None
    for bn,block in enumerate(page_text['blocks']):
        if verbose:
            print(bn,type(block),end="")
            if type(block) == dict:
                print(block.keys())
            else:
                print()
        for ln,line in enumerate(block['lines']):
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

    if header_start == None and separator == None:
        print("Failed to find header")
    elif header_start == None and separator != None:
        print("Failed to find header start")
    elif header_start != None and separator == None:
        print("Failed to find header end")
    return None,None
        

def assemble_header(page_text, header_start, header_end):
    header = []
    n = 0
    if header_start[0] == header_end[0]:
        header.append([])
        for line in page_text['blocks'][header_start[0]]['lines'][header_start[1]:header_end[1]]:
            header[n].append(line['spans'][0]['text'])
        return header
    else:
        for bn in range(header_start[0],header_end[0]):
            header.append([])
            if bn == header_start[0]:
                for ln in range(header_start[1],len(page_text['blocks'][bn]['lines'])):
                    header[n].append(page_text['blocks'][bn]['lines'][ln]['spans'][0]['text'])
            elif bn > header_start[0] and bn < header_end[0]:
                for line in page_text['blocks'][bn]['lines']:
                    header[n].append(line['spans'][0]['text'])
            elif bn == header_end[0]:
                for ln in range(header_end[1]):
                    header[n].append(page_text['blocks'][bn]['lines'][ln]['spans'][0]['text'])
            else:
                raise ValueError("How did you got here?")
            n += 1
        return header

# Tests
page_testing = bronxville.load_page(1)
page_testing_text = page_testing.get_text('dict')
page_new = cornwall.load_page(0)
page_new_text = page_new.get_text('dict')

## Test get_header
header_start,header_end = get_header(page_testing_text)
header_start_new, header_end_new = get_header(page_new_text)
#print(header_start,header_end)
#print(page_testing_text['blocks'][header_start[0]]['lines'][header_start[1]]['spans'][0]['text'])
#print(page_testing_text['blocks'][header_end[0]]['lines'][header_end[1]]['spans'][0]['text'])
assert (header_start,header_end) == ((5,2),(7,0))
assert (header_start_new,header_end_new) == ((1,0),(1,3))

print("\n ###### ")

## Test assemble_header
header_testing = assemble_header(page_testing_text, header_start, header_end)
header_new = assemble_header(page_new_text, header_start_new, header_end_new)
#for bl,block in enumerate(header):
#    print("\nblock",bl)
#    for ln,line in enumerate(block):
#        print(ln,line,end='')
#print(header)
assert header_testing == [
    [
        'TAX MAP PARCEL NUMBER        PROPERTY LOCATION & CLASS  ASSESSMENT  EXEMPTION CODE------------------COUNTY--------TOWN------SCHOOL ',
        'CURRENT OWNERS NAME ',
        '       SCHOOL DISTRICT  ',
        '     LAND      TAX DESCRIPTION ',
        ' ',
        '  TAXABLE VALUE '
    ],
    [
        'CURRENT OWNERS ADDRESS        PARCEL SIZE/GRID COORD     TOTAL      SPECIAL DISTRICTS ',
        ' ',
        ' ',
        ' ',
        ' ACCOUNT NO. '
    ],
]
assert header_new == [
    [
        'TAX MAP PARCEL NUMBER          PROPERTY LOCATION & CLASS  ASSESSMENT  EXEMPTION CODE-----VILLAGE------COUNTY--------TOWN------SCHOOL',
        'CURRENT OWNERS NAME            SCHOOL DISTRICT               LAND      TAX DESCRIPTION            TAXABLE VALUE',
        'CURRENT OWNERS ADDRESS         PARCEL SIZE/GRID COORD       TOTAL      SPECIAL DISTRICTS                                 ACCOUNT NO.'
    ]
]


# Create entries by separators, split entries into columns

# In[9]:


def get_page_data(page_text,header_end):
    page_data = {}; n = 0; harvest = False
    for bn,block in enumerate(page_text['blocks'][header_end[0]:]):
        for line in block['lines']:
            line_text = line['spans'][0]['text']
            separator = re.search(
                re_separator,
                line_text
            )
            if separator:
                id=re.search(re_id,separator.group()).group()
                page_data[id] = [[]]
                harvest = True
                n = 0
            else:
                page_end = re.search(
                    re_page_end,
                    line_text
                )
                if page_end: return page_data
            if harvest: page_data[id][n].append(line_text.strip())
        if harvest: page_data[id].append([])
        n += 1


# In[205]:


def get_data(source,from_page=0,verbose=False,print_failed=True):
    c = time.time()
    
    data = {}
    failed = []
    
    for p in range(from_page,source.page_count):
        page = source.load_page(p)
        page_text=page.get_text('dict')
    
        hs,he = get_header(page_text)
        #header = assemble_header(page_text,hs,he)
    
        if hs != None and he != None:
            page_data = get_page_data(page_text,he)
            if verbose: print("page",p,page_data.keys())
            for id in page_data:
                data[id] = page_data[id]
        else:
            failed.append(p+1)
            if verbose: print("page",p)
        
    if print_failed: print("failed to find headers:",failed)
    d = time.time()
    if verbose: print("completed in",d-c)
    return data

data_bronxville = get_data(bronxville,1)
data_cornwall = get_data(cornwall,0)


# In[206]:


def break_lines(entry):
    out = []
    for line in entry:
        out.append(re.split(' {2,}+',line))
    return out

#print(break_blocks(data_cornwall['101-1-1'][0]))
print(break_lines(data_bronxville['11./5/1.-212'][0]))


# In[207]:


# Shape cornwall data
def unwrap_sublists(var:list):
    assert type(var) == list, "Input value must be a list"
    out = []
    for item in var:
        if type(item) != list:
            out.append(item)
        else:
            out.extend(item)
    return out

for key in data_cornwall:
    #for item in data_cornwall[key]:
    go = True
    while go:
        if type(data_cornwall[key]) == list:
            data_cornwall[key] = unwrap_sublists(data_cornwall[key])
            if not any(isinstance(i, list) for i in data_cornwall[key]):
                go = False
        else:
            print(key)
            go = False

for key in data_cornwall:
    data_cornwall[key] = break_lines(data_cornwall[key])


# In[143]:


def get_owner_names(entry,key):
    col1 = []
    owner_names_data = normalize_data(entry)
    #print(owner_names_data)
    for block in owner_names_data:
        try:
            #if 'PRIOR OWNER' in block[0] or 'FULL MARKET VALUE' in block[0]: break
            if 'PRIOR OWNER' in block[0]: break
            col1.append(block[0])
        except: pass
    #print(col1)
    col1 = list(filter(None,col1))
    #for block in col1: print(block)
    col1_id = max([i for i,item in enumerate(col1) if key in item])
    #print(col1_id)
    owner_names = []
    #owner_names.append(col1[2])
    for item in col1[col1_id + 1:-2]:
        owner_names.append(item)
    for item in col1[-2:]:
        company = re.search('(l ?l ?c)|(L ?L ?C)',item)
        if company:
            owner_names.append(item)
            company = None
    for i,name in enumerate(owner_names):
        if '  ' in owner_names[i]:
            owner_names[i] = name.split('  ')[0]
        owner_names[i] = owner_names[i].replace(' FULL MARKET VALUE','')
        owner_names[i] = owner_names[i].replace('FULL MARKET VALUE','')
        owner_names[i] = owner_names[i].replace(' Bronxville Sch','')
        owner_names[i] = owner_names[i].replace('Bronxville Sch','')
        owner_names[i] = re.sub(' DEED BOOK.+','',owner_names[i])
        owner_names[i] = re.sub('DEED BOOK.+','',owner_names[i])
    return owner_names

def run_test(entry,key,result,function):
    output = function(entry,key)
    assert output == result, f"{key}, {result} != {output}"

# Tests
#print(get_owner_names(data[key]))
#for block in data['11./5/1.-212']: print(block)
#run_tests([
#    (data_cornwall,[
#        ('101-1-1',['Nguyen Lap','Fowlie Greta'])
#    ])
#],get_owner_names)

testset_bronxville = [
    ('18./1/2',['Coffey John', 'Coffey Anne', 'Ameriprise Financial-D.Amoruso']),
    ('14./3/4.B',['Hyde Lindsay', 'Hyde Arthur D IV']),
    ('11./5/1.-212',['Nagle,Arthur J, Irrevocable Tr', 'Nagle Christopher P', 'Christopher Nagle']),
    ('4./5/11',['Nibur 132 Parkway Road Bronxvi', 'George Comfort & Sons, Inc.']),
    ('3./3/1.A',['Midland Garden Owners', 'Attn: Barhite & Holzinger']),
    ('1./1/1',['Mercer Robert']),
    ('1./1/10',['Nuguid Dumalag Marie A']),
    ('7.A/3/5',['Copete Andres', 'Copete Margaret M']),
    ('4./1/5',['701 Pondfield LLC', 'Pondfield 17 LLC', 'c/o Houlihan-Parnes Realtors']),
    ('20./2/1.-5L',['Bonanno Rosario']),
    ('15./3/5',['Hannick John D', 'Hannick Elizabeth E']),
    ('6.D/2/10.J',['Wolfe Gregory N', 'Wolfe Elana R']),
    ('1./1/26',['Maianti Echeverrigaray Juan P', 'Darricarrere Nicole']),
    ('1./1/15',['42 Park LLC', 'Mark J. Fonte-Trifont Realty']),
    ('2./3/48',['McLean Heights Realty LLC']),
    ('2./2/17',['Mosbacher Emil','L L C','c/o Mosbacher Properties Group','LLC']),
]

testset_cornwall = [
    ('101-1-1',['Nguyen Lap','Fowlie Greta'])
]

for key,result in testset_bronxville:
    run_test(data_bronxville[key],key,result,get_owner_names)

for key,result in testset_cornwall:
    entry = data_cornwall[key]
    if any(('FULL MARKET VALUE' in i) for i in entry[-1]): entry = entry[:-1]
    run_test(entry,key,result,get_owner_names)

#run_tests(testset,get_owner_names)

all_names = []
for entry in data_bronxville:
    all_names.append(get_owner_names(data_bronxville[entry],entry))

assert '' in ['', 'test']
assert '' not in all_names
#assert [] not in all_names
assert None not in all_names


# In[176]:


def get_owner_address(entry):
    col1 = []; company = None
    owner_address_data=normalize_data(entry)
    for bn,block in enumerate(owner_address_data):
        if len(block) > 0:
            company = re.search('(l ?l ?c)|(L ?L ?C)',block[0])
            if company:
                block.pop(0)
                company = None
    for block in owner_address_data:
        #print(block)
        try:
            if 'PRIOR OWNER' in block[0]: break
            col1.append(block[0])
        except: pass
    col1 = list(filter(None,col1))
    owner_addr = col1[-2:]
    for i,name in enumerate(owner_addr):
        if '   ' in owner_addr[i]:
            owner_addr[i] = name.split('   ')[0]
        
    return ', '.join(owner_addr)

def run_test(entry,result,function):
    output = function(entry)
    assert output == result, f"{key}, {result} != {output}"

# Tests
testset_bronxville = [
    ('14./3/4.B','5 Edgehill Close, Bronxville, NY 10708'),
    ('2./2/17','18 E 48th Street 19th Floor, New York, NY 10017'),
    ('11./5/17','118-35 Queens Blvd.,1710, Forest Hills, NY 11375'),
    ('11./5/1.-212','906 Mill Creek Dr, Palm Beach Gardens, FL 33410'),
    ('3./3/1.A','77 Pondfield Road, Bronxville, NY 10708'),
    ('20./3/2','33 Sagamore Road, Bronxville, NY 10708'),
    ('1./1/5','60 Parkway Road, Bronxville, NY 10708'),
    ('1./1/10','50 Parkway Road, Bronxville, NY 10708'),
    ('1./1/15','1955 Central Park Ave, Yonkers, NY 10710'),
    ('1./1/15.A','36-38 Parkway Road, Bronxville, NY 10708'),
]

testset_cornwall = [
    ('101-1-1','303 Shore Rd, Cornwall-On-Hudson, NY 12520'),
    ('25-1-3','31 Cedar Ln, Cornwall, NY 12518'),
    ('4-2-8.2','42 Robert Rd, Cornwall, NY 12518'),
    ('116-1-4','184 Mountain Rd, Cornwall-On-Hudson, NY 12520'),
]

for key,result in testset_bronxville:
    run_test(data_bronxville[key],result,get_owner_address)

for key,result in testset_cornwall:
    entry = []
    for line in data_cornwall[key]:
        if 'FULL MARKET VALUE' in line[0] or \
            'DEED BOOK' in line[0] or \
            'EAST-' in line[0]: break
        else: entry.append(line)
    run_test(entry,result,get_owner_address)

all_owner_addrs = []
for entry in data_bronxville:
    all_owner_addrs.append(get_owner_address(data_bronxville[entry]))

assert '' in ['', 'test']
assert '' not in all_names
assert None not in all_names


# In[168]:


def get_property_type(entry,key):
    if entry[1][1] == '':
        if entry[1][3] == '': return entry[1][2]
        else: return ' '.join(entry[1][2:4])
    elif entry [1][1] == key:
        return entry[2][1]
    else: return entry[1][1]

def run_test(entry,key,result,function):
    output = function(entry,key)
    assert output == result, f"{key}, {result} != {output}"

# Tests
testset_bronxville = [
    ('13./3/1','210 1 Family Res'),
    ('11./3/3.A','311 Res vac land'),
    ('20./2/1.-7K','411 Apartment - CONDO'),
    ('20./2/60.A-8A','210 1 Family Res'),
]

testset_cornwall = [
    ('101-1-1','210 1 Family Res'),
    ('25-1-3','220 2 Family Res'),
    ('39-6-15','250 Estate'),
]

for key,result in testset_bronxville:
    run_test(data_bronxville[key],key,result,get_property_type)

for key,result in testset_cornwall:
    entry = data_cornwall[key]
    if any(('FULL MARKET VALUE' in i) for i in entry[-1]): entry = entry[:-1]
    run_test(entry,key,result,get_property_type)

all_types = []
for entry in data_bronxville:
    all_types.append(get_property_type(data_bronxville[entry],entry))

assert '' in ['', 'test']
assert '' not in all_types


# In[216]:


def get_property_address(entry,key):
    address = [line for line in entry[0][1:] if line != '']
    if len(address) > 1:
        if key in address:
            print(f"WARN: {key} has no address")
            return None
        checks = [
            len([i for i in address if 'INCLUDLOT' in i]) != 1,
            len(address) == 2 and address[0] != address[1],
            '836' not in get_property_type(entry,key)
        ]
        if False not in checks:
            raise ValueError(f"entry {entry[1][0]}: Address len is more than 1")
    return address[0]

def run_test(entry,key,result,function):
    output = function(entry,key)
    assert output == result, f"{key}, {result} != {output}"

# Tests
testset_bronxville = [
    ('7.H/2/2','26 Courseview Road'),
    ('11./5/7', None),
]

testset_cornwall = [
    ('101-1-1','303 Shore Rd'),
    ('16-11-12','13 Bede Ter'),
    ('30-1-97.1','2 J R Ct'),
]

for key,result in testset_bronxville:
    run_test(data_bronxville[key],key,result,get_property_address)

for key,result in testset_cornwall:
    entry = copy.deepcopy(data_cornwall[key][1:])
    entry[0][0],entry[0][1] = entry[0][1],entry[0][0]
    #if any(('FULL MARKET VALUE' in i) for i in entry[-1]): entry = entry[:-1]
    run_test(entry,key,result,get_property_address)

all_property_addrs = []
for entry in data_bronxville:
    all_property_addrs.append(get_property_address(data_bronxville[entry],entry))

assert '' in ['', 'test']
assert '' not in all_property_addrs


# In[226]:


def get_zoning(entry,pattern):
    lines = [
        ' '.join(entry[1]),
        ' '.join(entry[2])
    ]
    for item in lines:
        zoning = re.search(pattern, item)
        if zoning:
            zoning = zoning.group()
            zoning = re.sub(' +', ' ',zoning)
            zoning = zoning.strip()
            return zoning
        
    #zoning = entry[2][1]
    #if zoning == '': zoning = entry[2][2]
    #if 'Bronxville Sch' in zoning:
    #    return entry[2][1]
    #else:
    #    print(entry[1][0])

def run_test(entry,key,result,function,pattern):
    output = function(entry,pattern)
    assert output == result, f"{key}, {result} != {output}"

# Tests
testset_bronxville = [
    ('1./1/15.A','Bronxville Sch 552403'),
    ('13./4/3', 'Bronxville Sch 552403'),
]

testset_cornwall = [
    ('30-1-97.1','Cornwall Csd 332401'),
    ('24-1-14','Cornwall Csd 332401'),
]

for key,result in testset_bronxville:
    run_test(data_bronxville[key],key,result,get_zoning,'Bronxville Sch  ?\\d{6} ')

for key,result in testset_cornwall:
    entry = copy.deepcopy(data_cornwall[key][1:])
    #if any(('FULL MARKET VALUE' in i) for i in entry[-1]): entry = entry[:-1]
    run_test(entry,key,result,get_zoning,'Cornwall Csd  ?\\d{6} ')

all_zoning = []
for entry in data_bronxville:
    all_zoning.append(get_zoning(data_bronxville[entry],'Bronxville Sch  ?\\d{6} '))
    if get_zoning(data_bronxville[entry],'Bronxville Sch  ?\\d{6} ') == None:
        print(entry)
        for block in data_bronxville[entry]:
            print(block)
    #print(entry,"\t:",get_zoning(data[entry]))

assert '' in ['', 'test']
assert '' not in all_zoning
assert None not in all_zoning


# In[232]:


def get_acreage(entry):
    for block in entry:
        for ln,line in enumerate(block):
            if 'ACRES' in line:
                if line == 'ACRES':
                    acreage = block[ln+1]
                else:
                    acreage = line.split()
                    try:
                        acreage = [acreage[sn+1] for sn,string in enumerate(acreage) if string == 'ACRES'][0]
                    except Exception as e:
                        if re.search('[a-zA-Z ]', block[ln+1]):
                            acreage = block[ln+1].split()
                            return float(acreage[0])
                        else:
                            acreage = block[ln+1]
                if re.search('[a-zA-Z ]', acreage):
                    acreage = acreage.split()
                    return float(acreage[0])
                else:
                    return float(acreage)

# Tests
def run_test(entry,key,result,function):
    output = function(entry)
    assert output == result, f"{key}, {result} != {output}"

# Tests
testset_bronxville = [
    ('12./3/13', 0.30),
    ('1./1/14', 0.05),
    ('7.F/5/2', None),
]

testset_cornwall = [
    ('2-9-12', 0.15),
    ('35-1-21.2', 1.00),
    ('624.089-0000-621.700-1881', None),
    ('29-1-13.221',15.90),
    ('106-3-36',0.94),
]

for key,result in testset_bronxville:
    run_test(data_bronxville[key],key,result,get_acreage)

for key,result in testset_cornwall:
    entry = copy.deepcopy(data_cornwall[key][1:])
    #if any(('FULL MARKET VALUE' in i) for i in entry[-1]): entry = entry[:-1]
    run_test(entry,key,result,get_acreage)

all_acreage = []
for entry in data_bronxville:
    acr = get_acreage(data_bronxville[entry])
    all_acreage.append(acr)

assert '' in ['', 'test']
assert '' not in all_acreage


# In[41]:


def get_full_market_value(entry):
    for block in entry:
        for ln,line in enumerate(block):
            if 'FULL MARKET VALUE' in line:
                if line == 'FULL MARKET VALUE':
                    if block[ln+1] == '':
                        mval = block[ln+2]
                    else:
                        mval = block[ln+1]
                    if type(mval) == str:
                        if re.search('[a-zA-Z ]', mval):
                            mval = mval.split()[0]
                        return float(mval.replace(',','.'))
                else:
                    line = line.split()
                    for sn,subline in enumerate(line):
                        if subline == 'VALUE':
                            try: mval = line[sn+1]
                            except Exception as e:
                                if block[ln+1] == '':
                                    mval = block[ln+2]
                                else:
                                    mval = block[ln+1]
                            break
                    if type(mval) == str:
                        if re.search('[a-zA-Z ]', mval):
                            mval = mval.split()[0]
                        return float(mval.replace(',','.'))
                                
                        

# Tests
assert get_full_market_value(data['11./5/1.-202']) == 1011.081
assert get_full_market_value(data['2./1/11']) == 6321.803

all_market_values = []
for entry in data:
    mval = get_full_market_value(data[entry])
    all_market_values.append(mval)
    if mval == None: print(data[entry])
    #try:all_market_values.append(get_full_market_value(data[entry]))
    #except Exception as e:
        #print(entry,":",e)
        #print(entry)

assert '' in ['', 'test']
assert '' not in all_market_values
assert None not in all_market_values


# In[40]:


def get_taxable(entry,taxable_name):
    taxable = find_line(entry,taxable_name)
    if taxable == 1:
        #print(f"WARN: {entry[1][0]} doesn't have {taxable_name}")
        return None
    else:
        bn,ln = taxable[0],taxable[1]
    if taxable_name == entry[bn][ln]: taxable = entry[bn][ln+1]
    else:
        taxable = entry[bn][ln].split()
        for sn,string in enumerate(taxable):
            if string == 'VALUE':
                try: taxable = taxable[sn+1]
                except: taxable = entry[bn][ln+1]
                break
    if re.search('[a-zA-Z ]', taxable):
        taxable = taxable.split()[0]
    return float(taxable.replace(',','.'))


def get_all_taxables(entry):
    taxable_names = ['COUNTY TAXABLE VALUE','VILLAGE TAXABLE VALUE','SCHOOL TAXABLE VALUE']
    taxables = []
    for tn in taxable_names:
        taxables.append(get_taxable(entry,tn))
    return taxables

# Tests
def run_test(entry,key,result,function):
    output = function(entry)
    assert output == result, f"{key}, {result} != {output}"

testset_bronxville = [
    ('1./1/10',[None,1100,1100]),
    ('7.E/3/8',[None,3500,3500]),
    ('11./5/1.-311',[None,869.261,869.261]),
    ('3./3/11',[1475,1475,1398.580]),
]

testset_cornwall = [
    ('30-1-97.1','Cornwall Csd 332401'),
    ('24-1-14','Cornwall Csd 332401'),
]

for key,result in testset_bronxville:
    run_test(data_bronxville[key],key,result,get_zoning)

for key,result in testset_cornwall:
    entry = copy.deepcopy(data_cornwall[key][1:])
    #if any(('FULL MARKET VALUE' in i) for i in entry[-1]): entry = entry[:-1]
    run_test(entry,key,result,get_zoning)

#print(get_all_taxables(data[key]))
#print(get_all_taxables(data['11./5/1.-311']))
assert get_all_taxables(data['1./1/10']) == [None,1100,1100]
assert get_all_taxables(data['7.E/3/8']) == [None,3500,3500]
assert get_all_taxables(data['11./5/1.-311']) == [None,869.261,869.261]
assert get_all_taxables(data['3./3/11']) == [1475,1475,1398.580]

all_taxables = []
for entry in data:
    #print(entry)
    taxable = get_all_taxables(data[entry])
    all_taxables.append(taxable)
    #try:all_market_values.append(get_full_market_value(data[entry]))
    #except Exception as e:
        #print(entry,":",e)
        #print(entry)

assert '' in ['', 'test']
assert ['','',''] not in all_taxables
assert None not in all_taxables


# In[46]:


wb = Workbook()
ws = wb.active

ws.title = "2024 final assessment roll"
ws['A1'] = 'id'               # 1 id
ws['B1'] = 'OWNERS NAME'      # 2 owners name
ws['C1'] = 'OWNERS ADDRESS'   # 3 owners address
ws['D1'] = 'PROPERTY TYPE'    # 4 property type
ws['E1'] = 'PROPERTY ADDRESS' # 5 property address
ws['F1'] = 'ZONING'           # 6 School district, I think
ws['G1'] = 'ACREAGE'          # 7 acreage
ws['H1'] = 'FULL MARKET VALUE'# 8 school taxable
ws['I1'] = 'COUNTY TAXABLE'   # 9 town taxable
ws['J1'] = 'SCHOOL TAXABLE'
ws['K1'] = 'TOWN TAXABLE'


# In[47]:


row = 2
a = time.time()
for id in data:
    ws[f"A{row}"] = id
    ws[f"B{row}"] = ', '.join(get_owner_names(data[id]))
    ws[f"C{row}"] = get_owner_address(data[id])
    ws[f"D{row}"] = get_property_type(data[id])
    ws[f"E{row}"] = get_property_address(data[id],id)
    ws[f"F{row}"] = get_zoning(data[id])
    ws[f"G{row}"] = get_acreage(data[id])
    ws[f"H{row}"] = get_full_market_value(data[id])
    ws[f"I{row}"] = get_taxable(data[id],'COUNTY TAXABLE VALUE')
    ws[f"J{row}"] = get_taxable(data[id],'SCHOOL TAXABLE VALUE')
    ws[f"K{row}"] = get_taxable(data[id],'VILLAGE TAXABLE VALUE')
    row += 1

wb.save('extracted_data.xlsx')
b = time.time()

print(b-a)


# In[ ]:




