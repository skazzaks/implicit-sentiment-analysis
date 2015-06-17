# Author: Devon Fritz
# Date: 30.5.15
# Stems the lexicon of german words

import sys
from pattern.de import lemma, lexeme

reload(sys)
sys.setdefaultencoding('utf-8')
input_file = sys.argv[1]

with open(input_file) as f:
    for line in f:
        print lemma(line.strip())

