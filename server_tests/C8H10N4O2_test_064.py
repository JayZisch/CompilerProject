x = [1,2,[input(),4]]
print x
y = { 5:x, 6:{ 7:[input(),9], 10:{ 11:12, input():[14,15,[16,17]] } }, 18:19 }
print x[0]
print x[2][0]
print y[5][0]
print y[5][2][0]
print y[6][7][0]
print y[6][10][11]
print y[6][10][13][0]
print y[6][10][13][2][0]
print y[18]
z = { 20:x, 21:y }
print z[20][0]
print z[20][2][0]
print z[21][5][0]
print z[21][5][2][0]
print z[21][6][7][0]
print z[21][6][10][11]
print z[21][6][10][13][0]
print z[21][6][10][13][2][0]
print z[21][18]
