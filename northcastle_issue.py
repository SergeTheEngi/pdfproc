{
 "cells": [
  {
   "cell_type": "markdown",
   "id": "fe4dffd6-c9ce-4498-8db2-301334209585",
   "metadata": {},
   "source": [
    "# This is not the whole notebook, just a quick fix."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 2,
   "id": "22b49e2c-03c1-497d-878a-f4926d6be11a",
   "metadata": {},
   "outputs": [],
   "source": [
    "import time\n",
    "\n",
    "import pymupdf\n",
    "import re\n",
    "import copy\n",
    "from openpyxl import Workbook\n",
    "import pdfproc\n",
    "from pdfproc.as_dict import \\\n",
    "    break_lines, \\\n",
    "    find_line, \\\n",
    "    get_columns, \\\n",
    "    normalize_data, \\\n",
    "    unwrap_sublists_recursive\n",
    "import pdfproc.as_lines\n",
    "\n",
    "re_id = '[0-9\\\\.\\\\-/A-Z]+'\n",
    "re_separator = f\"\\\\*+ ?{re_id} ?\\\\*+\"\n",
    "re_page_end = '\\\\*+'\n",
    "# New values\n",
    "re_hs = 'TAX MAP PARCEL'\n",
    "\n",
    "ext = pdfproc.as_dict.Extractor(\n",
    "    re_id,\n",
    "    re_separator,\n",
    "    re_page_end\n",
    ")\n",
    "\n",
    "# Sources\n",
    "src_northcastle = pymupdf.open('pdfproc/testing_data:2024FA_Northcastle.pdf')"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 3,
   "id": "9ef18cda-dcf2-4d8f-895b-1d67fe8a80e3",
   "metadata": {
    "scrolled": true
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "W: Failed to find header\n",
      "W: Failed to find header\n",
      "W: Failed to find header\n",
      "W: Failed to find header\n",
      "W: Failed to find header\n",
      "W: Failed to find header\n",
      "W: Failed to find header\n",
      "W: Failed to find header\n",
      "W: Failed to find header\n",
      "W: Failed to find header\n",
      "W: Failed to find header\n",
      "W: Failed to find header\n",
      "W: Failed to find header\n",
      "W: Failed to find header\n",
      "W: Failed to find header\n",
      "W: Failed to find header\n",
      "failed to find headers: [996, 997, 998, 1010, 1011, 1026, 1027, 1085, 1086, 1087, 1088, 1089, 1090, 1091, 1092, 1093]\n"
     ]
    }
   ],
   "source": [
    "# Extract data\n",
    "alldata = ext.get_data([\n",
    "    {'source':src_northcastle,'name':'northcastle'},\n",
    "])\n",
    "\n",
    "data_northcastle = copy.deepcopy(alldata['northcastle'])\n",
    "\n",
    "del alldata"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 4,
   "id": "e594fe26-8ad9-4b17-9d42-0978f72cc30e",
   "metadata": {
    "scrolled": true
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "['********************************************************************************************** 88.04-1-2 **************************']\n",
      "['E MIDDLE PATENT RD                                                          ACCT: R4A']\n",
      "['88.04-1-2                  311 RES VACANT LAND                         COUNTY TAXABLE                        500']\n",
      "['GORDON ALLAN S             CENTRAL SCH DIST #2                     500 TOWN TAXABLE                          500']\n",
      "['ATTN ACCOUNTING DEPT       1/02/22.A                                   SCHOOL TAXABLE                        500']\n",
      "['441 LEXINGTON AVE 9TH FL   M3                                      500 AD382 AMBUL DIST #2 (                 500 TO']\n",
      "['NEW YORK NY 10017          ACREAGE  1.07                               FD383 FIRE DIST #3                    500 TO']\n",
      "['EAST  729622  NRTH  856861']\n",
      "['FULL MKT VAL  27,777']\n"
     ]
    }
   ],
   "source": [
    "# Get zoning\n",
    "for line in data_northcastle['88.04-1-2'][0]:\n",
    "    print([line])\n",
    "\n",
    "re_acct = 'ACCT: [A-Z0-9]+'\n",
    "\n",
    "def find_my_acct(data,key,verbose=False):\n",
    "    for line in data[key][0]:\n",
    "        acct = None\n",
    "        acct = re.search(re_acct,line)\n",
    "        if acct != None:\n",
    "            return acct.group()\n",
    "    if verbose: print(f\"WARN: No account in {key}\")\n",
    "    return key\n",
    "\n",
    "failed = []\n",
    "for key in data_northcastle:\n",
    "    out = find_my_acct(data_northcastle,key)\n",
    "    if out == key:\n",
    "        failed.append(out)\n",
    "    else:\n",
    "        pass\n",
    "\n",
    "#for item in failed:\n",
    "#    for line in data_northcastle[item][0]:\n",
    "#        print([line])\n",
    "#    input(\"Press enter\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 60,
   "id": "ab017413-d3ef-4409-9fa3-16c6eda2084d",
   "metadata": {},
   "outputs": [],
   "source": [
    "# Get school districts\n",
    "\n",
    "re_scl = r'(\\w+ )+CENTRAL|CENTRAL (\\w+ )+#[0-9]+'\n",
    "\n",
    "for key in data_northcastle:\n",
    "    for line in data_northcastle[key][0]:\n",
    "        scl = None\n",
    "        line_edit = re.split('  +',line)\n",
    "        line_edit = '    '.join(line_edit[1:])\n",
    "        scl = re.search(re_scl,line_edit)\n",
    "        if scl != None:\n",
    "            scl = scl.group()\n",
    "            if 'CENTRAL SCH DIST' not in scl \\\n",
    "                and 'CENTRAL SCHOOL DIST' not in scl \\\n",
    "                and 'BYRAM HILLS CENTRAL' not in scl \\\n",
    "                and 'VALHALLA CENTRAL' not in scl \\\n",
    "                and 'HARRISON CENTRAL' not in scl:\n",
    "                print(key,scl)\n",
    "                pass\n",
    "            break"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3 (ipykernel)",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.12.7"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
