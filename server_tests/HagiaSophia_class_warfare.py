class C():
	def __init__(self, x):
		self.x = x
	def getX(self, otherObj):
		self.x = self.x + -1
		print self.x
		return otherObj.getX(self) if self.x != 0 else self.x

y = 20
z = 10
c1 = C(y)
c2 = C(z)
c1.getX(c2)
