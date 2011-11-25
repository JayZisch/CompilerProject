x = [1,[1,2],{2:4}]
y = x[2]
print x
print y
print x is y
print x[2] is y
c = {9:12} if input() else x
print x is c
