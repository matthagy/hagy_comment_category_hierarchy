"""
Export the clusters to a JSON file for visualization in the site
"""
import json
import pickle
import re
from dataclasses import dataclass
from typing import cast, Any

import pandas as pd

from cluster import cluster_rms
from generate_summaries import load_summaries
from generate_titles import load_titles
from nodes import BranchNode, TreeNode
from util import COMMENTS_PATH, CLUSTERS_PATH, NODE_EXPORT_TS_PATH, ROOT_DIR, save_using_tmp
from vectorize_comments import load_embeddings

EXPORT_TEMPLATE = '''
export interface NodeData {
  id: string;
  count: number;
  medianLikes: number;
  avgLikes: number;
  maxLikes: number;
  commentRms: number;
  titles: string[];
  summary: string;
  children: NodeData[];
}

export const node_data: NodeData = JSON_NODE_DATA_REPLACE;
'''.strip()

PUNCTUATION_RE = re.compile(r"[^\w\s-]|[^\w\s]-[^\w\s]")


def main():
    top_node: BranchNode = pickle.load(open(CLUSTERS_PATH, 'rb'))
    comments: pd.DataFrame = pd.read_csv(COMMENTS_PATH).set_index('id')
    embeddings: pd.Series = load_embeddings()
    titles = load_titles()
    summaries = load_summaries()
    exporter = Exporter(comments=comments, embeddings=embeddings, titles=titles, summaries=summaries)
    export = exporter.export_node(top_node)

    json_export = json.dumps(export, indent=2)
    export_ts = EXPORT_TEMPLATE.replace('JSON_NODE_DATA_REPLACE', json_export)

    def write(path):
        with open(path, 'wt') as f:
            print(export_ts, file=f)

    # save_using_tmp(NODE_EXPORT_TS_PATH, write)

    def write2(path):
        with open(path, 'wt') as f:
            print(json_export, file=f)

    save_using_tmp(ROOT_DIR / 'site' / 'static' / 'node_data.json', write2)


@dataclass(frozen=True)
class Exporter:
    comments: pd.DataFrame
    embeddings: pd.Series
    titles: pd.Series
    summaries: pd.Series

    def export_node(self, node: TreeNode) -> dict[str, Any]:
        comment_ids = node.get_comment_ids()
        cluster: pd.DataFrame = self.comments.loc[comment_ids]
        likes: pd.Series = cluster['likes']
        obj = {
            'count': len(cluster),
            'medianLikes': round(likes.median(), 1),
            'avgLikes': round(likes.mean(), 1),
            'maxLikes': int(likes.max()),
            'commentRms': round(100 * cluster_rms(comment_ids, self.embeddings), 1),
            'titles': [PUNCTUATION_RE.subn('', t)[0].strip()
                       for t in self.titles.loc[node.node_id].split('|')],
            'summary': self.summaries.loc[node.node_id] or 'n/a',
        }
        if isinstance(node, BranchNode):
            obj.update({
                'id': f'branch{node.node_id}',
                'children': [ec for ec in (self.export_node(child) for child in cast(BranchNode, node).children)
                             if ec is not None],
            })
        else:
            obj.update({
                'id': f'leaf{node.node_id}',
                'children': [],
            })
        return obj


__name__ == '__main__' and main()
