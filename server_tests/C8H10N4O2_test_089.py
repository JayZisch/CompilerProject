def g(x):
	return x+1

def f(x):
	return 1 if x==1 else g(x)

print f(2)
