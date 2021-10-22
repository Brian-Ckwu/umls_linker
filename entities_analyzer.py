import pandas as pd

class EntitiesAnalyzer(object):
    def __init__(self, df):
        self._df = df
        self._cats = ["ss", "dx", "drug", "surgery", "non-surgery", "others"]
    
    def count_spans(self) -> pd.DataFrame:
        # scdf: span count DataFrame
        scdf = self._df.groupby(["category", "term"])["span"].nunique().to_frame().reset_index() # DataFrame of number of linked spans
        scdf["span"] = scdf["span"].apply(lambda c : c if c <= 3 else 3) # group together the span counts which are greater than 3
        scdf = scdf.groupby(["category", "span"]).size().to_frame().unstack(level=0)[0] # count the number of each span count (i.e. 0, 1, 2, 3)
        scdf = scdf[self._cats] # re-order columns
        scdf = scdf.append(scdf.sum(axis=0), ignore_index=True).rename(index={4: "total"}) # sum rows
        scdf["total"] = scdf.sum(axis=1) # sum columns
        return scdf