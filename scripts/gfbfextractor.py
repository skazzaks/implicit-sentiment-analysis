import re
import os
import sys
import math
from nltk.stem import WordNetLemmatizer
from nltk.tag.stanford import POSTagger
from nltk.corpus import wordnet

import goslate

class GFBFEventStatistic:
    def __init__(self):
        self.positive_count = 0
        self.negative_count = 0

    def count_line(self, gfbf_line):
        if gfbf_line["polarity"] == "badfor":
            self.negative_count += 1
        else:
            self.positive_count += 1

    @property
    def total_count(self):
        return self.gf_count + self.bf_count

class GFBFCounter:
    def __init__(self):
        self.events = {}

    def __call__(self, gfbf_generator):
        for gfbf_line in gfbf_generator:
            tokens = gfbf_line["tokens"].split()
            if len(tokens) != 1:
                continue
            lemmas = get_lemmas_from_tokens(tokens)

            event_stat = self.events.setdefault(" ".join(lemmas), GFBFEventStatistic())
            event_stat.count_line(gfbf_line)

def get_lemmas_from_tokens(tokens):
    #postagger = POSTagger("tagger/models/english-bidirectional-distsim.tagger", "tagger/stanford-postagger.jar")
    #tags = postagger.tag(tokens)

    lemmatizer = WordNetLemmatizer()

    lemmas = []
    for idx, token in enumerate(tokens):
        lemmas.append(lemmatizer.lemmatize(token.lower(), pos = "v"))

    return lemmas

def get_wordnet_pos(treebank_tag):
    #http://stackoverflow.com/questions/15586721/wordnet-lemmatization-and-pos-tagging-in-python
    if treebank_tag.startswith('J'):
        return wordnet.ADJ
    elif treebank_tag.startswith('V'):
        return wordnet.VERB
    elif treebank_tag.startswith('N'):
        return wordnet.NOUN
    elif treebank_tag.startswith('R'):
        return wordnet.ADV
    else:
        return wordnet.NOUN

def filter_gf_bf_types(gfbf_generator):
    for gfbf_line in gfbf_generator:
        if gfbf_line["type"] == "gfbf":
            yield gfbf_line

def read_gfbf_file(filename):
    with open(filename) as f:
        for line in f:
            contents = decode_gfbf_line(line)
            yield contents

def decode_gfbf_line(line):
    line_head_regex = re.compile(r"(?P<id>\d+)\s+(?P<position>\d+,\d+)\s+(?P<datatype>\w+)\s+(?P<type>\w+)")
    attr_regex = re.compile(r"\s+(\w+)=\"(.*?)\"((?=\s+(\w+)=\"(.*?)\")|$)")

    head_result = line_head_regex.match(line)
    attr_start = head_result.end()

    attributes = {}

    while True:
        attr_result = attr_regex.match(line, attr_start)

        if attr_result == None:
            break

        attr_start = attr_result.end()

        attributes[attr_result.group(1)] = attr_result.group(2)

    return {
        "type": head_result.group("type"),
        "polarity": attributes.get("polarity"),
        "tokens": attributes.get("tokenized"),
        "sentence": attributes.get("sentence")
    }


def read_gfbf_corpus(dirname):
    for filename in os.listdir(dirname):
        if filename.endswith(".mpqa"):
            file_sentences = read_gfbf_file(dirname + "/" + filename)
            for sentence in file_sentences:
                yield sentence

def calculate_event_pmi(event, total_p_pos, total_p_neg):
    total = event.positive_count + event.negative_count

    #p(+ | ev)
    p_pos = event.positive_count / float(total)
    #p(- | ev)
    p_neg = event.negative_count / float(total)

    if p_pos == 0:
        pmi_pos = float('-inf')
    else:
        #log(p(+ | ev) / p(+))
        pmi_pos = math.log(p_pos/total_p_pos)

    if p_neg == 0:
        pmi_neg = float('-inf')
    else:
        pmi_neg = math.log(p_neg/total_p_neg)

    if pmi_pos > pmi_neg:
        return "+", pmi_pos
    else:
        return "-", pmi_neg

def get_total_pos_neg_probability_in_events(events):
    pos_count = 0
    neg_count = 0
    for event in events:
        pos_count += event.positive_count
        neg_count += event.negative_count
    return pos_count / float(pos_count + neg_count), neg_count / float(pos_count + neg_count)

def sort_events_by_pmi(events):
    total_p_pos, total_p_neg = get_total_pos_neg_probability_in_events(events.values())

    pmi_scores = []

    for key, event in events.items():
        pmi_scores.append((key, calculate_event_pmi(event, total_p_pos, total_p_neg)))

    return sorted(pmi_scores, key=lambda x: x[1])

if __name__ == "__main__":
    counter = GFBFCounter()
    counter(filter_gf_bf_types(read_gfbf_corpus(sys.argv[1])))

    #print sort_events_by_pmi(counter.events)

    events = sort_events_by_pmi(counter.events)

    translator = goslate.Goslate()
    with open(sys.argv[2], "w") as of:
        for key, score in events:
            german_key = translator.translate(key, "de")
            if german_key[0].isupper():
                continue
            if len(german_key.split()) > 1:
                continue
            of.write(u"{0}\t{1}".format(german_key, unicode(score[0])).encode("utf-8"))
            of.write("\n")
