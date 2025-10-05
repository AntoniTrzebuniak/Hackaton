import pandas as pd
from datetime import datetime, timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from transformers import pipeline

generator = pipeline("text2text-generation", model="google/flan-t5-base")


# Funkcja wczytująca i łącząca pliki
def load_and_merge(file1, file2):
    headers = ["id", "subject", "timestamp", "body", "from", "to", "direction", "domain"]

    df1 = pd.read_csv(file1, header=None, names=headers, skiprows=1, encoding="utf-8")
    df2 = pd.read_csv(file2, header=None, names=headers, skiprows=1, encoding="utf-8")

    df1 = df1[df1['id'] != "id"]
    df2 = df2[df2['id'] != "id"]

    merged_df = pd.concat([df1, df2], ignore_index=True)
    return merged_df


# Funkcja wyodrębniająca maile z dzisiaj
def get_yesterdays_emails(df):
    yesterday = (datetime.today() - timedelta(days=1)).date()
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', infer_datetime_format=True)
    df = df.dropna(subset=['timestamp'])
    return df[df['timestamp'].dt.date == yesterday], df[df['timestamp'].dt.date < yesterday]

# Funkcja klasteryzacji maili
def cluster_emails(df_old, n_clusters=5):
    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(df_old['body'] + " " + df_old['subject'])
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    clusters = kmeans.fit_predict(X)
    df_old['cluster'] = clusters
    return df_old, vectorizer, kmeans


# Funkcja przypisująca nowe maile do istniejących klastrów
def assign_clusters(df_today, vectorizer, kmeans, threshold=0.8):
    X_new = vectorizer.transform(df_today['body'] + " " + df_today['subject'])
    clusters = kmeans.predict(X_new)
    similarities = cosine_similarity(X_new, kmeans.cluster_centers_)
    max_similarities = similarities.max(axis=1)

    df_today['cluster'] = clusters
    df_today['similarity'] = max_similarities
    df_today['cluster_valid'] = df_today['similarity'] >= threshold

    return df_today


# Funkcja zapytania użytkownika
def prompt_user_and_generate_response(email_row):
    print(f"\n📩 Nowy email od: {email_row['from']}")
    print(f"Temat: {email_row['subject']}")
    print(f"Tresc: {email_row['body']}\n")

    choice = input("Czy chcesz wygenerować odpowiedź na tego maila? (tak/nie): ").strip().lower()
    if choice == "tak":
        response = generate_ai_response(email_row)
        print(f"\n💬 Odpowiedź wygenerowana:\n{response}")
        return response
    return None


# Przykładowa funkcja generująca odpowiedź AI (placeholder)
def generate_ai_response(email_row):
    # Tworzymy czysty prompt — bez "Napisz..." w treści maila
    prompt = (
        f"Email od: {email_row['from']}\n"
        f"Temat: {email_row['subject']}\n"
        f"Tresc: {email_row['body']}\n\n"
        f"Napisz krótką i uprzejmą odpowiedź."
    )

    result = generator(
        prompt,
        max_new_tokens=150,
        do_sample=True,
        temperature=0.7,
        top_p=0.9
    )

    generated_text = result[0]['generated_text']

    # Usuwamy powtórzoną treść maila w odpowiedzi
    if email_row['body'] in generated_text:
        generated_text = generated_text.replace(email_row['body'], "").strip()

    return generated_text


# --- GŁÓWNY SKRYPT ---
if __name__ == "__main__":
    file1 = "../data/emails.csv"
    file2 = "../data/emails1.csv"

    df = load_and_merge(file1, file2)
    df_today, df_old = get_yesterdays_emails(df)

    print(f"Znaleziono {len(df_today)} maili z wczoraj i {len(df_old)} maili z wcześniejszych dni.")

    df_old, vectorizer, kmeans = cluster_emails(df_old, n_clusters=5)
    df_today = assign_clusters(df_today, vectorizer, kmeans, threshold=0.8)

    for _, row in df_today.iterrows():
        if row['cluster_valid']:
            print(f"\n📩 Mail pasuje do klastra {row['cluster']} z podobieństwem {row['similarity']:.2f}")
            response = prompt_user_and_generate_response(row)
            if response:
                print(f"\n💡 Wygenerowana odpowiedź:\n{response}")
        else:
            print(f"\nMail od {row['from']} nie pasuje do żadnego istniejącego klastra.")