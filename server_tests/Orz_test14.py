#max = 536870911
#min = -max + -1

#print max
#print min

list = [1, 2, 3, [4, 5]]
list2 = [1, 2, 3]
list[2] = list
print [list if input() else list2]

list1 = [1, 2, 3]
list2 = [7, 8, 9]
list3 = list1 + [5] + list2
list3[3] = list3
print list3[3][3][3][3][3][0]
