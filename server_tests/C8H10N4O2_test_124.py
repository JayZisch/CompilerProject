x = 1
a = 5
b = 6
class C:
	y = 3
	print y
	print a
	class D:
		z = 4
		print z
		print b
		print x
		x = 2
		print x
print C.D.x
print x
