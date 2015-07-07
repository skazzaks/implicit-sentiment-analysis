# Author: Devon Fritz
# Date: 30.5.15
# Stems the lexicon of german words

import sys
from pattern.de import lemma

reload(sys)
sys.setdefaultencoding('utf-8')
input_file = sys.argv[1]

with open(input_file) as f:
    for line in f:
        print lemma(line.split()[0].strip()) + (' ' + line.split()[1] if len(line.split()) > 1 else '')

