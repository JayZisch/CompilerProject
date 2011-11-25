d1 = {input(): input(), True: input()}
d2 = {0: 10, 1: 11}

(d1 if input() else d2)[input()] = input()

print d1[True]
print d1[6]
print d2[0]
