import json
import spacy
import scispacy
from scispacy.abbreviation import AbbreviationDetector
from scispacy.linking import EntityLinker

class UMLSLinker(object):
    def __init__(self):
        # load sciSpacy pipelines
        self._nlp = spacy.load("en_core_sci_lg")
        self._nlp.add_pipe("abbreviation_detector")
        self._nlp.add_pipe("scispacy_linker", config={"resolve_abbreviations": True, "threshold": 0, "linker_name": "umls"})
        # UMLS concept linker
        self._linker = self._nlp.get_pipe("scispacy_linker")
        # UMLS TUI data
        with open("./umls_data/tui.json") as f:
            self._tui2info = json.load(f)
    
    def get_tui_name(self, tui: str) -> str:
        return self._tui2info[tui]["type_name"]

    def choose_tui(self, types: list) -> str:
        # some rules (e.g. the node closest to the leaves)
        return types[0]
    
    def link_term(self, t: str) -> list:
        linked_ents = list()
        tt = "the " + t
        span = self._nlp(tt)[1:]
        subspans = span.ents
        if len(subspans) > 0:
            for subspan in subspans:
                umls_concepts = list()
                for cui, prob in subspan._.kb_ents:
                    concept = self._linker.kb.cui_to_entity[cui]
                    cui_name = concept.canonical_name
                    tui = self.choose_tui(concept.types)
                    tui_name = self._tui2info[tui]["type_name"]
                    umls_concepts.append({
                        "CUI": cui,
                        "CUI_Name": cui_name,
                        "TUI": tui,
                        "TUI_Name": tui_name,
                        "Prob": prob
                    })
                linked_ents.append((str(subspan), umls_concepts))
        return linked_ents