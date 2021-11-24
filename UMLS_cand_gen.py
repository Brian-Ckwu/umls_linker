import os
import json
import pandas as pd
from tqdm import tqdm
from typing import List
from scispacy.candidate_generation import CandidateGenerator, MentionCandidate

class UMLSCandidateGenerator(object):
    def __init__(self):
        self._cand_gen = CandidateGenerator(name="umls")
        self._fields = ["term", "alias", "similarity", "cui", "cui_name", "tui", "tui_name"]
        # UMLS TUI data
        file_path = os.path.join(os.path.dirname(__file__), r".\umls_data\tui.json")
        with open(file_path) as f:
            self._tui2info = json.load(f)

    def find_cands(self, medical_term: str, k: int = 5) -> List[MentionCandidate]: # when the cand_gen object is called as a function
        return self._cand_gen([medical_term], k)[0]

    def cands_to_tuples(self, candidates: List[MentionCandidate]) -> List[tuple]:
        tuples = list()
        for cand in candidates:
            cui = cand.concept_id
            for alias, similarity in zip(cand.aliases, cand.similarities):
                t = (alias, similarity, cui)
                tuples.append(t)
        return sorted(tuples, key=lambda t: t[1], reverse=True)
    
    def tuple_to_entity_fields(self, cand_tuple: tuple) -> dict: # (alias, similarity, cui) -> {alias, similarity, cui, cui_name, tui, tui_name}
        d = {field: None for field in self._fields[1:]}
    
        concept = self._cand_gen.kb.cui_to_entity[cand_tuple[2]]
        d["alias"], d["similarity"], d["cui"] = cand_tuple
        d["cui_name"], d["tui"] = concept.canonical_name, concept.types[0], # concept.types[0] might not be the most probable way
        d["tui_name"] = self._tui2info[d["tui"]]["type_name"]

        return d
    
    def build_concept_lexicon(self, vocab: List[str], num_aliases: int = 5) -> pd.DataFrame:
        lex_d = {field: list() for field in self._fields}

        print(f"Building concept lexicon...")
        for term in tqdm(vocab):
            cands = self.find_cands(medical_term=term, k=num_aliases)
            tuples = self.cands_to_tuples(cands)
            for t in tuples:
                d = self.tuple_to_entity_fields(cand_tuple=t)
                d["term"] = term
                for field in self._fields:
                    lex_d[field].append(d[field])
        
        return pd.DataFrame(lex_d)