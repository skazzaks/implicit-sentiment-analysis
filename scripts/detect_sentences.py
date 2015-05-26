# !/usr/bin/python
# Author: Devon Fritz
# Creation Date: 25.5.15
# Figures out the sentences from which we can extra sentiment information from
# a list of dependency parsed sentences
import sys
import random

POS_SENT_NUM = 0
POS_WORD = 1
POS_POS = 5
POS_ROLE = 11
POS_SUB = "SB"
POS_PPER = "PPER"
MAX_LEN = 10

input_file = sys.argv[1]
random.seed()

# This is our first shot at detection - grab all the sentences that
# only have one subject
def phase1_detection(f):
    found_subject = False
    success = True
    new_sentence = True
    previous_sentence = ""
    total_sentences = 0
    total_successes = 0
    current_word = 1
    sentences = []
    
    for line in f:
        if len(line) < 2:
            # We are on a new sentence
            # 1) Let's see if the old one was success
            if success:
                total_successes += 1
                #print previous_sentence
                sentences.append(previous_sentence)

            # 2) Reset variables
            new_sentence = True
            success = True
            previous_sentence = ""
            first_sentence = False
            found_subject = False
            total_sentences += 1
            current_word = 1
            
        else:
            s = line.split()

            #print len(s), s
            if s[POS_ROLE] == POS_SUB:
                # If we found two subjects, let's discard this sentence for now
                if found_subject == True:
                    success = False
                found_subject = True

            # Mark as failure any sentence with a pronoun, since we don't plan
            # to try to resolve them
            if s[POS_POS] == POS_PPER:
                success = False

            # Sentence length limit
            if current_word > MAX_LEN:
                success = False

            previous_sentence += " " + s[POS_WORD]
            current_word += 1

    print "Sentence Count: " + str(total_sentences) + "\tSuccesses: " + str(total_successes) + "\n"
    print "Sample Sentences: \n"
    for i in range(1, 25):
        x = random.randrange(0, len(sentences))
        print sentences[x]
    
with open(input_file) as f:
    phase1_detection(f)
    
    
    
