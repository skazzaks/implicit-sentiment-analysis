#!/usr/bin/env python
# -*- coding: utf-8 -*-
#Author: Devon Fritz
# Date: 6.30.15
# This script takes the given lexicon and expands it using Germanet
from pygermanet import load_germanet
import argparse
import sys

# Function assumes all hyponyms have the same value as the parent
def find_hyponyms(synset, value):
    results = []

    results.append([synset.lemmas[0].orthForm, value])
    for s in synset.hyponyms:
        results = results +  find_hyponyms(s, value)

    return results

def germanet_processor(data):
    gn = load_germanet()
    results = []
    for record in data:
        word = record[0]
        value = record[1]
        synsets = gn.synsets(word)
        if synsets == None:
            continue

        for synset in synsets:
            results += find_hyponyms(synset, value)

    return results
# Processes all expanders. Each expander processer takes the original dataset and returns a list of new items
def process(data, processors):
    results = data

    for p in processors:
        results = results + p(data)

    return results


if __name__ == "__main__":

    reload(sys)
    sys.setdefaultencoding('utf-8')
    parser = argparse.ArgumentParser(description="Expand the German lexicon")
    parser.add_argument("lexiconfile")
    args = parser.parse_args()

    data =  [l.split() for l in open(args.lexiconfile) if l[0] is not "#"]

    processors = [germanet_processor]

    results = process(data, processors)
    print results
    for r in results:
        print  r[0].encode('utf-8') + " " + r[1].encode('utf-8')
