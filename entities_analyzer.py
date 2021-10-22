import pandas as pd

class EntitiesAnalyzer(object):
    def __init__(self, df: pd.DataFrame):
        self._df = df.drop_duplicates()
        self._cats = ["ss", "dx", "drug", "surgery", "non-surgery", "others"]
    
    @property
    def df(self):
        return self._df
    
    @property
    def cats(self):
        return self._cats
    
    def count_spans(self) -> pd.DataFrame:
        # scdf: span count DataFrame
        scdf = self._df.groupby(["category", "term"])["span"].nunique().to_frame().reset_index() # DataFrame of number of linked spans
        scdf["span"] = scdf["span"].apply(lambda c : c if c <= 3 else 3) # group together the span counts which are greater than 3
        scdf = scdf.groupby(["category", "span"]).size().to_frame().unstack(level=0)[0] # count the number of each span count (i.e. 0, 1, 2, 3)
        scdf = scdf[self._cats] # re-order columns
        scdf = scdf.append(scdf.sum(axis=0), ignore_index=True).rename(index={4: "total"}) # sum rows
        scdf["total"] = scdf.sum(axis=1) # sum columns
        return scdf
    
    @staticmethod
    def count_tui_name(df: pd.DataFrame) -> pd.Series:
        return df.groupby("tui_name").size().sort_values(ascending=False)
    
    @staticmethod
    def get_df_by_cat(df: pd.DataFrame, cat: str) -> pd.DataFrame:
        return df[df["category"] == cat]
    
    @staticmethod
    def get_df_by_span_count(df: pd.DataFrame, sc: int) -> pd.DataFrame:
        s = df.groupby("term")["span"].nunique() == sc # Series of the terms of which the span count equals sc
        terms = s[s == True].index
        return df[df["term"].isin(terms)]
    
    @staticmethod
    def get_df_by_tui_name(df: pd.DataFrame, tui_name: str) -> pd.DataFrame:
        return df[df["tui_name"] == tui_name]