#!/usr/bin/env python2

import subprocess
import argparse
import dependency
import copy
import sys

from collections import Counter

HDPRO_PATH = "/Users/juliussteen/Downloads/de.uniheidelberg.cl.hdpro.german-pipelines-0.3-with-dependencies.jar"
BLANK_STR = "_"
POS_ADV = "ADV"
POS_NICHT = "PTKNEG"
POS_PPER = "PPER"

def run_hdpro(filename):
    subprocess.call(["java", "-jar", HDPRO_PATH,
            "MPNBE",
            "p",
            "-it", "TEXT",
            "-if", filename,
            "-ot", "CONLL2009",
            "-mv", "sprml13-german-train-predicted-fullzmorgelemma"])

def is_complex_sentence(sentence):
    return sentence.is_complex_sentence

def has_named_entity_subject(sentence):
    return sentence.subject_node.pos_tag == "NE"

def has_no_unresolved_pronouns(sentence):
    return not sentence.has_unresolved_pronoun

def has_trigger_pred(sentence):
    return sentence.predicate_trigger is not None

def is_not_reflexive(sentence):
    if sentence.is_complex_sentence:
        return is_not_reflexive(sentence.object_node)
    return sentence.object_node.pos_tag != "PRF"

class get_trigger_predicate:
    def __init__(self, triggers_filename):
        with open(triggers_filename, "r") as f:
            self.triggers = set([(w.split()[0].strip().lower(), 1 if w.split()[1] == "+" else -1) for w in f if not w.startswith("#")])

    def __call__(self, predicate):
        match = [(trig, polarity) for trig, polarity in self.triggers if predicate.lemma.lower() == trig]
        if len(match) is not 0:
            return match[0][0], match[0][1]
        else:
            return [None, None]

def has_unmodified_predicate(sentence):
    return len(sentence.predicate_node.find_children_by_label("MO")) == 0

class SentenceAnalyser:
    def __init__(self, get_trigger_predicate):
        self.get_trigger_predicate = get_trigger_predicate

    def __call__(self, root_nodes, local_context):
        longest_node = max(root_nodes, key = lambda n: n.child_count)
        sentence = self.analyse_sentence(longest_node)
        if sentence:
            local_context.sentence = sentence
            return PipelineProcessingStatus.CONTINUE
        else:
            return PipelineProcessingStatus.DISCARD_NODES

    def analyse_sentence(self, root_node):
        subject, dir_object = self.get_subject_and_object_from_node(root_node)
        modifiers = self.get_modifiers(root_node)
        trigger_pred, pred_polarity = self.get_trigger_predicate(root_node)

        if subject and dir_object:
            return SentenceTuple(root_node, subject, dir_object, modifiers, trigger_pred, pred_polarity)

        comp_phrase = root_node.find_child_by_label("OC")

        if comp_phrase:
            embeded_sentence = self.analyse_sentence(comp_phrase)

            if subject and embeded_sentence:
                return SentenceTuple(root_node, subject, embeded_sentence, modifiers, trigger_pred, pred_polarity)

        return None

    def get_subject_and_object_from_node(self, root_node):
        subject = root_node.find_child_by_label("SB")
        dir_object = root_node.find_child_by_label("OA")
        return subject, dir_object

    def get_modifiers(self, root_node):
        """
        Retrieves the set of modifiers (right now just adverbs) that occur
        at the provided level of the sentence
        """
        results = list(root_node.find_children_by_POS_tag(POS_ADV))
        results.extend(list(root_node.find_children_by_POS_tag(POS_NICHT)))
        return results

class SentenceFilter:
    def __init__(self, conditions = []):
        self.conditions = copy.copy(conditions)

    def __call__(self, root_nodes, local_context):
        sentence = local_context.sentence
        if all((condition(sentence) for condition in self.conditions)):
            return PipelineProcessingStatus.CONTINUE
        else:
            return PipelineProcessingStatus.DISCARD_NODES

class SentencePrinter:
    def __call__(self, root_nodes, local_context):
        print local_context.sentence
        return PipelineProcessingStatus.CONTINUE

class SentenceCounter:
    def __init__(self):
        self.count = 0

    def __call__(self, root_nodes, local_context):
        self.count += 1
        return PipelineProcessingStatus.CONTINUE

class CountIndicator:
    def __init__(self, counter, prefix):
        self.counter = counter
        self.prefix = prefix

    def __call__(self, root_nodes, local_context):
        sys.stdout.write(self.prefix + str(self.counter.count))
        sys.stdout.write("\r")
        sys.stdout.flush()

        return PipelineProcessingStatus.CONTINUE

class EntityCollector:
    def __init__(self):
        self.subj_position_entities_counter = Counter()
        self.obj_position_entities_counter = Counter()
        self.relation_counter = Counter()

    def __call__(self, root_nodes, local_context):
        sentence = local_context.sentence
        self.count_sentence(sentence)

        return PipelineProcessingStatus.CONTINUE

    def count_sentence(self, sentence):
        all_entity_strs = []
        curr_sentence = sentence

        while curr_sentence.is_complex_sentence:
            subj_str = curr_sentence.subject_node.word
            all_entity_strs.append(subj_str)
            self.subj_position_entities_counter[subj_str] += 1

            curr_sentence = curr_sentence.object_node

        subj_str = sentence.subject_node.word
        self.subj_position_entities_counter[subj_str] += 1
        all_entity_strs.append(subj_str)

        obj_str = curr_sentence.object_node.word
        self.obj_position_entities_counter[obj_str] += 1
        all_entity_strs.append(obj_str)

        self.relation_counter.update(fold_forward(all_entity_strs))

def fold_forward(list_):
    """
    Combines the elements in an iterable into two-tuples
    so that each element is combined with all elements that follow it.
    """
    if len(list_) == 1:
        return []
    result = []
    for idx, elem1 in enumerate(list_):
        for elem2 in list_[idx + 1:]:
            result.append((elem1, elem2))
    return result

class SentenceLimiter:
    def __init__(self, limit):
        self.limit = limit
        self.counter = 0

    def __call__(self, root_nodes, local_context):
        self.counter += 1
        if self.counter <= self.limit:
            return PipelineProcessingStatus.CONTINUE
        else:
            return PipelineProcessingStatus.STOP_PROCESSING

class PipelineProcessingStatus:
    CONTINUE = 0
    DISCARD_NODES = 1
    STOP_PROCESSING = 2

class PipelineContext(object):
    def __init__(self):
        super(PipelineContext, self).__setattr__("values", {})

    def __getattr__(self, attr_name):
        return self.values[attr_name]

    def __setattr__(self, attr_name, value):
        self.values[attr_name] = value

class PipelineProcessor:
    def __init__(self, *pipeline_components):
        self.pipeline_components = pipeline_components

    def __call__(self, root_nodes):
        try:
            stop_processing = False
            local_context = PipelineContext()
            for component in self.pipeline_components:
                status = component(root_nodes, local_context)
                if status == PipelineProcessingStatus.STOP_PROCESSING:
                    return False
                elif status == PipelineProcessingStatus.DISCARD_NODES:
                    break
                elif status != PipelineProcessingStatus.CONTINUE:
                    raise RuntimeError("Status {0} is invalid", status)
        except Exception as e:
            print "Skipping sentence {0}".format(root_nodes)
        return True

class SentenceTuple:
    def __init__(self, predicate_node, subject_node, object_node, modifiers, pred_trigger, pred_polarity):
        self.predicate_node = predicate_node
        self.subject_node = subject_node
        self.object_node = object_node
        self.modifiers = modifiers
        self.predicate_trigger = pred_trigger
        self.predicate_polarity = pred_polarity

    @property
    def is_complex_sentence(self):
        return isinstance(self.object_node, SentenceTuple)

    @property
    def has_unresolved_pronoun(self):
        if self.subject_node.pos_tag == POS_PPER:
            return True
        if self.is_complex_sentence:
            if self.object_node.has_unresolved_pronoun:
                return True
        else:
            if self.object_node.pos_tag  == POS_PPER:
                return True

        return False

    def __str__(self):
        return '{0} "{1}"'.format(self.to_str(), self.predicate_node.flat_text)

    def to_str(self):
        subject_str = self.subject_node.word

        # If we have a Target, concatenate it. If not, add a blank
        if self.is_complex_sentence:
            object_str = BLANK_STR
        else:
            object_str = self.object_node.word

        final_str =  "{0}, {1}, {2}, {3},".format(self.predicate_node.word, subject_str, object_str, " ".join(self.modifiers))

        if self.is_complex_sentence:
            final_str += str(self.object_node.to_str())

        return final_str

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("indir")
    parser.add_argument("triggerfile")
    args = parser.parse_args()

    sentence_counter = SentenceCounter()
    success_counter = SentenceCounter()
    entity_collector = EntityCollector()
    dependency.process_sdewac_splits(
            args.indir,
            PipelineProcessor(
                sentence_counter,
                CountIndicator(sentence_counter, "Processing sentence #"),
                SentenceAnalyser(get_trigger_predicate(args.triggerfile)),
                SentenceFilter([has_named_entity_subject, has_trigger_pred, has_no_unresolved_pronouns, is_not_reflexive]),
                entity_collector,
                success_counter,
                #SentencePrinter()
                ))

    print "Found {0} candidates out of {1} sentences".format(success_counter.count, sentence_counter.count)

    print "Best SUBJ entities:"
    print entity_collector.subj_position_entities_counter.most_common(25)
    print "Best OBJ entities:"
    print entity_collector.obj_position_entities_counter.most_common(25)
    print "Best relations:"
    print entity_collector.relation_counter.most_common(25)

