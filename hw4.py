from nltk import word_tokenize as toknz
from copy import deepcopy

all_vars = 0

class Variable(str):
	def __repr__(self):
		return self

class Expr(tuple):
	def __repr__(self):
		string = "("
		for item in self:
			string += str(item) + " "
		return string[:-1] + ")"

def fresh_variable():
	global all_vars 
	all_vars += 1
	return Variable("_" + str(all_vars))

def is_variable_name(s):
	#takes in a string, returns true if variable
	#s is a variable if it's a single letter followed optionally by numbers
	for i in range(len(s)):
		if i is 0:
			try: 
				int(s[i])
				return False
			except:
				continue
		else:
			try: 
				int(s[i])
				return True
			except:
				return False
	return True

def parse_expr(s):
	tokens = toknz(s)
	left_paren = []
	# expr_indices = []
	i = 0

	while i < len(tokens):	
		if tokens[i] is ')':
			j = left_paren.pop()
			# expr_indices.append((j, i))
			tokens[j:i + 1] = [tokens[j + 1:i]]
			left_paren = []
			i = 0
		elif tokens[i] is '(':
			left_paren.append(i)
			i += 1
		else:
			i += 1

	if len(left_paren) > 0:
		raise Exception("Expression is not well-formed (non-matching parenthesis)")
		
	clean_expr(tokens)
	return Expr(tokens[0])


def clean_expr(expr):
	for i in range(len(expr)):
		if type(expr[i]) is not list:
			if is_variable_name(expr[i]):
				expr[i] = Variable(expr[i])
		else:
			clean_expr(expr[i])
			expr[i] = Expr(expr[i])

def is_lambda_expr(e):
	return(e[0] == 'lambda')


def normalize(expr, repl=None):
	expr_list = list(expr)
	if repl is None:
		repl = {}
	if expr in repl:
		return repl[expr]
	if type(expr) is not Expr:
		return expr
	if not is_lambda_expr(expr):
		for i in range(len(expr_list)):
			expr_list[i] = normalize(expr_list[i], repl)
		return Expr(expr_list)

	#else, we have a lambda expression
	if type(expr_list[1]) is not Expr:
		expr_list[1] = Expr((list(expr_list[1],)))

	params = list(expr_list[1])
	old = {}

	for i in range(len(params)):
		param = params[i]
		if param in repl:
			old[param] = repl[param]

		repl[param] = fresh_variable()
		params[i] = repl[param]

	expr_list[1] = Expr(params)
	expr_list[2] = normalize(expr_list[2], repl)

	for param in params:
		if param in old:
			repl[param] = old[param]

	return Expr(expr_list)


def simplify(e):
	return simplify1(normalize(e), {})

def simplify1(expr, env):
	expr_list = list(expr)
	if expr in env:
		return env[expr]
	if type(expr) is not Expr:
		return expr
	if is_lambda_expr(expr):
		#simplify the body
		#(lambda params body) is the form
		expr_list[2] = simplify1(expr_list[2], env) 
		return Expr(expr_list) 

	for i in range(len(expr_list)):
		expr_list[i] = simplify1(expr_list[i], env)
		expr = Expr(expr_list)

	if is_lambda_expr(expr[0]):
		return beta_reduce(expr, env)
	else:
		return expr

def beta_reduce(expr, env):
	lambda_expr = expr[0]
	params = lambda_expr[1]
	i = 0
	for param in params:
		arg = expr[1 + i]
		env[param] = arg
		i += 1
	result = simplify1(lambda_expr[len(lambda_expr) - 1], env)
	for i in range(len(params)):
		param = params[i]
		del env[param]
	return result


# if __name__ == "__main__":

# 	y = Variable('x')
# 	print(y)

# 	v = fresh_variable()
# 	print(v)
# 	w = fresh_variable()
# 	print(w)

# 	e = Expr(['lambda', Variable('x'), Expr(['chases', 'Fido', Variable('x')])])
# 	print(e)
# 	print(isinstance(e, Expr), e[0])
# 	print(isinstance(e[2], Expr), e[2][1])

# 	print("---testing is_variable_name()---")

# 	print(is_variable_name('x')) #true
# 	print(is_variable_name('X')) #true
# 	print(is_variable_name('x12')) #true
# 	print(is_variable_name('2d')) #false
# 	print(is_variable_name('cat')) #false

# 	print("---testing parse_expr---")

# 	a = parse_expr('(lambda x (chases Fido x))')
# 	print(a)
# 	print(a[0], a[1], type(a[0]), type(a[1]))
# 	b = parse_expr('(and (dog x (with y)) (friendly x))')
# 	print(b)

# 	print(is_lambda_expr(parse_expr('(lambda (x y) (foo y x))')))
# 	print(is_lambda_expr(parse_expr('((lambda x x) foo)')))
# 	e = parse_expr('((lambda x ((lambda x (bar x)) x)) x)')
# 	print(e)

# 	print("---testing normalize---")
# 	print(normalize(e))
# 	f = parse_expr('((lambda y (lambda x y)) x)')
# 	print(normalize(f))

# 	print(simplify(e))

# 	E = parse_expr
# 	w = E('(all x (if (dog x) (barks x)))')
# 	print(w[1], type(w[1]), w[2][1][0])

# 	h = E('((lambda x ((lambda x (foo x)) x)) x)')
# 	print(h)
# 	print(normalize(h))
# 	print(simplify(h))

# 	print("--------------------------")

# 	g = E('''((lambda (x y) (foo (bar y) x)) (mother jack) (father jill))''')
# 	print(g)
# 	print(simplify(g))

# 	j = E('((lambda (x f) (f x)) fido (lambda x x))')
# 	print(j)
# 	print(simplify(j))

# 	k = simplify(E('((lambda x x) fido)'))
# 	print(k)

# 	l = simplify(E('((lambda f (f fido)) (lambda x (dog x)))'))
# 	print(l)

# 	m = simplify(E('''(((lambda f (lambda x (f x x))) (lambda (x y) (likes y x))) fido)'''))
# 	print(m)