x=1
y=x
def f():
	def g():
		return lambda y:x+y+z
z=1
print f()()
