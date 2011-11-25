class B():
	x = 7
	y = 4
class C(B):
	print B.x
	class D():
		def __init__(self):
			self.y = 19
		def f(self):
			return self.y
c = C()
d = c.D()
print d.f()
