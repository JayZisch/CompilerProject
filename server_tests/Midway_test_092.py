x=1
y=2
z=3
def f(z):
	def g():
		def h():
			return z + 3
		return y + 2
	return x + 1
	
print f(1)
