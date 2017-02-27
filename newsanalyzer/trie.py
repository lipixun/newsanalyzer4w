# encoding=utf8

""" A trie-tree python implementation
    Author: lipixun
    Created Time : 日  2/12 17:33:59 2017

    File Name: trie.py
    Description:

        For easy installation, I wrote a pure python version of trie-tree. This may cause a serious issue of performance but
        installing c version of trie-tree requires too many dependencies (python-dev, gcc, g++ ...).

"""

class TrieTreeNode(object):
    """The trie tree node
    """
    def __init__(self, term, parent, nodes = None, attrs = None):
        """Create a new TrieTreeNode
        """
        self.term = term
        self.parent = parent
        self.nodes = nodes or {}
        self.attrs = attrs or {}
        self.isLeaf = False

    def add(self, terms, **attrs):
        """Add
        """
        if not terms:
            # The leaf node
            self.isLeaf = True
            # Add attributes to current node
            for key, value in attrs.iteritems():
                self.addAttr(key, value)
        else:
            term = terms[0]
            terms = terms[1: ]
            node = self.nodes.get(term)
            if not node:
                node = TrieTreeNode(term, self)
                self.nodes[term] = node
            # Continue add
            node.add(terms, **attrs)

    def addAttr(self, key, value):
        """Add key value
        """
        if key in self.attrs:
            raise ValueError("Conflicted key found: %s", key)
        self.attrs[key] = value

    def longestPrefix(self, terms, startIndex):
        """Search for longest prefix
        Returns:
            TrieTreeNode: The matched node
        """
        if startIndex >= len(terms):
            if self.isLeaf:
                return self
            return
        # Get child node
        term = terms[startIndex]
        if not term in self.nodes:
            return
        # Found the child node
        node = self.nodes[term]
        # Check if could continuously match
        nextNode = node.longestPrefix(terms, startIndex + 1)
        if nextNode:
            return nextNode
        elif node.isLeaf:
            return node

    def getPath(self):
        """Get the term path
        Returns:
            [ str ]: The terms
        """
        node = self
        terms = []
        while node:
            if node.term:
                terms.append(node.term)
            node = node.parent
        return reversed(terms)

class TrieTree(TrieTreeNode):
    """Tree tree
    """
    def __init__(self):
        """Create a new TrieTree
        """
        super(TrieTree, self).__init__(None, None)

    def search(self, terms):
        """Search in the terms (sequence)
        Yield:
            (Node, startIndex)
        """
        for i in xrange(0, len(terms)):
            node = self.longestPrefix(terms, i)
            if node:
                yield (node, i)

    def split(self, terms):
        """Split the terms
        Yield:
            (words, attrs)
        """
        index = 0
        while index < len(terms):
            node = self.longestPrefix(terms, index)
            if node:
                terms = node.getPath()
                yield (terms, node.attrs)
                index += len(terms)
            else:
                yield ((terms[index], ), None)
                index += 1
