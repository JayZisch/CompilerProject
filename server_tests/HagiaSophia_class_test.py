class C():
	def __init__(self):
		print 7
	def f(self):
		print 11

def testFun(x, y):
	return x + y

c = C()
c.f()
unbndMth = C.f
unbndMth(c)
print testFun(12,24)
