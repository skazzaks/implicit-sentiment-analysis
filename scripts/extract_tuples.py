import subprocess
import argparse
import dependency
import copy

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

class has_trigger_pred:
    def __init__(self, triggers_filename):
        with open(triggers_filename, "r") as f:
            self.triggers = set([w.strip().lower() for w in f])

    def __call__(self, sentence):
        for word in sentence.predicate_node.all_tree_nodes:
            if word.lemma.lower() in self.triggers:
                return True
        else:
            return False

def has_unmodified_predicate(sentence):
    return len(sentence.predicate_node.find_children_by_label("MO")) == 0

class SentenceFilterProcessor:
    def __init__(self, conditions = []):
        self.conditions = copy.copy(conditions)
        self.success_count = 0

    def __call__(self, root_nodes):
        longest_node = max(root_nodes, key = lambda n: n.child_count)
        sentence = analyse_sentence(longest_node)
        if sentence:
            if all((condition(sentence) for condition in self.conditions)):
                self.success_count += 1
                print sentence
        return True

class SentenceTuple:
    def __init__(self, predicate_node, subject_node, object_node, modifiers):
        self.predicate_node = predicate_node
        self.subject_node = subject_node
        self.object_node = object_node
        self.modifiers = modifiers

    @property
    def is_complex_sentence(self):
        return isinstance(self.object_node, SentenceTuple)

    @property
    def has_unresolved_pronoun(self):
        if self.subject_node.pos_tag == POS_PPER:
            return True
        if self.is_complex_sentence:
            if self.object_node.subject_node.pos_tag == POS_PPER or self.object_node.object_node.pos_tag == POS_PPER:
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
        
        final_str =  "{0}, {1}, {2}, {3}, ".format(self.predicate_node.word, subject_str, object_str, " ".join(self.modifiers))
        
        if self.is_complex_sentence:
            final_str += str(self.object_node.to_str())
      
        return final_str
    
def analyse_sentence(root_node):
    subject, dir_object = get_subject_and_object_from_node(root_node)
    modifiers = get_modifiers(root_node)
	
    if subject and dir_object:
        return SentenceTuple(root_node, subject, dir_object, modifiers)

    comp_phrase = root_node.find_child_by_label("OC")

    if comp_phrase:
        embeded_sentence = analyse_sentence(comp_phrase)

        if subject and embeded_sentence:
            return SentenceTuple(root_node, subject, embeded_sentence, modifiers)

def get_subject_and_object_from_node(root_node):
    subject = root_node.find_child_by_label("SB")
    dir_object = root_node.find_child_by_label("OA")
    return subject, dir_object

# Retrieves the set of modifiers (right now just adverbs) that occur
# at the provided level of the sentence
def get_modifiers(root_node):
    results = list(root_node.find_children_by_POS_tag(POS_ADV))
    results.extend(list(root_node.find_children_by_POS_tag(POS_NICHT)))
    return results
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("indir")
    parser.add_argument("triggerfile")
    args = parser.parse_args()


    filter_processor = SentenceFilterProcessor([is_complex_sentence, has_named_entity_subject, has_trigger_pred(args.triggerfile), has_no_unresolved_pronouns])
    dependency.process_sdewac_splits(args.indir, filter_processor)
    print "Found {0} candidates".format(filter_processor.success_count)

