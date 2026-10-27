import pandas as pd

df = pd.read_csv(r'data\llm\hybrid_results.csv')   # <-- your actual file
print(df.columns.tolist())                          # check the column names first

tam = df[df['label'] == 'tampered']
hit = tam['verdict'].isin(['LIKELY_TIMESTOMPING', 'SUSPICIOUS'])
print(tam.assign(hit=hit).groupby('experiment')['hit'].agg(['sum', 'count', 'mean']))