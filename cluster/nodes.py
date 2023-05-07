"""
Data model for nodes in the cluster hierarchy.
"""

from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Optional, Iterable


@dataclass
class TreeNode(ABC):
    node_id: int
    parent: Optional['TreeNode'] = field(default=None)

    @abstractmethod
    def get_comment_ids(self) -> list[int]:
        pass

    @abstractmethod
    def iter_nodes(self) -> Iterable['TreeNode']:
        pass


@dataclass
class LeafNode(TreeNode):
    comment_ids: tuple[int, ...] = field(default=())

    def get_comment_ids(self) -> list[int]:
        return list(self.comment_ids)

    def iter_nodes(self) -> Iterable[TreeNode]:
        yield self


@dataclass
class BranchNode(TreeNode):
    children: tuple[TreeNode, ...] = field(default=())

    def get_comment_ids(self) -> list[int]:
        return [ix for c in self.children for ix in c.get_comment_ids()]

    def iter_nodes(self) -> Iterable[TreeNode]:
        yield self
        for c in self.children:
            yield from c.iter_nodes()
