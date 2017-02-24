import sys
import re
import random
from nltk import word_tokenize as toknz

class Tree:
	def __init__(self, cat, children=None, word=None):
		self.cat = cat
		self.children = children
		self.word = word

	def __str__(self): 
		#pretty-print the tree
		wlist = []
		pprint = ""
		str_helper(self, wlist, 0)
		return "".join(wlist)

def str_helper(tree, wlist, level):
	#print("TREE", tree)
	for i in range (0, level):
		wlist.append("  ")
	if isleaf(tree):
		wlist.extend(("(", tree.cat, " ", tree.word, ")", "\n"))
	elif tree is not None:
		#print("tree")
		wlist.extend(("(", tree.cat, "\n"))
		for child in tree.children:
			str_helper(child, wlist, level + 1)	
		wlist.pop()
		wlist.extend((")", '\n'))


def isleaf(tree):
	if type(tree) is not Tree:
		return False
	if tree.children is not None:
		return False
	if tree.word is None:
		return False
	if tree.children is []:
		return False
	return True

def isinterior(tree):
	return not isleaf(tree)

def parse_tree(sentence):
	tokens = toknz(sentence)
	j = 0
	children = []
	subchildren = []
	parent = Tree(tokens[1], children)

	while j < len(tokens) - 1: 
		if tokens[j] == '(':
			if tokens[j + 2] != '(':
				(t, j) = parse_subtree(tokens, j)
				subchildren.append(Tree(t[0], word=t[1]))
				print (t, j)
			else:
				j += 2

		elif tokens[j] == ')':
			tree = Tree(tokens[j - len(subchildren)*4 - 1], subchildren)
			children.append(tree)
			subchildren = []
			j += 1

	#take care of the last children found
	for child in subchildren:
		children.append(child)
		
	parent.children = children
	return parent
	
def parse_subtree(toks, i):
	return ((toks[i+1], toks[i+2]), i + 4)
	
def terminal_helper(tree, wordlist):
	if isleaf(tree):
		wordlist.append(tree.word)
	else:
		for child in tree.children:
			terminal_helper(child, wordlist) 

def terminal_string(tree):
	wordlist = []
	terminal_helper(tree, wordlist)
	sys.stdout.write(" ".join(wordlist))
	print('.')

class Index:
	def __init__(self):
		self.table = dict()
	def __getitem__(self, key):
		if key in self.table:
			return self.table[key]
		else:
			return []
	def add(self, key, value):
		if key in self.table:
			self.table[key].append(value)
		else:
			self.table[key] = [value]


class Lexicon:
	def __init__(self, lexfile):
		self.word_index = Index()
		self.part_index = Index()
		f = open(lexfile, 'r')
		for line in f:
			split = line.split()
			key = split[0]
			for i in range(1, len(split)):
				self.word_index.add(key, split[i])
				self.part_index.add(split[i], key)

	def parts(self, word):
		return self.word_index[word]

	def words(self, part):
		return self.part_index[part]

class Rule:
	def __init__(self, lhs, rhs):
		self.lhs = lhs
		self.rhs = rhs
	def __repr__(self):
		string = self.lhs + " ->"
		for part in self.rhs:
			string += " " + part
		return string

class Grammar:
	def __init__(self, gramfile):
		lexfile = gramfile + ".lex"
		gramfile += ".g"
		self.lexicon = Lexicon(lexfile)
		self.expansion_index = Index()
		self.continuation_index = Index()
		f = open(gramfile, 'r')
		self.start = None
		for line in f:
			split = line.split()
			split.remove('->')
			lhs = split[0]
			if self.start is None:
				self.start = lhs
			rhs_first = split[1]
			rhs = split[1:]

			self.expansion_index.add(lhs, Rule(lhs, rhs))
			self.continuation_index.add(rhs_first, Rule(lhs, rhs))

	def expansions(self, lhs):
		return self.expansion_index[lhs]

	def continuations(self, rhs_first):
		return self.continuation_index[rhs_first]

	def isterm(self, term):
		if len(self.expansions(term)) > 0:
			return False
		return True

	def generate_from(self, categ, trees):
		if self.isterm(categ):
			possible_words = self.lexicon.words(categ)
			chosen_word = random.choice(list(possible_words))
			return Tree(categ, word=chosen_word)
		else:
			possible_expansions = self.expansions(categ)
			chosen_expansion = random.choice(list(possible_expansions))
			children = []
			parent = Tree(chosen_expansion.lhs, children)
			for cat in chosen_expansion.rhs:
				sub_tree = self.generate_from(cat, trees)
				parent.children.append(sub_tree)
			return parent

	def generate(self):
		rule = random.choice(list(self.expansion_index.table))
		possible_expansions = self.expansions(rule)
		chosen_expansion = random.choice(list(possible_expansions))
		children = []
		parent = Tree(chosen_expansion.lhs, children)
		trees = []
		for cat in chosen_expansion.rhs:
			sub_parent = self.generate_from(cat, trees)
			parent.children.append(sub_parent)
			trees = []

		return parent

if __name__ == "__main__":

	sys.setrecursionlimit(2500)
	print(sys.getrecursionlimit())
	#tree testing
	d = Tree('Det', word='the')
	n = Tree('N', word='dog')
	np = Tree('NP', [d, n])
	v = Tree('V', word='barks')
	s = Tree('S', [np, v])

	terminal_string(s)
	pprint = []
	print(pprint)
	print(s)

	sent = '(S (NP (Det the) (N dog)) (V barks))'
	#sent = "(NP (Det the) (N dog))"
	tree = parse_tree(sent)

	print(tree)

	#index testing
	index = Index()
	print(index['hi'])
	index.add('hi', 16)
	print(index['hi'])
	index.add('hi', 42)
	print(index['hi'])

	#lexicon testing
	lex = Lexicon('g0.lex')
	print(lex.parts('book'))
	print(lex.words('N'))

	#rule testing
	r = Rule('S', ['NP', 'VP'])
	print(r.rhs)
	print(r.lhs)

	#grammar testing
	g = Grammar('g0')
	print(g.expansions('VP'))
	print(g.continuations('NP'))
	print(g.isterm('NP'))
	print(g.isterm('X'))
	print(g.lexicon.words('N'))
	generated = g.generate()
	print(generated)
	terminal_string(generated)



