## busines email : id, subject, timestamp, body, from, to, direction, domain

import pandas as pd


df1 = pd.read_csv( "../data/emails.csv" )
df2 = pd.read_csv("../data/emails1.csv")

df = pd.concat([df1, df2], ignore_index=True)
df['timestamp'] = df['timestamp'].astype(str).str[:20]
df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
print(df.info())
print(df.head())
print(df['timestamp'])
print(df.isnull().sum())
df = df.dropna()
print( df.isnull().sum() )

