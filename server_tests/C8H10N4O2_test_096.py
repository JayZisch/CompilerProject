def f():
	def g(z):
		w = 1
		return z + w
	y = g
	x = lambda: 2
	return lambda: y(3) + x()
print f()()
