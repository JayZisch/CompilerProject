class C():
	0
class D():
	x = 4
class E(C, D):
	def __init__(self, x, y):
		self.x = x
		self.y = y
	def add(self):
		return self.x + self.y

E.m = 3+3+3
print E.m
C.m = 4+4+4
print C.m
e = E(10, 0)
while(e.x != 0):
	print e.add()
	e.x = e.x + -1
