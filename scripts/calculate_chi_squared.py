import argparse
from scipy.stats import chisquare
import numpy as np

import math

# This class captures each 'Event' where an 'Event' is 'something that
# happens to someone or something'. In our case, this starts off a just a
# verb.
# This class captures the overall polarity of such an Event by aggregating
# all instances of the event together (by verb) and counting the polarity
# of the various sentiment words we have seen.
class EventStatistic:
    positive_count = 0
    negative_count = 0

    def __init__(self, event, polarity_source,
                 modifiers, sentence_id):
        self.polarity_source = polarity_source
        self.event = event
        self.modifiers = modifiers
        self.sentence_id = sentence_id

    @property
    def total(self):
        return self.positive_count + self.negative_count

    @property
    def polarity(self):
        # Find out which direction has more weight and assume it is dominant
        if self.positive_count > self.negative_count:
            return "+"
        else:
            return "-"

    @property
    def polarity_count(self):
        if self.polarity == "+":
            return self.positive_count
        else:
            return self.negative_count

    @property
    def chi_square(self):
        # build an observation array
        obs = np.array([self.positive_count, self.negative_count])

        # build the expected array, which we assume to be all of one type
        exp = np.array([self.total / 2.0, self.total / 2.0])

        probability = chisquare(obs, f_exp=exp)[1]

        return self.polarity, probability

def calculate_events_pmi(event, total_p_pos, total_p_neg):
    total = event.positive_count + event.negative_count

    #p(+ | ev)
    p_pos = event.positive_count / float(total)
    #p(- | ev)
    p_neg = event.negative_count / float(total)

    if p_pos == 0:
        pmi_pos = float('-inf')
    else:
        #log(p(+ | ev) / p(+))
        pmi_pos = math.log(p_pos/total_p_pos)

    if p_neg == 0:
        pmi_neg = float('-inf')
    else:
        pmi_neg = math.log(p_neg/total_p_neg)

    if pmi_pos > pmi_neg:
        return "+", pmi_pos
    else:
        return "-", pmi_neg

# Calculates the chi_squared value for all of the passed in events
def calculate_chi_squared(events):
    results = {}

    total_pos_p, total_neg_p = get_total_pos_neg_probability_in_events(events)

    for key, event in events.iteritems():
        if event.total < 5:
            continue

        #results[key] = event.chi_square
        results[key] = calculate_events_pmi(event, total_pos_p, total_neg_p)

        #print event.event + ": " + chi[0] + " " + str(chi[1]) + " " +  \
        #    str([event.positive_count, event.negative_count])
    return results

def get_total_pos_neg_probability_in_events(events):
    pos_count = 0
    neg_count = 0
    for event in events.values():
        pos_count += event.positive_count
        neg_count += event.negative_count
    return pos_count / float(pos_count + neg_count), neg_count / float(pos_count + neg_count)

def load_in_events(event_file):
    events = {}

    with open(event_file) as f:
        for line in f:
            line = line.split()

            if line[2] not in events:
                events[line[2]] = EventStatistic(line[2],
                                                 line[0], "TODO", "TODO")

            if line[1] == "+":
                events[line[2]].positive_count += 1
            else:
                events[line[2]].negative_count += 1

    return events

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("input_file")
    args = parser.parse_args()

    events = load_in_events(args.input_file)

    results = calculate_chi_squared(events)

    sorted_results = sorted(results.items(), key=lambda r: r[1], reverse = True)

    for key, chi in sorted_results:
        event = events[key]
        print "{0} {1} {2} [{3}, {4}]".format(key, chi[0], chi[1], event.positive_count, event.negative_count)
