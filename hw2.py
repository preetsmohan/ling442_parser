from hw1 import *
from itertools import product
from copy import deepcopy

def cross_product(child_trees):
	#this is kind of hacky
	if len(child_trees) == 2:
		return list(product(child_trees[0], child_trees[1]))
	else:
		childlist = []
		for child in child_trees:
			childlist.extend(child)
		return [childlist]

def tree_expansions(node_expansion):
	choices = [n.trees() for n in node_expansion]
	return cross_product(choices)

class Node: 
	def __init__(self, cat, exp, i, j):
		self.cat = cat
		self.expansions = [exp]
		self.i = i
		self.j = j 
	def __repr__(self):
		return '[' + str(self.i) + " " + self.cat + " " + str(self.j) + ']' 
	def add(self, exp):
		self.expansions.append(exp)

	def trees(self):
		out = []
		for e in self.expansions:
			if isinstance(e, str):
				out.append(Tree(self.cat, word=e))
			elif len(e) == 0:
				out.append(Tree(self.cat))
			else:
				for childlist in tree_expansions(e):
					tree = Tree(self.cat, childlist)
					out.append(tree)
		return out

class Edge:
	def __init__(self, rule, expansion):
		self.rule = rule
		self.expansion = expansion
		self.leftovers = [x for x in self.rule.rhs[len(self.expansion):]]
	def __repr__(self):
		expansions = ' '.join(str(x) for x in self.expansion)
		leftovers = ' '.join(str(x) for x in self.leftovers)
		return '(' + self.rule.lhs + " -> " + expansions + " * " + leftovers + ')'
	def __add__(self, next):
		exp = deepcopy(self.expansion)
		exp.append(next)
		return Edge(deepcopy(self.rule), exp)
	def cat(self):
		return self.rule.lhs
	def start(self):
		return self.expansion[0].i
	def end(self):
		return self.expansion[len(self.expansion) - 1].j
	def afterdot(self):
		if len(self.leftovers) == 0:
			return None
		else:
			return self.leftovers[0]

class Parser: 
	def __init__(self, grammar):
		self.chart = None
		self.edges = None
		self.words = None
		self.gram = grammar

	def __call__(self, words, tracing=False):
		self.chart = dict()
		self.edges = Index()
		self.words = words
		self.tracing = tracing

		for i in range(0, len(words)):
			self.shift(i)

		start = self.gram.start
		key = (start, 0, len(words))
		if key not in self.chart:
			return None
		result = self.chart[key]

		return self.unravel(result)

	def unravel(self, result):
		#result is a Node object
		trees = result.trees()
		return trees

	def shift(self, i):
		j = i + 1
		cats = self.gram.lexicon.parts(self.words[i])
		for cat in cats:
			self.add_node(cat, self.words[i], i, j)
			
	def add_node(self, cat, nodes, i, j):
		node = Node(cat, nodes, i, j)
		key = (cat, i, j)
		if key not in self.chart:
			if self.tracing:
				if isinstance(nodes, str):
					print("Add Node", node, nodes)	
				else:
					print("Add Node", node, [node for node in nodes])
			self.chart[key] = node
			self.start(node)
			self.combine(node)
		else:
			self.chart[key].add(nodes)
			if self.tracing:
				print("Add Expansion", self.chart[key])


	def add_edge(self, edge):
		afterdot = edge.afterdot()
		if self.tracing:
			print("Add Edge", edge)
		if afterdot is not None:
			self.edges.add((edge.end(), afterdot), edge)
		else:
			self.complete(edge)

	def start(self, node):
		continuations = self.gram.continuations(node.cat)
		for rule in continuations:
			edge = Edge(rule, [node])
			self.add_edge(edge)

	def complete(self, edge):
		self.add_node(edge.rule.lhs, edge.expansion, edge.start(), edge.end())

	def combine(self, node):
		k = node.i
		predecessors = self.edges[(k, node.cat)]
		for p in predecessors:
			edge = p + node
			self.add_edge(edge)		


# if __name__ == "__main__":

	# #test Nodes
	# d = Node('Det', 'the', 0, 1)
	# n = Node('N', 'dog', 1, 2)
	# np = Node('NP', [d, n], 0, 2)
	# print(np)
	# print(np.cat)
	# print(np.i, np.j)
	# print(d.expansions)
	# print(np.expansions)

	# #test Edges
	# r = Rule('NP', ['Det', 'N'])
	# print(r)
	# e = Edge(r, [d])
	# print(e)
	# print(e.rule)
	# print(e.expansion)

	# g = Grammar('g0')
	# p = Parser(g)
	# trees = p('I book a flight in May'.split())
	# for tree in trees:
	# 	print(tree)

	# f = open('g1.sents', 'r')

	# gr = Grammar('g1')
	# pr = Parser(gr)
	# for line in f:
	# 	print(line)
	# 	trees = pr(line.split(), tracing=False)
	# 	if trees is not None:
	# 		for tree in trees:
	# 			print(tree)
	# 	else:
	# 		print("ERROR")
