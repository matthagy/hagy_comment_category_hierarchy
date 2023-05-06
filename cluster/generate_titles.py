"""
Use ChatGPT API to generate 5 titles for each cluster
"""

import pickle

import pandas as pd

from nodes import BranchNode
from util import (CLUSTERS_PATH, TITLES_PATH, load_comments_wo_urls, save_using_tmp, sample_node_bodies,
                  set_openai_key, chat_complete)

N_TITLES = 5
TEMPERATURE = 0.8
MAX_TOKENS = 8
TITLE_QUERY_TEMPLATE = '''
Suggest a short, yet descriptive name for the group of similar comments below.
Response should be at most 5 words in length.
Avoid generic names like "discussion" or "comments".
Respond only with the group name, do not provide any explanation, formatting, or punctuation.
Comments:
{comment_bodies}
'''.strip()


def main():
    top_node: BranchNode = pickle.load(open(CLUSTERS_PATH, 'rb'))
    titles = load_titles()

    nodes_to_titles = [n for n in top_node.iter_nodes() if n.node_id not in titles.index]
    print(f"Generating titles for {len(nodes_to_titles)} nodes")
    if not nodes_to_titles:
        return

    set_openai_key()
    comments = load_comments_wo_urls()
    for node in nodes_to_titles:
        bodies = sample_node_bodies(node, comments)
        query = TITLE_QUERY_TEMPLATE.format(comment_bodies=bodies)
        results = chat_complete(
            query=query, temperature=TEMPERATURE, n=N_TITLES, max_tokens=MAX_TOKENS
        )
        comment_titles = [r['message']['content'] for r in results]
        print(f'{node.node_id} {len(node.get_comment_ids())=}: {comment_titles}')
        titles = pd.concat([titles,
                            pd.Series('|'.join(t.replace('|', '') for t in comment_titles), index=[node.node_id])])
        save_titles(titles)


def load_titles() -> pd.Series:
    if not TITLES_PATH.exists():
        return pd.Series(dtype=object, name='titles', index=pd.Index([], name='node_id'))
    return pd.read_csv(TITLES_PATH).set_index('node_id')['titles']


def save_titles(titles: pd.Series):
    titles.name = 'titles'
    titles.index.name = 'node_id'
    save_using_tmp(TITLES_PATH, titles.to_csv)


__name__ == '__main__' and main()
