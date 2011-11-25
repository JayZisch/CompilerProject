class C:
	x = 1
	y = x
	x = 2
	print y
print C.y
C.x = 10
print C.y
