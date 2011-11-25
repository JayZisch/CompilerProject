class C:
	x = 1
	y = 2
	z = x + y
	class D:
		x = 10
		y = 20
		z = x + y
		print x
		print y
		print z
	print x
	print y
	print z
print C.D.x
print C.D.y
print C.D.z
print C.x
print C.y
print C.z
