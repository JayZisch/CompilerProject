import compiler
import compile

def test(filename):
	x={}
	ast = compiler.parseFile("server_tests/%s"%filename)
	#print 'ast tree:'
	#print ast
	#print '\n'
	print '\nCode:'
	fil = open("server_tests/%s"%filename)
	for line in fil:
		print line	
	fil.close()
	uni = ast.declass(compile.tempVars())
	print 'new uni tree:'
	print uni
	

files = ['add_0.py','add_0.py','add_1.py','add_2.py','add_3.py','and0.py','assign0.py','assign_lhs_stack.py','assign_lhs_stack2.py','bool0.py','bool1.py','class0.py','class1.py','class2.py','class3.py','class4.py','class5.py','class6.py','class7.py','class8.py','class9.py','cmp0.py','der.py','dict0.py','dict1.py','discard.py','discard2.py','eq0.py','eq1.py','fun0.py','fun1.py','fun2.py','fun3.py','fun4.py','ifexp0.py','ifexp1.py','ifexp2.py','ifexp3.py','ifexp4.py','ifexp5.py','ifexp6.py','ifexp7.py','ifstmt0.py','ifstmt1.py','input0.py','input_0.py','input_1.py','input_2.py','is0.py','lambda0.py','list0.py','list1.py','list2.py','list3.py','list4.py','list5.py','list6.py','list7.py','map.py','maplist.py','method0.py','method1.py','move_0.py','move_id.py','mult.py','neg_0.py','neg_add_0.py','neq0.py','not0.py','not1.py','notes0.py','obj0.py','obj1.py','obj2.py','obj3.py','or0.py','or1.py','print0.py','reg_alloc_0.py','spill.py','sum.py','sumlist.py','t5.py','test0.py','test0b.py','test1.py','test2.py','test3.py','usub_0.py','usub_1.py','var_0.py','var_1.py','while0.py','while1.py','while2.py']


def main():
	d = 1
	for i in files:
		if i[-2:]=='py':
			print 'testing %s %d'%(i,d)
			test(i)
			print 'done',''
			d = d + 1
