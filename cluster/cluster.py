"""
Performs agglomerative clustering on the embeddings and collapse select nodes
"""

from typing import cast, Iterable

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering

from nodes import TreeNode, LeafNode, BranchNode
from util import CLUSTERS_PATH, save_pickle_using_tmp
from vectorize_comments import load_embeddings

MAX_LEAF_RMS = 0.205
MAX_BRANCH_CHILDREN = 5


def main():
    embeddings: pd.Series = load_embeddings()
    initial_clusters = create_initial_binary_clusters(embeddings)
    consolidated_clusters = consolidate_nodes(initial_clusters, embeddings)
    print('-' * 80)
    print_tree(consolidated_clusters, embeddings)
    save_pickle_using_tmp(CLUSTERS_PATH, consolidated_clusters)


def create_initial_binary_clusters(embeddings: pd.Series) -> BranchNode:
    stacked_embeddings = np.vstack(embeddings.values).astype(np.float64)
    model = AgglomerativeClustering(distance_threshold=0, n_clusters=None)
    model = model.fit(stacked_embeddings)

    nodes: list[TreeNode] = [LeafNode(node_id=i, comment_ids=(embeddings.index[i],))
                             for i in range(model.n_leaves_)]
    for i, j in model.children_:
        node = BranchNode(node_id=len(nodes), children=(nodes[i], nodes[j]))
        nodes.append(node)
        nodes[i].parent = node
        nodes[j].parent = node

    top_node: BranchNode = cast(BranchNode, nodes[-1])
    assert isinstance(top_node, BranchNode)
    assert top_node.parent is None
    return top_node


def embeddings_rms(embeddings: np.ndarray) -> float:
    return np.mean(np.sum(np.square(embeddings - np.mean(embeddings, axis=0)), axis=1))


def cluster_rms(comment_ids: Iterable[int], embeddings: pd.Series) -> float:
    return embeddings_rms(np.vstack(embeddings.loc[comment_ids].values))


def consolidate_nodes(node: TreeNode, embeddings: pd.Series, depth: int = 0) -> TreeNode:
    if isinstance(node, LeafNode):
        return node
    node = cast(BranchNode, node)
    comment_ids = node.get_comment_ids()
    rms = cluster_rms(comment_ids, embeddings)
    prefix = '-' * depth

    if rms < MAX_LEAF_RMS:
        print(f'{prefix}consolidating leaf {node.node_id} with {len(comment_ids)=}, {rms=:0.3f}')
        return LeafNode(node_id=node.node_id, comment_ids=tuple(comment_ids))
    else:
        children = tuple(consolidate_nodes(child, embeddings=embeddings, depth=depth + 1)
                         for child in node.children)
        grandchildren = []
        for child in children:
            if isinstance(child, BranchNode):
                grandchildren.extend(cast(BranchNode, child).children)
            else:
                grandchildren.append(child)
        if len(grandchildren) <= MAX_BRANCH_CHILDREN:
            print(f'{prefix}consolidating branch {node.node_id} with {len(children)=} {len(grandchildren)=}')
            children = tuple(grandchildren)
        else:
            print(f'{prefix}splitting branch {node.node_id} with {len(comment_ids)=}, {rms=:0.3f}, {len(children)=}')

        new_node = BranchNode(node_id=node.node_id, children=children)
        for child in children:
            child.parent = new_node
        return new_node


def print_tree(node: TreeNode, embeddings: pd.Series, depth: int = 0):
    prefix = "-" * depth
    comment_ids = node.get_comment_ids()
    rms = cluster_rms(comment_ids, embeddings)
    if isinstance(node, LeafNode):
        print(f'{prefix}leaf({node.node_id}) {rms=:0.3f} {len(comment_ids)=}')
    else:
        node = cast(BranchNode, node)
        print(f'{prefix}branch({node.node_id}) {rms=:0.3f} {len(node.children)=} {len(comment_ids)=}')
        for child in node.children:
            print_tree(child, embeddings, depth + 1)


__name__ == '__main__' and main()
