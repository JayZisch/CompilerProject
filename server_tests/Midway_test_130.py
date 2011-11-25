class A:
	x = 1
	y = 2
class B:
	x = 10
	y = 20
	z = 30
class C(A,B):
	x = 100
print A.x
print A.y
print B.y
print B.z
print C.x
print C.y
print C.z

class Z(C):
	0
print Z.x
print Z.y
print Z.z
