x = 1
class C:
	class D:
		print x
		x = 2
		print x
print C.D.x
print x
