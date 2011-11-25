y = 10

class C:
	j = y
	y = 9
	print j
	print y
	class G:
		h = 6

o = C()
o.j = 2
print o.j

print o.G.h
