#!/usr/bin/env python
# coding: utf-8

# In[1]:


import time

import pymupdf
import re
import copy
from openpyxl import Workbook
import pdfproc
from pdfproc.as_dict import \
    break_lines, \
    find_line, \
    normalize_data, \
    unwrap_sublists, \
    unwrap_sublists_recursive

bronxville = pymupdf.open('pdfproc/testing_data:2024FA_Bronxville.pdf')
cornwall = pymupdf.open('pdfproc/testing_data:2024FA_Cornwall.pdf')
scarsdale = pymupdf.open('pdfproc/testing_data:2024FA_Scarsdale.pdf')
harrison = pymupdf.open('Harrison.pdf')


# In[2]:


# Inspect the data
page = harrison.load_page(1)
page_text = page.get_text('dict')

#print(page_text)

#for block in page_text['blocks']:
#    for line in block['lines']:
#        print(line['spans'][0]['text'])

header_start,header_end = get_header(page_text)
header = assemble_header(page_text, header_start, header_end)

for block in header:
    for line in block: print([line])


# ## Extracting the data
# 
# ### Splitting by text field location
# 
# Get header location by block and line number, assemble it into a new list of the same shape.

# In[3]:


re_id = '[0-9\\.\\-/A-Z]+'
re_separator = f"\\*+ ?{re_id} ?\\*+"
re_page_end = '\\*+'

ext = pdfproc.as_dict.Extractor(
    re_id,
    re_separator,
    re_page_end
)


# In[4]:


# Test header extractor
bronxville_page = bronxville.load_page(1)
bronxville_text = bronxville_page.get_text('dict')
cornwall_page = cornwall.load_page(0)
cornwall_text = cornwall_page.get_text('dict')

testset = [
        (bronxville_text,{
            'get_header':((5,2),(7,0)),
            'assemble_header':[
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
        }),
        (cornwall_text,{
            'get_header':((1,0),(1,3)),
            'assemble_header':[
                [
                    'TAX MAP PARCEL NUMBER          PROPERTY LOCATION & CLASS  ASSESSMENT  EXEMPTION CODE-----VILLAGE------COUNTY--------TOWN------SCHOOL',
                    'CURRENT OWNERS NAME            SCHOOL DISTRICT               LAND      TAX DESCRIPTION            TAXABLE VALUE',
                    'CURRENT OWNERS ADDRESS         PARCEL SIZE/GRID COORD       TOTAL      SPECIAL DISTRICTS                                 ACCOUNT NO.'
                ]
            ]
        })
]

for test,result in testset:
    header_start,header_end = ext.get_header(test)
    assert (header_start,header_end) == result['get_header']
    
    header = ext.assemble_header(test,header_start,header_end)
    assert header == result['assemble_header']


# Create entries by separators, split entries into columns

# In[5]:


# Extract data
alldata = ext.get_data([
    (bronxville,'bronxville'),
    (cornwall,'cornwall'),
    (scarsdale,'scarsdale'),
    (harrison,'harrison')
])

data_bronxville = copy.deepcopy(alldata['bronxville'])
data_cornwall = copy.deepcopy(alldata['cornwall'])
data_scarsdale = copy.deepcopy(alldata['scarsdale'])
data_harrison = copy.deepcopy(alldata['harrison'])

del alldata


# In[6]:


# Shape data
for key in data_cornwall:
    data_cornwall[key] = unwrap_sublists_recursive(data_cornwall,key)
    data_cornwall[key] = break_lines(data_cornwall[key])

for key in data_scarsdale:
    data_scarsdale[key] = unwrap_sublists_recursive(data_scarsdale,key)
    data_scarsdale[key] = break_lines(data_scarsdale[key])


# #### Get owner names

# In[7]:


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


# In[19]:


# Test bronxville
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

for key,result in testset_bronxville:
    entry = []
    temp_data = normalize_data(data_bronxville[key])
    for block in temp_data:
        if len(block) > 0 and 'PRIOR OWNER' in block[0]: break
        if len(block) > 0:
            if '  ' in block[0]:
                block[0] = block[0].split('  ')[0]
            temp = block[0].replace(' FULL MARKET VALUE','')
            temp = temp.replace('FULL MARKET VALUE','')
            temp = temp.replace(' Bronxville Sch','')
            temp = temp.replace('Bronxville Sch','')
            temp = re.sub(' DEED BOOK.+','',temp)
            temp = re.sub('DEED BOOK.+','',temp)
            entry.append(temp)
    output = ext.get_owner_names(entry,key)
    assert output == result, f"{key}, {result} != {output}"

all_names = []
for entry in data_bronxville:
    all_names.append(get_owner_names(data_bronxville[entry],entry))

assert '' in ['', 'test']
assert '' not in all_names
#assert [] not in all_names
assert None not in all_names


# In[25]:


# Test cornwall
testset_cornwall = [
    ('101-1-1',['Nguyen Lap','Fowlie Greta']),
    ('102-4-5',['Igo Ellen M']),
]

for key,result in testset_cornwall:
    entry = []
    for line in data_cornwall[key]:
        if 'FULL MARKET VALUE' in line[0] or \
            'DEED BOOK' in line[0] or \
            'EAST-' in line[0] or \
            'ACRES' in line[0] or \
            'add to' in line[0] or \
            'add map' in line[0] or \
            'SCHOOL' in line[0] or \
            'WS SHORE DR' in line[0] or \
            'BLOOMING GROVE' in line[0] or \
            'MAP' in line[0]: break
        elif ('FRNT' in line[0] and 'DPTH' in line[1]):
            if line[0][-4:] == 'FRNT': pass
            else: break
        else:
            patterns = ['FD[0-9]{3}','RG[0-9]{3}']
            temp = None
            append_test = True
            for pattern in patterns:
                temp = re.search(pattern,line[0])
                if temp: append_test = False
            if not append_test: break
            entry.append(line[0])
    output = ext.get_owner_names(entry,key)
    assert output == result, f"{key}, {result} != {output}"


# In[28]:


# Test scarsdale
testset_scarsdale = [
    ('01.05.12',['DALLAL STEVEN','DALLAL TERESA']),
    ('08.19.32',['MCHENRY BRENDAN']),
    ('19.01.40',['MITCHELL ROBERT A','MITCHELL DANA E']),
    ('01.02.20A',['HOFF BARTHELSON','MUSIC SCHOOL','% KEN COLE EXEC DIR']),
    ('11.05.9',['KROHNENGOLD STUART']),
    ('05.02.64',['HITCHCOCK PRESBYTERIAN','CHURCH']),
    ('06.06.4',['LEVINE ERIC B','SIMON TERRI E']),
    ('05.03.72',['NG JOSEPH']),
    ('13.04.52',['NEIRA ALBERT G']),
    ('09.11.50.52',['SILBERBERG HOWARD']),
    ('06.08.18',['LANDAUER BRIAN','LANDAUER MADELYN']),
    ('02.05.9',['SCARSDALE CHATEAUX OWNERS','% BARHITE AND HOLZINGER']),
    ('20.01.7',['636 EXPRESS LLC','SUITE 1191']),
    ('21.01.24',['8 STONEWALL LANE LLC']),
    ('21.01.42',['LEVITT BARRIE']),
    ('10.31.10',['VILLAGE OF SCARSDALE','EAST SIDE CLARENCE RD','TREASURER']),
]

for key,result in testset_scarsdale:
    entry = []
    for line in data_scarsdale[key]:
        if 'FULL MKT VAL' in line[0] or \
            'DEED BK' in line[0] or \
            'EAST-' in line[0] or \
            'ACREAGE' in line[0] or \
            'add to' in line[0] or \
            'add map' in line[0] or \
            'MAP' in line[0] or \
            'TAXABLE' in line[0] or \
            'CONTIGUOUS PARCEL' in line[0] or \
            bool(re.search('[A-Z]{2}[0-9]{3}',line[0])) or \
            bool(re.search('@ [0-9]',line[0])) or \
            bool(re.fullmatch('BANK [0-9]{2,3}',line[0])):
            break
        elif ('FRNT' in line[0] and 'DPTH' in line[0]) or \
            ('FRNT' in line[0] and 'DPTH' in line[1]):
            if line[0][-4:] == 'FRNT': pass
            else: break
        else:
            patterns = [
                ('FD[0-9]{3}',' '.join(line)),
                ('RG[0-9]{3}',' '.join(line)),
                ('[0-9\\,]{4,}+ ?EX',' '.join(line[:2]))
            ]
            temp = None
            append_test = True
            for pattern,text in patterns:
                temp = re.search(pattern,text)
                if temp:
                    append_test = False
            if not append_test:
                break
            else:
                newline = None
                for ln,subline in enumerate(line):
                    if 'SCARSDALE CENTRAL' in subline:
                        if ln > 1:
                            newline = [' '.join(line[:ln])]
                            newline.extend(line[ln:])
                            entry.append(newline[0])
                        else: break
                if not newline:
                    entry.append(line[0])
    #print(entry)
    output = ext.get_owner_names(entry,key)
    assert output == result, f"{key}, {result} != {output}"


# In[12]:


testset_harrison = [
    ('0011.-1',['RYEWOOD FARMS HOMEOWNERS','ASSOCIATION INC','WESTFAIR PROP MANAG INC','STE 330']),
    ('0856.-17',['MORGADO, RICHARD A']),
]

for key,result in testset_harrison:
    entry= []
    for line in data_harrison[key]:
        if 'FULL MKT VAL' in line[0] or \
            'DEED BK' in line[0] or \
            'EAST-' in line[0] or \
            'ACREAGE' in line[0] or \
            'add to' in line[0] or \
            'add map' in line[0] or \
            'MAP' in line[0] or \
            'TAXABLE' in line[0] or \
            'CONTIGUOUS PARCEL' in line[0] or \
            bool(re.search('[A-Z]{2}[0-9]{3}',line[0])) or \
            bool(re.search('@ [0-9]',line[0])) or \
            bool(re.fullmatch('BANK [0-9]{2,3}',line[0])):
            break
        elif ('FRNT' in line[0] and 'DPTH' in line[0]) or \
            ('FRNT' in line[0] and 'DPTH' in line[1]):
            if line[0][-4:] == 'FRNT': pass
            else: break
        else:
            patterns = [
                ('FD[0-9]{3}',' '.join(line)),
                ('RG[0-9]{3}',' '.join(line)),
                ('[0-9\\,]{4,}+ ?EX',' '.join(line[:2]))
            ]
            temp = None
            append_test = True
            for pattern,text in patterns:
                temp = re.search(pattern,text)
                if temp:
                    append_test = False
            if not append_test:
                break
            else:
                newline = None
                for ln,subline in enumerate(line):
                    if 'HARRISON CENTRAL' in subline:
                        if ln > 1:
                            newline = [' '.join(line[:ln])]
                            newline.extend(line[ln:])
                            entry.append(newline)
                        else: break
                if not newline:
                    entry.append(line)
    run_test(entry,key,result,get_owner_names)


# #### Get owner address

# In[13]:


def get_owner_address_blocks(entry):
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

def run_test(entry,key,result,function):
    output = function(entry)
    assert output == result, f"{key}, {result} != {output}"


# In[14]:


# Test bronxville
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

for key,result in testset_bronxville:
    run_test(data_bronxville[key],key,result,get_owner_address_blocks)

all_owner_addrs = []
for entry in data_bronxville:
    all_owner_addrs.append(get_owner_address_blocks(data_bronxville[entry]))

assert '' in ['', 'test']
assert '' not in all_owner_addrs
assert None not in all_owner_addrs


# In[15]:


# Test cornwall
testset_cornwall = [
    ('101-1-1','303 Shore Rd, Cornwall-On-Hudson, NY 12520'),
    ('25-1-3','31 Cedar Ln, Cornwall, NY 12518'),
    ('4-2-8.2','42 Robert Rd, Cornwall, NY 12518'),
    ('116-1-4','184 Mountain Rd, Cornwall-On-Hudson, NY 12520'),
    ('118-1-6.2','25 Boulevard, Cornwall, NY 12518'),
    ('101-1-13.12','16 Idlewild Park Dr, Cornwall-On-Hudson, NY 12520'),
    ('103-1-3.4','378 Hudson St, Cornwall-On-Hudson, NY 12520'),
    #('102-9-24','10-63 Jackson Ave Unit Pha, Long Island City, NY 111001'),
    ('17-6-10','8 Ferguson Rd, Cornwall, NY 12518'),
    ('105-9-17.3','325 Hudson St, Cornwall-On-Hudson, NY 12520'),
    ('1-1-2.22','25 Shore Dr, New Windsor, NY 12553'),
    ('1-1-64.2','1350 Broadway Ste 201, New York, NY 10018'),
    ('1-1-177','18 Idlewild Park Dr, Cornwall on Hudson, NY 12520'),
    ('1-2-19','255 Orrs Mills Rd, Salisbury Mills, NY 12577'),
]

for key,result in testset_cornwall:
    entry = []
    for line in data_cornwall[key]:
        if 'FULL MARKET VALUE' in line[0] or \
            'DEED BOOK' in line[0] or \
            'EAST-' in line[0] or \
            'ACRES' in line[0] or \
            'add to' in line[0] or \
            'add map' in line[0] or \
            'SCHOOL' in line[0] or \
            'WS SHORE DR' in line[0] or \
            'BLOOMING GROVE' in line[0] or \
            'MAP' in line[0]: break
        elif ('FRNT' in line[0] and 'DPTH' in line[1]):
            if line[0][-4:] == 'FRNT': pass
            else: break
        else:
            patterns = ['FD[0-9]{3}','RG[0-9]{3}']
            temp = None
            append_test = True
            for pattern in patterns:
                temp = re.search(pattern,line[0])
                if temp: append_test = False
            if not append_test: break
            entry.append(line)
    run_test(entry,key,result,get_owner_address_blocks)


# In[16]:


# Test scarsdale
testset_scarsdale = [
    ('01.05.12','5 SCHOOL LA, SCARSDALE NY 10583'),
    ('08.19.32','113 BRAMBACH RD, SCARSDALE NY 10583'),
    ('19.01.40','18 CORALYN RD, SCARSDALE NY 10583'),
    ('01.02.20A','25 SCHOOL LA, SCARSDALE NY 10583'),
    ('11.05.9','15 HAMILTON RD, SCARSDALE NY 10583'),
    ('05.02.64','6 GREENACRES AVE, SCARSDALE NY 10583'),
    ('09.11.50.52','37 SPRAGUE RD, SCARSDALE NY 10583'),
    ('06.08.18','1 BERKELEY RD, SCARSDALE NY 10583'),
    ('01.01.4','10 SCHOOL LA, SCARSDALE NY 10583'),
    ('02.05.9','77 PONDFIELD RD, BRONXVILLE NY 10708'),
    ('20.01.7','455 TARRYTOWN RD, WHITE PLAINS NY 10607'),
    ('21.01.24','16 STONEWALL LA, MAMARONECK NY 10538'),
    ('21.01.42','16 STONEWALL LA, MAMARONECK NY 10543'),
    ('10.31.10','1001 POST RD, SCARSDALE NY 10583'),
]

for key,result in testset_scarsdale:
    entry = []
    for line in data_scarsdale[key]:
        if 'FULL MKT VAL' in line[0] or \
            'DEED BK' in line[0] or \
            'EAST-' in line[0] or \
            'ACREAGE' in line[0] or \
            'add to' in line[0] or \
            'add map' in line[0] or \
            'MAP' in line[0] or \
            'TAXABLE' in line[0] or \
            'CONTIGUOUS PARCEL' in line[0] or \
            bool(re.search('[A-Z]{2}[0-9]{3}',line[0])) or \
            bool(re.search('@ [0-9]',line[0])) or \
            bool(re.fullmatch('BANK [0-9]{2,3}',line[0])):
                break
        elif ('FRNT' in line[0] and 'DPTH' in line[0]) or ('FRNT' in line[0] and 'DPTH' in line[1]):
            if line[0][-4:] == 'FRNT': pass
            else:
                break
        else:
            patterns = [
                ('FD[0-9]{3}',' '.join(line)),
                ('RG[0-9]{3}',' '.join(line)),
                ('[0-9\\,]{4,}+ ?EX',' '.join(line[:2]))
            ]
            temp = None
            append_test = True
            for pattern,text in patterns:
                temp = re.search(pattern,text)
                if temp:
                    if key == '10.31.10': print(temp.group())
                    append_test = False
            if not append_test:
                break
            else:
                entry.append(line)
    run_test(entry,key,result,get_owner_address_blocks)


# In[17]:


def get_owner_address_lines(entry,position):
    '''position = (fromchar,tochar)'''
    fromchar,tochar = position
    result = []
    for item in entry[-2:]:
        result.append(' '.join(item[fromchar:tochar].split()))
    return ', '.join(result)

# Test harrison
testset_harrison = [
    ('0011.-1','56 LAFAYETTE AVE, WHITE PLAINS NY 10603'),
    ('0824.-19','146 FREMONT ST, HARRISON NY 10528')
]

for key,result in testset_harrison:
    #entry = copy.deepcopy(data_harrison[key])
    entry = []
    for line in data_harrison[key]:
        if 'FULL MKT VAL' in line[0:27] or \
            'DEED BK' in line[0:27] or \
            'EAST-' in line[0:27] or \
            'ACREAGE' in line[0:27] or \
            'add to' in line[0:27] or \
            'add map' in line[0:27] or \
            'MAP' in line[0:27] or \
            'TAXABLE' in line[0:27] or \
            'CONTIGUOUS PARCEL' in line[0:27] or \
            bool(re.search('[A-Z]{2}[0-9]{3}',line[0:27])) or \
            bool(re.search('@ [0-9]',line[0:27])) or \
            bool(re.fullmatch('BANK [0-9]{2,3}',line[0:27])):
                break
        else:
            entry.append(line)
    assert get_owner_address_lines(entry,(0,27)) == result, f"{key}, {get_owner_address_lines(entry,(0,27))} != {result}"


# In[18]:


# Test harrison
testset_harrison = [
    ('0011.-1','56 LAFAYETTE AVE, WHITE PLAINS NY 10603'),
    ('0824.-19','146 FREMONT ST, HARRISON NY 10528')
]

for key,result in testset_harrison:
    entry = []
    for line in data_harrison[key]:
        if 'FULL MKT VAL' in line[0] or \
            'DEED BK' in line[0] or \
            'EAST-' in line[0] or \
            'ACREAGE' in line[0] or \
            'add to' in line[0] or \
            'add map' in line[0] or \
            'MAP' in line[0] or \
            'TAXABLE' in line[0] or \
            'CONTIGUOUS PARCEL' in line[0] or \
            bool(re.search('[A-Z]{2}[0-9]{3}',line[0])) or \
            bool(re.search('@ [0-9]',line[0])) or \
            bool(re.fullmatch('BANK [0-9]{2,3}',line[0])):
                break
        elif ('FRNT' in line[0] and 'DPTH' in line[0]) or ('FRNT' in line[0] and 'DPTH' in line[1]):
            if line[0][-4:] == 'FRNT': pass
            else:
                break
        else:
            patterns = [
                ('FD[0-9]{3}',' '.join(line)),
                ('RG[0-9]{3}',' '.join(line)),
                ('[0-9\\,]{4,}+ ?EX',' '.join(line[:2]))
            ]
            temp = None
            append_test = True
            for pattern,text in patterns:
                temp = re.search(pattern,text)
                if temp:
                    if key == '10.31.10': print(temp.group())
                    append_test = False
            if not append_test:
                break
            else:
                entry.append(line)
    print(entry)
    run_test(entry,key,result,get_owner_address_blocks)


# In[19]:


def get_property_type(entry,key):
    try:
        if entry[1][1] == '':
            if entry[1][3] == '': return entry[1][2]
            else: return ' '.join(entry[1][2:4])
        elif entry[1][1] == key or entry[2][0] == key:
            return entry[2][1]
        else: return entry[1][1]
    except Exception as e:
        print(f"WARN: {e} for {key}")
        return entry[2][1]

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
    ('101-3-1','210 1 Family Res'),
    ('101-1-13.12','210 1 Family Res'),
    ('101-3-3','210 1 Family Res'),
    ('1-1-64.2','311 Res vac land'),
]

testset_scarsdale = [
    ('01.05.12','210 1 FAMILY RES'),
    ('08.19.32','210 1 FAMILY RES'),
    ('19.01.40','210 1 FAMILY RES'),
    ('01.02.20A','612 SCHOOLS'),
    ('11.05.9','210 1 FAMILY RES'),
]

for key,result in testset_bronxville:
    run_test(data_bronxville[key],key,result,get_property_type)

for key,result in testset_cornwall:
    entry = data_cornwall[key]
    if any(('FULL MARKET VALUE' in i) for i in entry[-1]): entry = entry[:-1]
    run_test(entry,key,result,get_property_type)

for key,result in testset_scarsdale:
    entry = copy.deepcopy(data_scarsdale[key])
    if any(('FULL MARKET VALUE' in i) for i in entry[-1]): entry = entry[:-1]
    trash = None; trash = re.search('[A-Z]{2}',entry[2][1])
    if trash: del entry[2][1]
    run_test(entry,key,result,get_property_type)

all_types = []
for entry in data_bronxville:
    all_types.append(get_property_type(data_bronxville[entry],entry))

assert '' in ['', 'test']
assert '' not in all_types


# In[20]:


def get_property_address(entry,key):
    address = [line for line in entry[0][1:] if line != '']
    if key in address:
        print(f"WARN: {key} has no address")
        return None
    if len(address) > 1:
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
    ('101-3-1','40 Pine St'),
    ('107-2-34.5','61 Duncan Ave'),
    ('1-1-62.1','10 Morris Ln'),
    ('1-1-64.2',None),
    ('2-3-10','8 Oak Dr'),
    ('13-1-11','21 Howard St'),
    ('22-1-15.1','22 Willow Ave'),
]

testset_scarsdale = [
    ('01.05.12','5 SCHOOL LA'),
    ('08.19.32','113 BRAMBACH RD'),
    ('19.01.40','18 CORALYN RD'),
    ('01.02.20A','25 SCHOOL LA'),
    ('11.05.9','15 HAMILTON RD'),
    ('02.05.2A.2','CHRISTIE PL'),
]

for key,result in testset_bronxville:
    run_test(data_bronxville[key],key,result,get_property_address)

for key,result in testset_cornwall:
    entry = copy.deepcopy(data_cornwall[key][1:])
    if len(entry[0]) > 1:
        last_item = entry[0].pop()
        entry[0].insert(0,last_item)
        if len(entry[0]) > 2:
            entry[0][1] = ' '.join(entry[0][1:])
            entry[0] = entry[0][0:2]
    else: entry[0].append(entry[0][0])
    entry[0][1] = re.sub(' [0-9 A-Z]{10,}+','',entry[0][1])
    run_test(entry,key,result,get_property_address)

for key,result in testset_scarsdale:
    entry = copy.deepcopy(data_scarsdale[key][1:])
    if len(entry[0]) > 1:
        last_item = entry[0].pop()
        entry[0].insert(0,last_item)
    if len(entry[0]) > 2:
        entry[0][1] = ' '.join(entry[0][1:])
        entry[0] = entry[0][0:2]
    if len(entry[0]) == 1:
        entry[0].insert(0,'')
    run_test(entry,key,result,get_property_address)

all_property_addrs = []
for entry in data_bronxville:
    all_property_addrs.append(get_property_address(data_bronxville[entry],entry))

assert '' in ['', 'test']
assert '' not in all_property_addrs


# In[21]:


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
    ('1-1-64.2','Washingtonville 332002'),
    ('5-3-3','Newburgh Csd 331100'),
]

testset_scarsdale = [
    ('01.05.12','SCARSDALE CENTRAL'),
    ('08.19.32','SCARSDALE CENTRAL'),
    ('19.01.40','SCARSDALE CENTRAL'),
    ('01.02.20A','SCARSDALE CENTRAL'),
    ('11.05.9','SCARSDALE CENTRAL'),
]

for key,result in testset_bronxville:
    run_test(data_bronxville[key],key,result,get_zoning,'Bronxville Sch  ?\\d{6} ')

for key,result in testset_cornwall:
    entry = copy.deepcopy(data_cornwall[key][1:])
    #if any(('FULL MARKET VALUE' in i) for i in entry[-1]): entry = entry[:-1]
    run_test(entry,key,result,get_zoning,'Cornwall Csd  ?\\d{6} |Washingtonville  ?\\d{6} |[A-Za-z]+ Csd  ?\\d{6}')

# Scarsdale tests
for key,result in testset_scarsdale:
    entry = copy.deepcopy(data_scarsdale[key][1:])
    #if any(('FULL MARKET VALUE' in i) for i in entry[-1]): entry = entry[:-1]
    run_test(entry,key,result,get_zoning,'SCARSDALE CENTRAL')

for key in data_scarsdale:
    result = None; entry = None
    entry = copy.deepcopy(data_scarsdale[key][1:])
    result = get_zoning(entry,'SCARSDALE CENTRAL')
    assert result != None

# Old tests
all_zoning = []
for entry in data_bronxville:
    all_zoning.append(get_zoning(data_bronxville[entry],'Bronxville Sch  ?\\d{6} '))
    if get_zoning(data_bronxville[entry],'Bronxville Sch  ?\\d{6} |Washingtonville  ?\\d{6} ') == None:
        print(entry)
        for block in data_bronxville[entry]:
            print(block)
    #print(entry,"\t:",get_zoning(data[entry]))

assert '' in ['', 'test']
assert '' not in all_zoning
assert None not in all_zoning


# In[22]:


def get_acreage(entry,keyword='ACRES'):
    for block in entry:
        temp = ' '.join(block)
        temp = ' '.join(temp.split())
        acres = re.search(f"{keyword} [0-9]+\\.[0-9][0-9]",temp)
        if acres:
            acres = re.sub(f'{keyword} ','',acres.group())
            return float(acres)

# Tests
def run_test(entry,key,result,function,keyword='ACRES'):
    output = function(entry,keyword)
    assert output == result, f"{key}, {result} != {output}"

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

testset_scarsdale = [
    ('01.05.12',0.40),
    ('08.19.32',0.11),
    ('19.01.40',0.16),
    ('01.02.20A',1.48),
    ('11.05.9',0.18),
    ('08.22.20',None),
]

for key,result in testset_bronxville:
    run_test(data_bronxville[key],key,result,get_acreage)

for key,result in testset_cornwall:
    entry = copy.deepcopy(data_cornwall[key][1:])
    run_test(entry,key,result,get_acreage)

for key,result in testset_scarsdale:
    entry = copy.deepcopy(data_scarsdale[key][1:])
    run_test(entry,key,result,get_acreage,'ACREAGE')

all_acreage = []
for entry in data_bronxville:
    acr = get_acreage(data_bronxville[entry])
    all_acreage.append(acr)

assert '' in ['', 'test']
assert '' not in all_acreage


# In[23]:


def get_full_market_value(entry,keywords=['FULL MARKET VALUE','VALUE']):
    for block in entry:
        for ln,line in enumerate(block):
            if keywords[0] in line:
                if line == keywords[0]:
                    if block[ln+1] == '':
                        mval = block[ln+2]
                    else:
                        mval = block[ln+1]
                    if type(mval) == str:
                        if re.search('[a-zA-Z ]', mval):
                            mval = mval.split()[0]
                        return float(mval.replace(',',''))
                else:
                    line = line.split()
                    for sn,subline in enumerate(line):
                        if subline == keywords[1]:
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
                        return float(mval.replace(',',''))
                                
                        
# Tests
def run_test(entry,key,result,function,keywords=['FULL MARKET VALUE','VALUE']):
    output = function(entry,keywords)
    assert output == result, f"{key}, {result} != {output}"

testset_bronxville = [
    ('11./5/1.-202', 1011081),
    ('2./1/11', 6321803),
]

testset_cornwall = [
    ('102-19-10',424600),
    ('106-3-36',761400),
    ('20-6-12',551600),
    ('624.089-0000-621.700-1881',0)
]

testset_scarsdale = [
    ('01.05.12',2568721),
    ('08.19.32',1067520),
    ('19.01.40',2297037),
    ('01.02.20A',11742727),
    ('11.05.9',1177441),
]

for key,result in testset_bronxville:
    run_test(data_bronxville[key],key,result,get_full_market_value)

for key,result in testset_cornwall:
    entry = copy.deepcopy(data_cornwall[key][1:])
    run_test(entry,key,result,get_full_market_value)

for key,result in testset_scarsdale:
    entry = copy.deepcopy(data_scarsdale[key][1:])
    run_test(entry,key,result,get_full_market_value,keywords=['FULL MKT VAL','VAL'])

all_market_values = []
for entry in data_bronxville:
    mval = get_full_market_value(data_bronxville[entry])
    all_market_values.append(mval)
    if mval == None: print(data[entry])
    #try:all_market_values.append(get_full_market_value(data[entry]))
    #except Exception as e:
        #print(entry,":",e)
        #print(entry)

assert '' in ['', 'test']
assert '' not in all_market_values
assert None not in all_market_values


# In[24]:


def get_taxable(entry,taxable_name):
    taxable_line = find_line(entry,taxable_name)
    if taxable_line == 1:
        #print(f"WARN: {entry[1][0]} doesn't have {taxable_name}")
        return None
    
    taxable = re.search(taxable_name + ' [0-9\\,]+',taxable_line)
    taxable = re.sub(taxable_name + ' ','',taxable.group())
    return float(taxable.replace(',',''))
    #else:
    #    taxable = entry[bn][ln].split()
    #    for sn,string in enumerate(taxable):
    #        if string == 'VALUE':
    #            try: taxable = taxable[sn+1]
    #            except: taxable = entry[bn][ln+1]
    #            break
    #if re.search('[a-zA-Z ]', taxable):
    #    taxable = taxable.split()[0]
    #return float(taxable.replace(',',''))


def get_all_taxables(entry,taxable_names):
    taxables = []
    for tn in taxable_names:
        taxables.append(get_taxable(entry,tn))
    return taxables

# Tests
def run_test(entry,key,result,function,taxable_names):
    output = function(entry,taxable_names)
    assert output == result, f"{key}, {result} != {output}"

testset_bronxville = [
    ('1./1/10',[None,1100000,1100000]),
    ('7.E/3/8',[None,3500000,3500000]),
    ('11./5/1.-311',[None,869261,869261]),
    ('3./3/11',[1475000,1475000,1398580]),
]

testset_cornwall = [
    ('101-1-1',[475000,475000,475000]),
    ('18-3-16',[287400,287400,287400]),
]

testset_scarsdale = [
    ('01.01.1',[1425000,1425000,1425000]),
    ('01.05.12',[1925000,1925000,1925000]),
    ('08.19.32',[800000,800000,800000]),
    ('19.01.40',[1721400,1721400,1721400]),
    ('01.02.20A',[0,0,0]),
    ('11.05.9',[882375,882375,882375]),
]

taxable_names = ['COUNTY TAXABLE VALUE','VILLAGE TAXABLE VALUE','SCHOOL TAXABLE VALUE']
for key,result in testset_bronxville:
    run_test(data_bronxville[key],key,result,get_all_taxables,taxable_names)

taxable_names = ['COUNTY TAXABLE VALUE','TOWN TAXABLE VALUE','SCHOOL TAXABLE VALUE']
for key,result in testset_cornwall:
    entry = copy.deepcopy(data_cornwall[key][1:])
    run_test(entry,key,result,get_all_taxables,taxable_names)

taxable_names = ['COUNTY TAXABLE','VILLAGE TAXABLE','SCHOOL TAXABLE']
for key,result in testset_scarsdale:
    entry = copy.deepcopy(data_scarsdale[key][1:])
    run_test(entry,key,result,get_all_taxables,taxable_names)

taxable_names = ['COUNTY TAXABLE VALUE','VILLAGE TAXABLE VALUE','SCHOOL TAXABLE VALUE']
all_taxables = []
for entry in data_bronxville:
    taxable = get_all_taxables(data_bronxville[entry],taxable_names)
    all_taxables.append(taxable)

assert '' in ['', 'test']
assert ['','',''] not in all_taxables
assert None not in all_taxables


# In[58]:


wb = Workbook()
ws = wb.active

ws.title = "2024 final roll - Scarsdale"
ws['A1'] = 'id'
ws['B1'] = 'OWNERS NAME'
ws['C1'] = 'OWNERS ADDRESS'
ws['D1'] = 'PROPERTY TYPE'
ws['E1'] = 'PROPERTY ADDRESS'
ws['F1'] = 'ZONING'
ws['G1'] = 'ACREAGE'
ws['H1'] = 'FULL MARKET VALUE'
ws['I1'] = 'COUNTY TAXABLE'
ws['J1'] = 'SCHOOL TAXABLE'
ws['K1'] = 'VILLAGE TAXABLE'


# In[59]:


# Extract the data
row = 2
a = time.time()
for key in data_scarsdale:
    print(key)
    ws[f"A{row}"] = key
    
    # Owner names
    entry = []
    for line in data_scarsdale[key]:
        if 'FULL MKT VAL' in line[0] or \
            'DEED BK' in line[0] or \
            'EAST-' in line[0] or \
            'ACREAGE' in line[0] or \
            'add to' in line[0] or \
            'add map' in line[0] or \
            'MAP' in line[0] or \
            'TAXABLE' in line[0] or \
            'CONTIGUOUS PARCEL' in line[0] or \
            bool(re.search('[A-Z]{2}[0-9]{3}',line[0])) or \
            bool(re.search('@ [0-9]',line[0])) or \
            bool(re.fullmatch('BANK [0-9]{2,3}',line[0])):
            break
        elif ('FRNT' in line[0] and 'DPTH' in line[0]) or ('FRNT' in line[0] and 'DPTH' in line[1]):
            if line[0][-4:] == 'FRNT': pass
            else: break
        else:
            patterns = [
                ('FD[0-9]{3}',' '.join(line)),
                ('RG[0-9]{3}',' '.join(line)),
                ('[0-9\\,]{4,}+ ?EX',' '.join(line[:2]))
            ]
            temp = None
            append_test = True
            for pattern,text in patterns:
                temp = re.search(pattern,text)
                if temp:
                    append_test = False
            if not append_test:
                break
            else:
                newline = None
                for ln,subline in enumerate(line):
                    if 'SCARSDALE CENTRAL' in subline:
                        if ln > 1:
                            newline = [' '.join(line[:ln])]
                            newline.extend(line[ln:])
                            entry.append(newline)
                        else: break
                if not newline:
                    entry.append(line)
    ws[f"B{row}"] = ', '.join(get_owner_names(entry,key))

    # Owner address
    entry = []
    for line in data_scarsdale[key]:
        if 'FULL MKT VAL' in line[0] or \
            'DEED BK' in line[0] or \
            'EAST-' in line[0] or \
            'ACREAGE' in line[0] or \
            'add to' in line[0] or \
            'add map' in line[0] or \
            'MAP' in line[0] or \
            'TAXABLE' in line[0] or \
            'CONTIGUOUS PARCEL' in line[0] or \
            bool(re.search('[A-Z]{2}[0-9]{3}',line[0])) or \
            bool(re.search('@ [0-9]',line[0])) or \
            bool(re.fullmatch('BANK [0-9]{2,3}',line[0])):
                break
        elif ('FRNT' in line[0] and 'DPTH' in line[0]) or ('FRNT' in line[0] and 'DPTH' in line[1]):
            if line[0][-4:] == 'FRNT': pass
            else:
                break
        else:
            patterns = [
                ('FD[0-9]{3}',' '.join(line)),
                ('RG[0-9]{3}',' '.join(line)),
                ('[0-9\\,]{4,}+ ?EX',' '.join(line[:2]))
            ]
            temp = None
            append_test = True
            for pattern,text in patterns:
                temp = re.search(pattern,text)
                if temp:
                    if key == '10.31.10': print(temp.group())
                    append_test = False
            if not append_test:
                break
            else:
                entry.append(line)
    ws[f"C{row}"] = get_owner_address(entry)

    # Property type
    entry = copy.deepcopy(data_scarsdale[key])
    if any(('FULL MARKET VALUE' in i) for i in entry[-1]): entry = entry[:-1]
    trash = None; trash = re.search('[A-Z]{2}',entry[2][1])
    if trash: del entry[2][1]
    ws[f"D{row}"] = get_property_type(entry,key)

    # Property address
    entry = copy.deepcopy(data_scarsdale[key][1:])
    if len(entry[0]) > 1:
        last_item = entry[0].pop()
        entry[0].insert(0,last_item)
    if len(entry[0]) > 2:
        entry[0][1] = ' '.join(entry[0][1:])
        entry[0] = entry[0][0:2]
    if len(entry[0]) == 1:
        entry[0].insert(0,'')
    ws[f"E{row}"] = get_property_address(entry,key)

    # Zoning
    entry = copy.deepcopy(data_scarsdale[key][1:])
    ws[f"F{row}"] = get_zoning(entry,'SCARSDALE CENTRAL')

    # Acreage
    entry = copy.deepcopy(data_scarsdale[key][1:])
    ws[f"G{row}"] = get_acreage(entry,'ACREAGE')

    # Full market value
    entry = copy.deepcopy(data_scarsdale[key][1:])
    ws[f"H{row}"] = get_full_market_value(entry,keywords=['FULL MKT VAL','VAL'])

    # Taxables
    entry = copy.deepcopy(data_scarsdale[key][1:])
    ws[f"I{row}"] = get_taxable(entry,'COUNTY TAXABLE')
    ws[f"J{row}"] = get_taxable(entry,'SCHOOL TAXABLE')
    ws[f"K{row}"] = get_taxable(entry,'VILLAGE TAXABLE')
    row += 1

wb.save('extracted_data.xlsx')
b = time.time()

print(b-a)

