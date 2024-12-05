#!/usr/bin/env python
# coding: utf-8

# # This is not the whole notebook, just a quick fix.

# In[5]:


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


# In[6]:


# Extract data
alldata = ext.get_data([
    {'source':src_northcastle,'name':'northcastle'},
])

data_northcastle = copy.deepcopy(alldata['northcastle'])

del alldata


# In[26]:


# Get zoning
for line in data_northcastle['88.04-1-2'][0]:
    print([line])

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
    else:
        pass

#for item in failed:
#    for line in data_northcastle[item][0]:
#        print([line])
#    input("Press enter")


# In[ ]:


# Get school districts

re_scl = '(\b\w+\b)CENTRAL'

for line in data_northcastle['88.04-1-2'][0]:
    print([line])

