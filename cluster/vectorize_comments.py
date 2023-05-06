"""
Computes comment embeddings using OpenAI's `text-embedding-ada-002` model
"""

import numpy as np
import pandas as pd

from util import (COMMENTS_PATH, COMMENT_EMBEDDINGS_PATH, get_embedding, set_openai_key, count_tokens,
                  URL_REGEX, iter_with_progress, save_using_tmp)


def main():
    comments: pd.DataFrame = pd.read_csv(COMMENTS_PATH).set_index('id')
    comments['body'] = comments['body'].map(lambda b: URL_REGEX.subn(' ', b)[0])
    comments['token_count'] = comments['body'].map(count_tokens)
    comments = comments[comments['token_count'].between(80, 1000)]

    embeddings: pd.Series = load_embeddings()
    to_compute_comment_ids = set(comments.index) - set(embeddings.index)
    print(f"Computing embeddings for {len(to_compute_comment_ids)} comments")
    if not to_compute_comment_ids:
        return

    set_openai_key()
    for i, comment_id in enumerate(iter_with_progress(to_compute_comment_ids, desc="Embedding comments")):
        comment = comments.loc[comment_id]
        embedding = get_embedding(comment['body'])
        embeddings[comment_id] = embedding
        if not i % 10:
            save_embeddings(embeddings)
    save_embeddings(embeddings)


def load_embeddings() -> pd.Series:
    if not COMMENT_EMBEDDINGS_PATH.exists():
        return pd.Series(dtype=object, name='embedding')
    arrays = np.load(COMMENT_EMBEDDINGS_PATH)
    return pd.Series(list(arrays['values']), index=arrays['index'], name='embedding', dtype=object)


def save_embeddings(embeddings: pd.Series):
    def write(path):
        np.savez_compressed(path, index=embeddings.index, values=np.vstack(embeddings.values).astype(np.float32))

    save_using_tmp(COMMENT_EMBEDDINGS_PATH, write)


__name__ == '__main__' and main()
