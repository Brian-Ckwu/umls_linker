import json
import spacy
import scispacy
from scispacy.abbreviation import AbbreviationDetector
from scispacy.linking import EntityLinker

class UMLSLinker(object):
    def __init__(self, ):
        # load sciSpacy pipelines
        self._nlp = spacy.load("en_core_sci_lg")
        self._nlp.add_pipe("abbreviation_detector")
        self._nlp.add_pipe("scispacy_linker", config={"resolve_abbreviations": True, "threshold": 0, "linker_name": "umls"})
        # UMLS concept linker
        self._linker = self._nlp.get_pipe("scispacy_linker")
