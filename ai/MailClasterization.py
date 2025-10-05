import pandas as pd
import tensorflow_hub as hub
from sklearn.cluster import KMeans

# -------------------------------
# 1. Wczytanie danych
# -------------------------------
df1 = pd.read_csv("../data/emails.csv")
df2 = pd.read_csv("../data/emails1.csv")
df = pd.concat([df1, df2], ignore_index=True)

# Łączenie subject i body
texts = df['subject'].fillna('') + ' ' + df['body'].fillna('')

# -------------------------------
# 2. Generowanie embeddingów
# -------------------------------
embed_model = hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")
embeddings = embed_model(texts.tolist())
embeddings_np = embeddings.numpy()

# -------------------------------
# 3. Klasteryzacja KMeans
# -------------------------------
num_clusters = 10
kmeans = KMeans(n_clusters=num_clusters, random_state=42)
df['cluster'] = kmeans.fit_predict(embeddings_np)

# -------------------------------
# 4. Generowanie nazw tematów dla klastrów
# -------------------------------
# proste podejście: temat = najczęściej występujące słowo w subject pierwszych maili klastra
cluster_topics = {}
for cluster_id in df['cluster'].unique():
    sample_subjects = df[df['cluster'] == cluster_id]['subject'].dropna().head(5).tolist()
    if sample_subjects:
        # bierzemy pierwsze 3 słowa z pierwszego maila jako "temat"
        topic_name = " ".join(sample_subjects[0].split()[:3])
    else:
        topic_name = f"Klastr {cluster_id}"
    cluster_topics[cluster_id] = topic_name

df['topic_name'] = df['cluster'].map(cluster_topics)

# -------------------------------
# 5. Wyświetlanie powiadomień
# -------------------------------
for cluster_id, topic_name in cluster_topics.items():
    count = df[df['cluster'] == cluster_id].shape[0]
    print(f"Masz {count} wiadomości w temacie '{topic_name}'")
