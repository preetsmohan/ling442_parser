from hw1 import Tree, Index # we redefine Lexicon, Rule, and Grammar
from hw2 import Node, cross_product

from copy import deepcopy

class Lexicon:
	def __init__(self, lexfile):
		self.word_index = Index()
		self.part_index = Index()
		f = open(lexfile, 'r')
		for line in f:
			split = line.split()
			key = split[0]
			for i in range(1, len(split)):
				self.word_index.add(key, parse_category(split[i]))
				self.part_index.add(parse_category(split[i]), key)
		f.close()

	def parts(self, word):
		return self.word_index[word]

	def words(self, part):
		return self.part_index[part]

class Rule:
	def __init__(self, lhs, rhs, bindings):
		self.bindings = bindings
		self.lhs = lhs
		self.rhs = rhs
	def __repr__(self):
		string = str(self.lhs) + ' ->'
		for part in self.rhs:
			string += ' ' + str(part)
		return string

class Category(tuple):
	def __repr__(self):
		string= ""
		for item in range(len(self)):
			if type(self[item]) is int:
				string += '$'
			string += str(self[item]) + "."
		string = string[:-1]
		return string

class Grammar:
	def __init__(self, gramfile):
		lexfile = gramfile + ".lex"
		gramfile += ".g"
		self.lexicon = Lexicon(lexfile)
		self.expansion_index = Index()
		self.continuation_index = Index()
		f = open(gramfile, 'r')
		lines = (line.rstrip() for line in f)
		lines = (line for line in lines if line)
		self.start = None
		for line in lines:
			if line[0] is not '#':
				split = line.split()
				split.remove('->')
				lhs = split[0]
				if self.start is None:
					self.start = lhs
				rhs_first = split[1]
				rhs = split[1:]
				begin_rhs = rhs[0].split('.')[0]
				bindings = ['*', '*']
				t = {}
				lhs = parse_category(lhs, t)
				for i in range(len(rhs)):
					rhs[i] = parse_category(rhs[i], t)
				# print("RULE IS", Rule(lhs, rhs, bindings))
				self.expansion_index.add(lhs, Rule(lhs, rhs, bindings))
				self.continuation_index.add(rhs_first, Rule(lhs, rhs, bindings))
		f.close()

	def expansions(self, lhs):
		return self.expansion_index[lhs]

	def continuations(self, rhs_first):
		returns = []
		r = []

		for k, v in self.continuation_index.table.items():
			split = k.split('.')
			if split[0] == rhs_first:
				r.append(v)

		for item in r:
			for i in item:
				returns.append(i)
		return returns

	def isterm(self, term):
		if len(self.expansions(term)) > 0:
			return False
		return True

class Edge:
	def __init__(self, rule, expansion, bindings):
		self.rule = rule
		self.expansion = expansion
		self.leftovers = [x for x in self.rule.rhs[len(self.expansion):]]
		self.bindings = bindings
	def __repr__(self):
		expansions = ' '.join(str(x) for x in self.expansion)
		leftovers = ' '.join(str(x) for x in self.leftovers)
		return '(' + str(self.rule.lhs) + " -> " + expansions + " * " + leftovers + ')'
	def __add__(self, next):
		exp = deepcopy(self.expansion)
		exp.append(next)
		return Edge(deepcopy(self.rule), exp, self.bindings)
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
			# print("CHART IS", self.chart)
			# print("EDGES ARE", self.edges.table)
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
		node = Node(str(cat), nodes, i, j)
		key = (str(cat), i, j)
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
			self.edges.add((edge.end(), afterdot[0]), edge)
		else:
			self.complete(edge)

	def start(self, node):
		continuations = self.gram.continuations(node.cat.split('.')[0])
		for rule in continuations:
			bindings_size = 0
			for item in rule.rhs[0]:
				if type(item) is int:
					if item > bindings_size:
						bindings_size = item

			bindings = ['*'] * (bindings_size + 1)

			unification = unify(rule.rhs[0], parse_category(node.cat), bindings)
			if unification is not None:
				edge = Edge(rule, [node], unification)
				self.add_edge(edge)

	def complete(self, edge):
		self.add_node(subst(edge.bindings, edge.rule.lhs), edge.expansion, edge.start(), edge.end())

	def combine(self, node):
		k = node.i
		predecessors = self.edges[(k, node.cat.split('.')[0])]
		# if len(predecessors) is 0:
		#  	print(self.edges.table)
		for p in predecessors:
			edge = p + node
			bindings_size = 0
			for item in p.afterdot():
				if type(item) is int:
					if item > bindings_size:
						bindings_size = item

			bindings = ['*'] * (bindings_size + 1)
			unification = unify(p.afterdot(), parse_category(node.cat), bindings)
			edge.bindings = unification
			if unification is not None:
				self.add_edge(edge)

def parse_category(v, t=None):
	#if t (the symbol table) is not set, variables are not allowed
	if type(v) is str:
		v = v.split(".")
	cat_list = [x for x in v if x != '.']
	for i in range(len(cat_list) - cat_list.count('$')):
		if '$' in cat_list[i]:
			assert(t != None), "Variables not allowed"
			cat_list[i] = cat_list[i][1:]
			var = cat_list[i]
			if var not in t:
				t[var] = len(t)
			cat_list[i] = t[var]
	return Category(cat_list)

def meet(u, v):
	#combines two values
	if u == v:
		return u
	if v == '*':
		return u
	if u == '*':
		return v
	return None

def unify(x, y, b):
	#takes two categories, returns updated bindings
	b = deepcopy(b)
	if x[0] != y[0]:
		return None
	for i in range(1, len(x)):
		u = x[i]
		v = y[i]
		if type(v) is int:
			#fail if v is a variable
			return None
		if type(u) is int:
			#u is the variable
			value = meet(b[u], v)
			if value is None:
				return None
			b[u] = value


	return b

def subst(b, x):
	replaced_cat = []
	for i in x:
		if type(i) is int:
			replaced_cat.append(b[i])
		else:
			replaced_cat.append(i)
	return parse_category(replaced_cat)


# if __name__ == "__main__":
# 	x = Category(['V', 0, 'i', '0'])
# 	print(x)
# 	t = {}
# 	c = parse_category('A.x.$x', t)
# 	print(c)
# 	d = parse_category('B.$y.$x', t)
# 	print(d)

# 	print(meet('a', 'a'))
# 	print(meet('a', 'b'))
# 	print(meet('a', '*'))
# 	print(meet('*', 'a'))

# 	t = {'x': 0, 'y': 1}
# 	b = ['*','*']
# 	b2 = unify(parse_category('A.$y.b', t), parse_category('A.c.b', t), b)
# 	print(b2)
# 	b3 = unify(parse_category('B.$y', t), parse_category('B.b', t), b2)
# 	print(b3)
# 	replaced = subst(b2, parse_category('X.$y.b.$x', t))
# 	print(replaced)

# 	lex = Lexicon('fg0.lex')
# 	print(lex.parts('barked'))

# 	t = {}
# 	np = parse_category('NP.$n', t)
# 	det = parse_category('Det.$n', t)
# 	n = parse_category('N.$n', t)
# 	r = Rule(np, [det,n], ['*'])
# 	print(r)
# 	g = Grammar('fg0')
# 	print(g.continuations('Det'))

# 	print("--------TESTING PARSER--------")
# 	p = Parser(g)
# 	trees = p('the dog barks'.split(), tracing=True)
# 	print(trees[0])

# 	print("--------TESTING PARSER WITH LARGE SET--------")
# 	gr = Grammar('fg1')
# 	pr = Parser(gr)

# 	f = open('fg1.sents', 'r')

# 	for line in f:
# 	 	print("Sentence:", line)
# 	 	trees = pr(line.split(), tracing=False)
# 	 	if trees is not None:
# 	 		for tree in trees:
# 	 			print(tree)
# 	 	else:
# 	 		print("ERROR: ", line)

# 	f.close()



