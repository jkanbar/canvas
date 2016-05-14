from __future__ import division
import numpy as np
from skbio.stats.composition import clr_inv
from collections import OrderedDict


def _balance_basis(tree_node):
    """ Helper method for calculating phylogenetic basis
    """

    n_tips = sum([n.is_tip() for n in tree_node.traverse()])
    counts = _count_matrix(tree_node)
    counts = OrderedDict([(x, counts[x])
                          for x in counts.keys() if not x.is_tip()])
    nds = counts.keys()
    r = np.array([counts[n]['r'] for n in nds])
    s = np.array([counts[n]['l'] for n in nds])
    k = np.array([counts[n]['k'] for n in nds])
    t = np.array([counts[n]['t'] for n in nds])

    a = np.sqrt(s / (r*(r+s)))
    b = -1*np.sqrt(r / (s*(r+s)))

    basis = np.zeros((n_tips-1, n_tips))
    for i in range(len(nds)):
        basis[i, :] = np.array([0]*k[i] + [a[i]]*r[i] + [b[i]]*s[i] + [0]*t[i])
    return basis, nds


def phylogenetic_basis(tree_node):
    """
    Determines the basis based on phylogenetic tree

    Parameters
    ----------
    treenode : skbio.TreeNode
        Phylogenetic tree.  Must be a strictly bifurcating tree
    Returns
    -------
    basis : np.array
        Returns a set of orthonormal bases in the Aitchison simplex
        corresponding to the phylogenetic tree. The order of the
        basis is index by the level order of the internal nodes.
    nodes : list, skbio.TreeNode
        List of tree nodes indicating the ordering in the basis.

    Raises
    ------
    ValueError
        The tree doesn't contain two branches

    Examples
    --------
    >>> from canvas.phylogeny import phylogenetic_basis
    >>> from skbio import TreeNode
    >>> tree = u"((b,c)a, d)root;"
    >>> t = TreeNode.read([tree])
    >>> phylogenetic_basis(t)
    array([[ 0.62985567,  0.18507216,  0.18507216],
           [ 0.28399541,  0.57597535,  0.14002925]])

    Notes
    -----
    The tree must be strictly bifurcating, meaning that
    every internal node has exactly 2 children.
    """
    basis, nodes = _balance_basis(tree_node)
    basis = clr_inv(basis)
    return basis, nodes


def _count_matrix(treenode):
    nodes = list(treenode.levelorder(include_self=True))
    # fill in the dictionary
    counts = OrderedDict()
    columns = ['k', 'r', 'l', 't', 'tips']
    for n in nodes:
        if n not in counts:
            counts[n] = {}
        for c in columns:
            counts[n][c] = 0

    # fill in r and l
    for n in nodes[::-1]:
        if n.is_tip():
            counts[n]['tips'] = 1
        elif len(n.children) == 2:
            lchild = n.children[0]
            rchild = n.children[1]
            counts[n]['r'] = counts[rchild]['tips']
            counts[n]['l'] = counts[lchild]['tips']
            counts[n]['tips'] = counts[n]['r'] + counts[n]['l']
        else:
            raise ValueError("Not a strictly bifurcating tree!")

    # fill in k and t
    for n in nodes:
        if n.parent is None:
            counts[n]['k'] = 0
            counts[n]['t'] = 0
            continue
        elif n.is_tip():
            continue
        # left or right child
        # left = 0, right = 1
        child_idx = 'l' if n.parent.children[0] != n else 'r'
        if child_idx == 'l':
            counts[n]['t'] = counts[n.parent]['t'] + counts[n.parent]['l']
            counts[n]['k'] = counts[n.parent]['k']
        else:
            counts[n]['k'] = counts[n.parent]['k'] + counts[n.parent]['r']
            counts[n]['t'] = counts[n.parent]['t']

    return counts
