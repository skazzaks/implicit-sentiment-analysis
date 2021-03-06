#!/usr/bin/python
# Author: Devon Fritz
# Creation Date: 18.5.15
# This script takes the english list of emotion words and converts them into
# German.
# It uses http://pythonhosted.org/goslate/ for the translation

import goslate
import re
import sys
import os

input_file = sys.argv[1]
# Finds the word we care about in each line
prog = re.compile("^[^#].+\s+(.*)/.*")
re_word = re.compile("\s(.*?)/")
# Initialize GoSlate
gs = goslate.Goslate()

with open(input_file) as f:
    for line in f:
        result = prog.match(line)
        if result:
            w = ""
            # We have a match! Let's translate the word
            for m in re.finditer(r".*?\s(.*?)/", line):
                w += m.group(1) + " "
            t = gs.translate(w, 'de')
            print (w + ", " + t).encode('utf-8')

gs = goslate.Goslate()
