#!/usr/bin/env python
# coding: utf-8

# # This is not the whole notebook, just a quick fix.

# In[78]:


import time

import pymupdf
import re
import copy
from openpyxl import Workbook
import pdfproc
from pdfproc.as_dict import \
    break_lines, \
    find_line, \
    get_columns, \
    normalize_data, \
    unwrap_sublists_recursive
import pdfproc.as_lines

re_id = '[0-9\\.\\-/A-Z]+'
re_separator = f"\\*+ ?{re_id} ?\\*+"
re_page_end = '\\*+'
# New values
re_hs = 'TAX MAP PARCEL'

ext = pdfproc.as_dict.Extractor(
    re_id,
    re_separator,
    re_page_end
)

# Sources
src_northcastle = pymupdf.open('pdfproc/testing_data:2024FA_Northcastle.pdf')
values_northcastle = {
    'zoning':{},
    'district':{},
}


# In[79]:


# Extract data
alldata = ext.get_data([
    {'source':src_northcastle,'name':'northcastle'},
])

data_northcastle = copy.deepcopy(alldata['northcastle'])

del alldata


# In[80]:


# Get zoning
re_acct = 'ACCT: [A-Z0-9]+'

def find_my_acct(data,key,verbose=False):
    for line in data[key][0]:
        acct = None
        acct = re.search(re_acct,line)
        if acct != None:
            return acct.group()
    if verbose: print(f"WARN: No account in {key}")
    return key

failed = []
for key in data_northcastle:
    out = find_my_acct(data_northcastle,key)
    if out == key:
        failed.append(out)
        values_northcastle['zoning'][key] = ''
    else:
        values_northcastle['zoning'][key] = out

print(f"Failed to get zoning for:\n{failed}")
print(len(values_northcastle['zoning']),len(data_northcastle))


# In[83]:


# Get school districts
re_scl = r'(\w+ )+CENTRAL|CENTRAL (\w+ )+#[0-9]+'

for key in data_northcastle:
    for line in data_northcastle[key][0]:
        scl = None
        line_edit = re.split('  +',line)
        line_edit = '    '.join(line_edit[1:])
        scl = re.search(re_scl,line_edit)
        if scl != None:
            values_northcastle['district'][key] = scl.group()
            break

print(len(values_northcastle['district']),len(data_northcastle))

