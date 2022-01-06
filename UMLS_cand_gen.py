import os
import json
import pandas as pd
from tqdm import tqdm
from typing import List
from scispacy.candidate_generation import CandidateGenerator, MentionCandidate

class UMLSCandidateGenerator(object):
    def __init__(self, kb: str):
        self._cand_gen = CandidateGenerator(name=kb)
        self._fields = ["term", "abbr_resolved", "alias", "similarity", "cui", "cui_name", "tui", "tui_name"]
        # UMLS TUI data
        tui_file = os.path.join(os.path.dirname(__file__), r".\umls_data\tui.json")
        with open(tui_file) as f:
            self._tui2info = json.load(f)
        # Load abbreviations file
        abbr_file = os.path.join(os.path.dirname(__file__), r".\umls_data\abbr2full.json")
        with open(abbr_file, encoding="utf-8") as f:
            self._abbr2full = json.load(f)

    def convert_abbr(self, medical_term: str) -> str:
        return self._abbr2full.get(medical_term, medical_term)

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
        d["cui_name"] = concept.canonical_name # concept.types[0] might not be the most probable way
        if concept.types:
            d["tui"] = concept.types[0]
            d["tui_name"] = self._tui2info[d["tui"]]["type_name"]

        return d
    
    def build_concept_lexicon(self, vocab: List[str], num_aliases: int = 5) -> pd.DataFrame:
        lex_d = {field: list() for field in self._fields}

        print(f"Building concept lexicon...")
        for term in tqdm(vocab):
            abbr_resolved = self.convert_abbr(term)
            cands = self.find_cands(medical_term=abbr_resolved, k=num_aliases)
            tuples = self.cands_to_tuples(cands)
            for t in tuples:
                d = self.tuple_to_entity_fields(cand_tuple=t)
                d["term"] = term
                d["abbr_resolved"] = abbr_resolved
                for field in self._fields:
                    lex_d[field].append(d[field])
        
        return pd.DataFrame(lex_d)

class SNOMEDRxCandidateGenerator(UMLSCandidateGenerator):
    def __init__(self):
        super().__init__(kb="umls")
        # SNOMED_CT CUIs data
        snomedct_file = os.path.join(os.path.dirname(__file__), r".\umls_data\snomed_cuis.txt")
        self._snomed_cuis = set()
        with open(snomedct_file) as f:
            for line in f:
                cui = line.rstrip()
                self._snomed_cuis.add(cui)
        # RxNorm CUIs data
        rxnorm_file = os.path.join(os.path.dirname(__file__), r".\umls_data\rxnorm_cuis.txt")
        self._rxnorm_cuis = set()
        with open(rxnorm_file) as f:
            for line in f:
                cui = line.rstrip()
                self._rxnorm_cuis.add(cui)
        # SNOMED + RxNorm Cuis
        self._whole_cuis = self._snomed_cuis | self._rxnorm_cuis
        # Resolve to a unique concept and alias
        self._unique = True
    
    def set_unique(self, flag: bool):
        self._unique = flag
    
    def find_cands(self, medical_term: str, k: int = 5) -> List[MentionCandidate]: # when the cand_gen object is called as a function
        cands = self._cand_gen([medical_term], k)[0]
        snomed_cands = list()
        for cand in cands:
            if cand.concept_id in self._whole_cuis:
                snomed_cands.append(cand)
                if self._unique:
                    break

        return snomed_cands

    def cands_to_tuples(self, candidates: List[MentionCandidate]) -> List[tuple]:
        tuples = list()
        for cand in candidates:
            cui = cand.concept_id
            for alias, similarity in zip(cand.aliases, cand.similarities):
                t = (alias, similarity, cui)
                tuples.append(t)
        tuples = sorted(tuples, key=lambda t: t[1], reverse=True)
        return [tuples[0]] if self._unique else tuples
    
    def build_concept_lexicon(self, vocab: List[str], num_aliases: int = 5) -> pd.DataFrame:
        lex_d = {field: list() for field in self._fields}

        print(f"Building concept lexicon...")
        for term in tqdm(vocab):
            abbr_resolved = self.convert_abbr(term)
            cands = self.find_cands(medical_term=abbr_resolved, k=num_aliases)
            if cands:
                tuples = self.cands_to_tuples(cands)
                for t in tuples:
                    d = self.tuple_to_entity_fields(cand_tuple=t)
                    d["term"] = term
                    d["abbr_resolved"] = abbr_resolved
                    for field in self._fields:
                        lex_d[field].append(d[field])
            else:
                lex_d["term"].append(term)
                lex_d["abbr_resolved"].append(abbr_resolved)
                for field in self._fields:
                    if field not in ["term", "abbr_resolved"]:
                        lex_d[field].append("NOT_FOUND")
            
        return pd.DataFrame(lex_d)