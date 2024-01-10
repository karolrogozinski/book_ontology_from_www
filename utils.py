import string

import spacy
from nltk.corpus import stopwords
import torch
import numpy as np

from collections import defaultdict
from transformers import AutoTokenizer, AutoModel

from sklearn.cluster import AgglomerativeClustering


MODEL_NAMES = {
        "herbert-klej-cased-v1": {
            "tokenizer": "allegro/herbert-klej-cased-tokenizer-v1",
            "model": "allegro/herbert-klej-cased-v1",
        },
        "herbert-base-cased": {
            "tokenizer": "allegro/herbert-base-cased",
            "model": "allegro/herbert-base-cased",
        },
        "herbert-large-cased": {
            "tokenizer": "allegro/herbert-large-cased",
            "model": "allegro/herbert-large-cased",
        },
    }


TOKENIZER = AutoTokenizer.from_pretrained("allegro/herbert-large-cased")
MODEL = AutoModel.from_pretrained(
        MODEL_NAMES["herbert-large-cased"]["model"]
    )

SPACY_CORE = spacy.load("pl_core_news_sm")
STOP_WORDS = set(stopwords.words("polish"))


def is_noun_or_adj(token):
    return token.pos_ in {'NOUN', 'ADJ'}


def clear_embeddings(embeddings: list()) -> dict():
    return {
        word: embeddings[word]
        for word in embeddings
        if is_noun_or_adj(SPACY_CORE(word)[0])
    }


def calculate_cluster_centers(
        embeddings_matrix: list(), clusters: list()) -> list():

    num_clusters = len(np.unique(clusters))
    cluster_centers = np.zeros((num_clusters, embeddings_matrix.shape[1]))

    for cluster_id in range(num_clusters):
        cluster_indices = np.where(clusters == cluster_id)
        cluster_center = np.mean(embeddings_matrix[cluster_indices], axis=0)
        cluster_centers[cluster_id] = cluster_center

    return cluster_centers


def create_embeddings(tokens: list()) -> list():
    embeddings = {}
    for word in tokens:
        tokens = TOKENIZER.encode(word.lower(), add_special_tokens=False)
        input_ids = torch.tensor(tokens).unsqueeze(0)

        with torch.no_grad():
            outputs = MODEL(input_ids)

        embedding = outputs.last_hidden_state[:, 0, :]
        embeddings[word] = embedding[0]

    return embeddings


def generate_tokens(text: str) -> list():
    doc = SPACY_CORE(text)
    return [
        token.lemma_ for token in doc
        if token.text.lower() not in STOP_WORDS
        and token.text not in string.punctuation and len(token) > 2
    ]


def cluster_embeddings(embeddings: dict(), keywords_num):
    embeddings_matrix = np.array(
        [tensor.numpy() for tensor in embeddings.values()]
    )

    keywords_num = np.min(
        [keywords_num, len(embeddings.values())]
    )

    normalized_embeddings = embeddings_matrix / np.linalg.norm(
        embeddings_matrix, axis=1, keepdims=True
    )
    agg_clustering = AgglomerativeClustering(
        n_clusters=keywords_num,
        affinity='cosine',
        linkage='average'
    )
    clusters = agg_clustering.fit_predict(normalized_embeddings)

    for (word, tensor), cluster in zip(embeddings.items(), clusters):
        embeddings[word] = [cluster, tensor]

    cluster_centers = calculate_cluster_centers(embeddings_matrix, clusters)

    return embeddings, cluster_centers


def get_representative_words(
        embeddings: dict(), cluster_centers: list()) -> list():

    representative_words = defaultdict(
        lambda: {'word': None, 'embedding': None})
    for word, (cluster, embedding) in embeddings.items():

        if representative_words[cluster]['word'] is None or np.dot(
                embedding, cluster_centers[cluster]
                ) < np.dot(representative_words[cluster]['embedding'],
                           cluster_centers[cluster]):

            representative_words[cluster]['word'] = word
            representative_words[cluster]['embedding'] = embedding

    return [data["word"] for _, data in representative_words.items()]


def get_keywords(text: str, keywords_num: int = 10) -> list():
    # Tworzenie tokenów z pojedynczych słów, stopwords, lematyzacja
    tokens = generate_tokens(text)

    # Tworzenie embeddingów dla każdego słowa
    embeddings = create_embeddings(tokens)

    # Usuwanie zbędnych embeddingów
    embeddings = clear_embeddings(embeddings)

    # Klastrowanie słów
    embeddings, cluster_centers = cluster_embeddings(embeddings, keywords_num)

    # Szukanie reprezentatywnego słowa dla każdego klastra
    keywords = get_representative_words(embeddings, cluster_centers)
    return keywords
