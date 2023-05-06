"""
Use ChatGPT API to generate a summary for each cluster
"""

import pickle

import pandas as pd

from nodes import BranchNode
from util import (CLUSTERS_PATH, SUMMARIES_PATH, load_comments_wo_urls, save_using_tmp, sample_node_bodies,
                  set_openai_key, chat_complete_stream)

TEMPERATURE = 1.0
TITLE_QUERY_TEMPLATE = '''
Summarize the group of similar comments from one authors below.
Focus on the main themes or viewpoints expressed within the comments.
Output one to three paragraphs of text.
Comments:
{comment_bodies}
'''.strip()


def main():
    top_node: BranchNode = pickle.load(open(CLUSTERS_PATH, 'rb'))
    summaries = load_summaries()

    nodes_to_titles = [n for n in top_node.iter_nodes() if n.node_id not in summaries.index]
    print(f"Generating summaries for {len(nodes_to_titles)} nodes")
    if not nodes_to_titles:
        return

    set_openai_key()
    comments = load_comments_wo_urls()
    for node in nodes_to_titles:
        bodies = sample_node_bodies(node, comments)
        query = TITLE_QUERY_TEMPLATE.format(comment_bodies=bodies)
        print(f'{node.node_id} {len(node.get_comment_ids())=}')
        summary = chat_complete_stream(query=query, temperature=TEMPERATURE)
        summaries = pd.concat([summaries, pd.Series([summary], index=[node.node_id])])
        save_summaries(summaries)


def load_summaries() -> pd.Series:
    if not SUMMARIES_PATH.exists():
        return pd.Series(dtype=object, name='titles', index=pd.Index([], name='node_id'))
    return pd.read_csv(SUMMARIES_PATH).set_index('node_id')['summary']


def save_summaries(titles: pd.Series):
    titles = titles.sort_index()
    titles.name = 'summary'
    titles.index.name = 'node_id'
    save_using_tmp(SUMMARIES_PATH, titles.to_csv)


__name__ == '__main__' and main()
