class C:
	x = 1
	class D:
		x = 10
		y = x + 10
print C.D.x
print C.D.y
print C.x
