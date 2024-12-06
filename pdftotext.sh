#!/usr/evn bash

set -o errexit
set -o errtrace
set -o pipefail

file="${1}"
if [ -z "$file" ]
then
   echo "Usage: pdftotext.sh [path_to_file]"
   return 1
else
   pdftotext -layout "$file"
fi
