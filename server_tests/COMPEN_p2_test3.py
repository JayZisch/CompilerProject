def g():
	def h(i):
		return i+9
	return  h


def h(i):
   	return i+-9


print g()(7) == h(7)

