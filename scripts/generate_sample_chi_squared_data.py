import sys
import argparse
import random

def run_program(lexicon, words, count):
    for x in xrange(count):
        i = random.randint(0, len(lexicon) - 1)
        s = lexicon[i][0] + " " + lexicon[i][1]

        # now, find a random word to use from our word list
        j = random.randint(0, len(words) - 1)
        s += " " + words[j].strip()  + " " + "NO_EVENT_MODIFIERS SENTENCE_ID"
        print s

def get_words(count):
    word_file = "/usr/share/dict/words"

    with open(word_file) as my_file:
        words = [next(my_file) for x in xrange(count)]

    return words

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("lexicon_file")
    args = parser.parse_args()

    lexicon = []


    with open(args.lexicon_file) as my_file:
        lexicon = [tuple(next(my_file).strip().split()) for x in xrange(10)]

    words = get_words(10)
    run_program(lexicon, words, 2000)
