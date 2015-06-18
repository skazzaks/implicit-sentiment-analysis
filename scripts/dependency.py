import os
import gzip

class DependencyNode:
    def __init__(self, id, word, lemma, pos_tag):
        self.id = id
        self.word = word
        self.lemma = lemma
        self.pos_tag = pos_tag
        self.children = []
        self.parent = None

    def add_child(self, child, label):
        self.children.append((child, label))
        child.parent = self

    @property
    def is_root(self):
        return self.parent == None

    @property
    def child_count(self):
        return len(self.children)

    def __str__(self):
        return self.to_str()

    def to_str(self, level = 0, label = None):
        base_str = "{1} ({2}); {3}".format(self.id, self.word, self.lemma, self.pos_tag)

        if label:
            base_str = "{0}: {1}".format(label,base_str)

        ident_str = "\t" * level
        base_str = ident_str + base_str

        str_components = [base_str]
        for child, label in sorted(self.children, key=lambda cl: cl[0].id):
            str_components.append(child.to_str(level + 1, label))

        return "\n".join(str_components)

    def find_children_by_label(self, match_label):
        matches = []
        for child, label in self.children:
            if label == match_label:
                matches.append(child)
        return matches

    def find_child_by_label(self, match_label):
        result = self.find_children_by_label(match_label)
        if len(result) != 1:
            return None
        else:
            return result[0]
	
    # Finds all of the children that have the given pos_tag
    def find_children_by_POS_tag(self, pos_tag):
        for child, label in self.children:
            if child.pos_tag == pos_tag:
                yield child.word


    @property
    def flat_text(self):
        all_nodes = self.all_tree_nodes
        all_nodes.sort(key = lambda k: k.id)

        return " ".join(map(lambda n: n.word, all_nodes))

    @property
    def all_tree_nodes(self):
        result = []
        for child in self.children:
            for node in child[0].all_tree_nodes:
                result.append(node)
        result.append(self)
        return result

def process_conll_stream(instream, processor):
    while True:
        new_parse = decode_conll_parse(instream)
        if new_parse is None:
            break
        should_continue = processor(new_parse)
        if not should_continue:
            break

def process_sdewac_splits(root_directory, processor):
    for file_ in os.listdir(root_directory):
        file_path = os.path.join(root_directory, file_)
        with gzip.open(file_path, 'rb') as f:
            process_conll_stream(f, processor)

def decode_conll_parse(instream):
    raw_nodes_by_parents = {}
    for line in instream:
        if len(line.strip()) == 0:
            break
        components = line.split()
        id = int(components[0].split("_")[1])
        raw_nodes_by_parents.setdefault(int(components[9]), []).append((DependencyNode(id, components[1], components[3], components[5]), components[11]))

    if len(raw_nodes_by_parents) == 0:
        return None

    root_nodes = list(map(lambda n: n[0], raw_nodes_by_parents[0]))
    for root_node in root_nodes:
        unprocessed_nodes = [root_node]
        while len(unprocessed_nodes) > 0:
            node = unprocessed_nodes.pop()
            for child, relation_label in raw_nodes_by_parents.get(node.id, []):
                node.add_child(child, relation_label)
                unprocessed_nodes.append(child)

    return root_nodes

