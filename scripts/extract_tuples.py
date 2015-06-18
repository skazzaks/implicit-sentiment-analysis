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

def has_trigger_pred(sentence):
    return sentence.predicate_trigger is not None 

class get_trigger_predicate:
    def __init__(self, triggers_filename):
        with open(triggers_filename, "r") as f:
            self.triggers = set([(w.split()[0].strip().lower(), 1 if w.split()[1] == "+" else -1) for w in f if not w.startswith("#")])

    def __call__(self, predicate):
        match = [(trig, polarity) for trig, polarity in self.triggers if predicate.lemma.lower() == trig]
        if len(match) is not 0:
            #print predicate.lemma
            return match[0][0], match[0][1] 
        else:
            return [None, None] 

def has_unmodified_predicate(sentence):
    return len(sentence.predicate_node.find_children_by_label("MO")) == 0

class SentenceFilterProcessor:
    def __init__(self, get_trigger_word, conditions = []):
        self.conditions = copy.copy(conditions)
        self.success_count = 0
        self.get_trigger_word = get_trigger_word

    def __call__(self, root_nodes):
        longest_node = max(root_nodes, key = lambda n: n.child_count)
        sentence = analyse_sentence(longest_node, self.get_trigger_word)
        if sentence:
            if all((condition(sentence) for condition in self.conditions)):
                self.success_count += 1
                print sentence
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
    
def analyse_sentence(root_node, get_trigger_and_polarity):
    subject, dir_object = get_subject_and_object_from_node(root_node)
    modifiers = get_modifiers(root_node)
    trigger_pred, pred_polarity = get_trigger_and_polarity(root_node)
    #if trigger_pred is not None:
        #print trigger_pred + " " + str(pred_polarity)
    if subject and dir_object:
        return SentenceTuple(root_node, subject, dir_object, modifiers, trigger_pred, pred_polarity)

    comp_phrase = root_node.find_child_by_label("OC")

    if comp_phrase:
        embeded_sentence = analyse_sentence(comp_phrase, get_trigger_and_polarity)

        if subject and embeded_sentence:
            return SentenceTuple(root_node, subject, embeded_sentence, modifiers, trigger_pred, pred_polarity)

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


    filter_processor = SentenceFilterProcessor(get_trigger_predicate(args.triggerfile),[is_complex_sentence, has_named_entity_subject, has_trigger_pred, has_no_unresolved_pronouns])
    dependency.process_sdewac_splits(args.indir, filter_processor)
    print "Found {0} candidates".format(filter_processor.success_count)

