#!/usr/bin/env python
import sys
import compiler
import traceback

from compiler.ast import *
# type-tag definitions

MASK = 3     # 11 
SHIFT = 2
INT_TAG = 0  # 00
BOOL_TAG = 1 # 01
BIG_TAG = 3  # 11


def tempVars():
    i = 0
    while True:
        yield 'tmp%d'%i
        i += 1

def labels():
    i = 0
    while True:
        yield '.L%d'%i
        i += 1
labelGen = labels()

def counter():
	i = 0
	while True:
		yield '_%d'%i
		i +=1
########################################################################
#                        module functions
########################################################################

def module_flatten(self,tempGen = None):
    if not tempGen:
        tempGen = tempVars()
    nodes, result, variables = self.node.flatten(tempGen)
    variables = list(set(variables)) #remove duplicates
    variables.sort()
    m = Module(self.doc, result)
    m.variables = variables
    return m

def module_code(self):
    code = ''
    if hasattr(self,'funcs'):
        for f in self.funcs:
            code += f.code()+'\n'
    return code + self.node.code()

def module_asm(self):
    func_lines=[]
    for func in self.funcs:
        l,_=func.asm()
        func_lines.append((l,func.variables))
    lines,_ = self.node.asm()
    lines += [('movl', '$0', '%eax')]
    lines = [('.globl main',),('main:',)] + gen_stack_asm(lines,len(self.variables))
    return func_lines + [(lines,self.variables)]

def module_explicate(self,tempGen):
    funcs = []
    variables = []
    for f in self.funcs:
        _,new_f,f_vars =f.explicate(tempGen)
        funcs.append(new_f)
        variables += f_vars
        
    _, result,n_vars = self.node.explicate(tempGen)
    variables += n_vars
    m = Module(self.doc, result)
    m.variables = list(set(self.variables + variables)) #remove duplicates
    m.variables.sort()
    m.funcs = funcs
    return m
    
def module_boundvars(self):
	return self.node.boundvars()
		
def module_uniq(self,global_cnt,var_map):
	for var in self.node.boundvars():
		var_map[var]=var+global_cnt.next()
	return Module(self.doc,self.node.uniq(global_cnt,var_map))
	

def module_closure(self, tempGen):
    funcs, stmt,variables = self.node.closure(tempGen)
    m = Module(self.doc, stmt)
    m.variables = list(set(self.variables + variables))
    m.variables.sort()
    m.funcs = funcs
    return m


##def stmt_heap(self):

def module_heapify(self,tempGen):
    heapvars = self.node.heapvars()
    
    _,stmt,new_vars = self.node.heapify(heapvars,tempGen)
    new_nodes = list(Assign([AssName(var,'OP_ASSIGN')],CallFunc(FuncName('make_list'),[Const(1)]))
        for var in set(self.variables) & set(heapvars))
    stmt.nodes = new_nodes+stmt.nodes
    m = Module(self.doc, stmt)
    m.variables = list(set(self.variables+new_vars))
    m.heapvars = heapvars
    return m

def module_declass(self,tempGen):
	tmp = None
	varmap = {}
	return Module(self.doc,self.node.declass(tempGen,tmp,varmap))

# Initialize functions as class function
Module.uniq = module_uniq
Module.boundvars = module_boundvars
Module.flatten = module_flatten
Module.code = module_code
Module.asm = module_asm
Module.explicate = module_explicate
Module.closure = module_closure
Module.heapify = module_heapify
Module.declass = module_declass

########################################################################
#                           Statement Functions
########################################################################

def stmt_flatten(self,tempGen):
    nodes = []
    variables = []
    for n in self.nodes:
        newNodes,result,newVariables = n.flatten(tempGen)
        nodes += newNodes
        variables += newVariables
    return None, Stmt(nodes), variables

def stmt_code(self):
    return '\n'.join([n.code() for n in self.nodes])

def stmt_asm(self):
    lines = []
    for n in self.nodes:
        l,_ = n.asm()
        lines += l
    return lines,''

def stmt_explicate(self,tempGen):
    nodes,variables = [],[]
    
    for n in self.nodes:
        n_nodes,n_result,n_variables = n.explicate(tempGen)
        nodes += n_nodes + [n_result]
        variables += n_variables
    
    return None,Stmt(nodes),variables

def stmt_boundvars(self):
	ans = set([])
	for n in self.nodes:
		ans |= n.boundvars()
	return ans
	
def stmt_uniq(self,global_cnt,var_map):
	nodes = []
	for n in self.nodes:
		nnodes = n.uniq(global_cnt,var_map)
		nodes += [nnodes]
	return Stmt(nodes)

def stmt_closure(self,tempGen):
    funcs,nodes,variables=[],[],[]
    for n in self.nodes:
        n_funcs,n_nodes,n_vars = n.closure(tempGen)
        funcs += n_funcs
        nodes += n_nodes
        variables += n_vars
    return funcs, Stmt(nodes),variables    

def stmt_heapvars(self):
    return sum([n.heapvars() for n in self.nodes],[])

def stmt_heapify(self,heapvars,tempGen):
    nodes = []
    variables = []
    for n in self.nodes:
        newNodes,result,newVariables = n.heapify(heapvars,tempGen)
        nodes += newNodes+[result]
        variables += newVariables
    return None, Stmt(nodes), variables

def stmt_declass(self,tempGen,tmp,varmap):
	nodes= []
	for n in self.nodes:
		newNodes = n.declass(tempGen,tmp,varmap)
		nodes += newNodes
	return Stmt(nodes)

Stmt.uniq = stmt_uniq
Stmt.boundvars = stmt_boundvars
Stmt.flatten = stmt_flatten
Stmt.code = stmt_code
Stmt.asm = stmt_asm
Stmt.explicate = stmt_explicate
Stmt.closure = stmt_closure
Stmt.heapvars = stmt_heapvars
Stmt.heapify = stmt_heapify
Stmt.declass = stmt_declass

########################################################################
#                              Printnl functions
########################################################################


def printnl_flatten(self,tempGen):
    nodes = []
    results = []
    variables = []
    for node in self.nodes:
        
        newNodes, result, newVariables = node.flatten(tempGen)
        nodes += newNodes
        variables += newVariables
        if result.is_simple:
            results.append(result) #TODO use make_simple
        else:
            var = tempGen.next()
            nodes += [Assign([AssName(var,'OP_ASSIGN')],result)]
            variables += [var]
            results.append(Name(var))
    
    return nodes + [Printnl(results,self.dest)], None, variables

def printnl_code(self):
    return 'print ' + ', '.join([n.code() for n in self.nodes])

def printnl_asm(self): 
    lines = []
    for node in self.nodes:
        l,val = node.asm()
        lines += l
        lines += [('pushl', val),
                  ('call','print_any'),
                  ('addl', '$4', '%esp')]
    return lines, ''

def printnl_explicate(self,tempGen):
    return [],self,[]
    
def printnl_boundvars(self):
	ans = set([])
	if not self.nodes:
		return ans
	else:
		for n in self.nodes:
			ans | n.boundvars()
	return ans

def printnl_uniq(self,global_cnt,var_map):
	nodes = []
	for n in self.nodes:
		nnodes =n.uniq(global_cnt,var_map)
		nodes.append(nnodes)
	return Printnl(nodes,self.dest)

def printnl_hepaify(self,heapvars,tempGen):
    nodes,results,variables = [],[],[]
    
    for n in self.nodes:
        n_nodes,n_result,n_vars = n.heapify(heapvars,tempGen)
        nodes += n_nodes
        results.append(n_result)
        variables += n_vars
    
    return nodes,Printnl(results,self.dest),variables

def printnl_declass(self,tempGen,tmp,varmap):
	nodes = []
	for n in self.nodes:
		nnodes = n.declass(tempGen,tmp,varmap)
		nodes.append(nnodes)
	return [Printnl(nodes,self.dest)]
	
Printnl.uniq = printnl_uniq    
Printnl.boundvars = printnl_boundvars
Printnl.flatten = printnl_flatten
Printnl.code = printnl_code
Printnl.asm = printnl_asm
Printnl.explicate = printnl_explicate
Printnl.heapify = printnl_hepaify
Printnl.declass = printnl_declass

########################################################################
#                           Assign Functions
########################################################################


def assign_flatten(self,tempGen):
    
    nodes, result, variables = self.expr.flatten(tempGen)
    newNodes = []
    
    for n in self.nodes:
        n_nodes,nodeResult,assignVars = n.flatten(tempGen)
        newNodes += [nodeResult]
        nodes += n_nodes
        variables += assignVars
    
    return nodes + [Assign(newNodes,result)], None, variables

def assign_code(self):
    return ', '.join([n.code() for n in self.nodes]) + ' = ' + self.expr.code()

def assign_asm(self):
    lines,val = self.expr.asm()
    lines = [('#%s'%self.code(),)] + lines
    for node in self.nodes:
        l,addr = node.asm()
        lines += l
        lines += [('movl',val, 'eax')]
        lines += [('movl','eax', addr)]
    return lines,''

def assign_explicate(self,tempGen):
    nodes,result,variables = self.expr.explicate(tempGen)
    
    if self.nodes[0].__class__ == Subscript:
        s_nodes, s_result, s_vars = self.nodes[0].explicate(tempGen, result)
        return nodes+s_nodes, s_result, variables+s_vars
    
    return nodes,Assign(self.nodes,result),variables

def assign_boundvars(self):
	lhs = self.nodes[0].boundvars()
	rhs = self.expr.boundvars()
	return lhs

def assign_uniq(self,global_cnt,var_map):
	return Assign([self.nodes[0].uniq(global_cnt,var_map)],self.expr.uniq(global_cnt,var_map))

def assign_closure(self,tempGen):
    result = self.expr.closure(tempGen)
    if len(result) == 4:
        _,nodes,call,variables = result
        nodes += [Assign(self.nodes,call)]
    else:
        nodes = [Assign(self.nodes,result[1][0])]
        variables = []
    return [],nodes,variables

def assign_heapify(self,heapvars,tempGen):
    new_nodes = []
    for n in self.nodes:
        _,node,_ = n.heapify(heapvars,tempGen)
        new_nodes.append(node)
    nodes,expr,variables = self.expr.heapify(heapvars,tempGen)
    
    return nodes,Assign(new_nodes,expr),variables

def assign_declass(self,tempGen,tmp,varmap):
	if(isinstance(self.nodes[0], AssAttr)):
		classname,attribute=self.nodes[0].declass(tempGen,tmp,varmap)
		if( not attribute in varmap ):
			varmap[attribute] = [varmap[classname]]
		else:
			varmap[attribute].append(varmap[classname])
			list(set(varmap[attribute]))
		return CallFunc(FuncName('set_attr'),[classname,attribute,self.expr.declass(tempGen,tmp,varmap)])
	if(tmp!=None):
		if(not self.nodes[0].declass(tempGen,tmp,varmap) in varmap):
			varmap[self.nodes[0].declass(tempGen,tmp,varmap)] = [tmp]
		else:
			varmap[self.nodes[0].declass(tempGen,tmp,varmap)].append(tmp)
			list(set(varmap[self.nodes[0].declass(tempGen,tmp,varmap)]))
		return CallFunc(FuncName('set_attr'),[tmp,self.nodes[0].declass(tempGen,tmp,varmap),self.expr.declass(tempGen,tmp,varmap)])
	else:
		if(not self.nodes[0].name in varmap):
			varmap[self.nodes[0].name] = [None]
		else:
			varmap[self.nodes[0].name].append(None)
			list(set(varmap[self.nodes[0].name]))
		return [Assign(self.nodes[0].declass(tempGen,tmp,varmap),self.expr.declass(tempGen,tmp,varmap))]
		
Assign.uniq = assign_uniq
Assign.boundvars = assign_boundvars
Assign.flatten = assign_flatten
Assign.code = assign_code
Assign.asm = assign_asm
Assign.explicate = assign_explicate
Assign.closure = assign_closure
Assign.heapify = assign_heapify
Assign.declass = assign_declass

def getvalue(node):
	if(isinstance(node,Const)):
		return node.value
	elif(isinstance(node,Name)):
		return node.name
	elif(isinstance(node,unarysub)):
		return node.expr.value
	elif(isinstance(node,Lambda)):
		return 
########################################################################
#                         Assname Functions
########################################################################

def assname_flatten(self,tempGen):
    new_name = 'usr_%s'%self.name #rename usr vars so they dont conflict with our temps
    return [],AssName(new_name,'OP_ASSIGN'),[new_name]

def assname_code(self):
    return self.name

def assname_asm(self):
    return [],self.name

def assname_explicate(self,tempGen):
    raise Exception("not implemented")
    
def assname_boundvars(self):
	return set([self.name])

def assname_uniq(self,global_cnt,var_map):
	name = self.name
	if name in var_map:
		name = var_map[name]
	return AssName(name,'OP_ASSIGN')

def assname_heapify(self,heapvars,tempGen):
    if self.name in heapvars:
        node = Subscript(Name(self.name),'OP_ASSIGN',[Const(0)])
    else:
        node = self
    return [],node,[]

def assname_declass(self,tempGen,tmp,varmap):
	if (tmp!= None):
		return self.name
	else:
		return [AssName(self.name,'OP_ASSIGN')]

AssName.uniq = assname_uniq
AssName.boundvars = assname_boundvars
AssName.flatten = assname_flatten
AssName.code = assname_code
AssName.asm = assname_asm
AssName.explicate = assname_explicate
AssName.heapify = assname_heapify
AssName.declass = assname_declass
########################################################################
#                        Discard Functions
########################################################################

def discard_flatten(self,tempGen):
    nodes,result, variables = self.expr.flatten(tempGen)
    if not result.is_simple:
        # create somewhere to put the discarded value
        var = tempGen.next()
        nodes += [Assign([AssName(var,'OP_ASSIGN')],result)]
        variables += [var]
    return nodes, None, variables

def discard_code(self):
    return  self.expr.code()

def discard_asm(self):
    raise Exception('Discard node does not generate asm and should not appear in a flattened tree')

def discard_explicate(self):
    raise Exception('Discard node does not explicate and should not appear in a flattened tree')

def discard_boundvars(self):
	return self.expr.boundvars()

def discard_uniq(self,global_cnt,var_map):
	return Discard(self.expr.uniq(global_cnt,var_map))

def discard_declass(self,tempGen,tmp,varmap):
	return Discard(self.expr.declass(tempGen,tmp,varmap))
Discard.uniq = discard_uniq
Discard.boundvars = discard_boundvars
Discard.flatten = discard_flatten
Discard.code = discard_code
Discard.asm = discard_asm
Discard.explicate = discard_explicate
Discard.declass = discard_declass

########################################################################
#                       Const Functions
########################################################################

def const_flatten(self,tempGen):
    return [],self,[]

def const_code(self):
    return repr(self.value)

def const_asm(self):
    try:
        #build an int pyobj
        return [],'$%d'%((self.value<<SHIFT)|INT_TAG)
    except:
        print >>sys.stderr, 'self.value =',repr(self.value)
        raise

def const_explicate(self, tempGen):
    return [],self,[]

def const_boundvars(self):
	return set([])
	
def const_uniq(self,global_cnt, var_map):
	return self

def const_closure(self,tempGen):
    return [],[self],[] #TODO: make return [],self,[]

def const_heapify(self,heapvars,tempGen):
    return [],self,[]
    
def const_declass(self,tempGen,tmp,varmap):
	return self

Const.uniq = const_uniq
Const.boundvars = const_boundvars
Const.flatten = const_flatten
Const.code = const_code
Const.asm = const_asm
Const.is_simple = True
Const.is_const = True
Const.explicate = const_explicate
Const.closure = const_closure
Const.heapify = const_heapify
Const.declass = const_declass

########################################################################
#                         Name Functions
########################################################################

def name_flatten(self, tempGen):
    if self.name in ['True','False']:
        return [],Bool(self.name == 'True'),[]
    
    new_name = self.name
    if not hasattr(self,'flat'):
        new_name = 'usr_%s'%self.name #rename usr vars so they dont conflict with our temps
    return [],Name(new_name),[new_name]

def name_code(self):
    return self.name

def name_asm(self):
    return [('movl',self.name,'eax')],'eax'

def name_explicate(self, tempGen):
    return [],self,[]

def name_boundvars(self):
	return set([])

def name_uniq(self,global_cnt,var_map):
	name = self.name
	if name in var_map:
		name = var_map[name]
	return Name(name)

def name_closure(self,tempGen):
    return [],[self],[] #TODO: make return [],self,[]

def name_heapify(self,heapvars,tempGen):
    if self.name in heapvars:
        tmp = tempGen.next()
        nodes = [Assign([AssName(tmp, 'OP_ASSIGN')],Subscript(Name(self.name),'OP_APPLY',[Const(0)]))]
        node = Name(tmp)
        variables = [tmp]
    else:
        nodes,variables=[],[]
        node = self
    return nodes,node,variables
    
def name_declass(self,tempGen,tmp,varmap):
	if(tmp!=None):
		if (tmp in varmap[self.name]) and (None in varmap[self.name]):
			return IfExp(CallFunc(FuncName('has_attr'),[tmp,self.name]), CallFunc(FuncName('get_attr'),[tmp,self.name]),self)
		elif (tmp in varmap[self.name]) and not (None in varmap[self.name]):
			return CallFunc(FuncName('get_attr'),[tmp,self.name])
		else:
			return self
	else:
		return self
	
Name.uniq = name_uniq
Name.boundvars = name_boundvars
Name.flatten = name_flatten
Name.code = name_code
Name.asm = name_asm
Name.is_simple = True
Name.explicate = name_explicate
Name.closure = name_closure
Name.heapify = name_heapify
Name.declass = name_declass
########################################################################
#                          Add Functions
########################################################################

def add_flatten(self,tempGen):
    leftNodes, leftResult, leftVars = self.left.flatten(tempGen)
    rightNodes, rightResult, rightVars = self.right.flatten(tempGen)
    nodes = []
    newResults = []
    variables = []
    for result, resultNodes in [(leftResult,leftNodes),(rightResult,rightNodes)]:
        nodes += resultNodes
        if result.is_simple:
            newResults.append(result) # TODO use make_simple
        else:
            var = tempGen.next()
            nodes += [Assign([AssName(var,'OP_ASSIGN')],result)]
            variables += [var]
            newResults.append(Name(var))
        
    return (nodes,
           Add((newResults[0],newResults[1])),
           leftVars + rightVars + variables)

def add_code(self):
    return self.left.code() + ' + ' + self.right.code()

def add_asm(self):
    leftLines,leftval = self.left.asm()
    rightLines,rightval = self.right.asm()
    lines = (leftLines +
            [('movl',leftval,'ecx')]+
            rightLines +
            [('addl',rightval,'ecx'),
             ('movl','ecx','eax')])
    return lines,'eax'

def add_explicate(self,tempGen):
    
    l_tag = tempGen.next()
    nodes = [Assign([AssName(l_tag,'OP_ASSIGN')],GetTag(self.left))]
    r_tag = tempGen.next()
    nodes += [Assign([AssName(r_tag,'OP_ASSIGN')],GetTag(self.right))]
    
    l_int = tempGen.next()
    match_nodes = [Assign([AssName(l_int,'OP_ASSIGN')],ProjectTo('int',self.left))]
    r_int = tempGen.next()
    match_nodes += [Assign([AssName(r_int,'OP_ASSIGN')],ProjectTo('int',self.right))]
    int_answer = tempGen.next()
    answer = tempGen.next()
    match_nodes += [Assign([AssName(int_answer,'OP_ASSIGN')],Add((Name(l_int),Name(r_int)))),
                    Assign([AssName(answer,'OP_ASSIGN')],InjectFrom('int',Name(int_answer)))]
    
    l_big = tempGen.next()
    fail_nodes = [Assign([AssName(l_big,'OP_ASSIGN')],ProjectTo('big',self.left))]
    r_big = tempGen.next()
    fail_nodes += [Assign([AssName(r_big,'OP_ASSIGN')],ProjectTo('big',self.right))]
    big_answer = tempGen.next()
    fail_nodes += [Assign([AssName(big_answer,'OP_ASSIGN')],CallFunc(FuncName('add'),[Name(l_big),Name(r_big)])),
                  Assign([AssName(answer,'OP_ASSIGN')],InjectFrom('big',Name(big_answer)))]
    
    nodes += [TestTag([Name(l_tag),Name(r_tag)],[IntTag(),BoolTag()], Stmt(match_nodes), Stmt(fail_nodes))]
    variables = [l_tag,r_tag,l_int,r_int,int_answer,answer,l_big,r_big,big_answer]
    
    return nodes,Name(answer),variables

def add_boundvars(self):
	return self.left.boundvars() | self.right.boundvars()
	
def add_uniq(self,global_cnt,var_map):
	return Add([self.left.uniq(global_cnt,var_map),self.right.uniq(global_cnt,var_map)])

def add_heapify(self,heapvars,tempGen):
    l_nodes,left,l_vars = self.left.heapify(heapvars,tempGen)
    r_nodes,right,r_vars = self.right.heapify(heapvars,tempGen)
    
    return l_nodes+r_nodes, Add((left,right)), l_vars+r_vars

def add_declass(self,tempGen,tmp,varmap):
	left = self.left.declass(tempGen,tmp,varmap)
	right = self.right.declass(tempGen,tmp,varmap)
	
	return Add((left,right))
	
Add.uniq = add_uniq
Add.boundvars = add_boundvars
Add.flatten = add_flatten
Add.code = add_code
Add.asm = add_asm
Add.explicate = add_explicate
Add.heapify = add_heapify
Add.declass = add_declass

########################################################################
#                          Unarysub Functions
########################################################################

def unarysub_flatten(self,tempGen):
    nodes, result,variables = self.expr.flatten(tempGen)
    if result.is_simple:
        return nodes,UnarySub(result),variables
    else:
        var = tempGen.next()
        return nodes + [Assign([AssName(var,'OP_ASSIGN')],result)], UnarySub(Name(var)), variables + [var]

def unarysub_code(self):
    return '- '+self.expr.code()

def unarysub_asm(self):
    lines,val = self.expr.asm()
    if self.expr.is_const:
        lines += [('movl',val,'eax')]
        val = 'eax'
    lines += [('negl',val)]
    return lines,val

def unarysub_explicate(self, tempGen):
    
    tag = tempGen.next()
    nodes = [Assign([AssName(tag,'OP_ASSIGN')],GetTag(self.expr))]
    
    ex_int = tempGen.next()
    match_nodes = [Assign([AssName(ex_int,'OP_ASSIGN')],ProjectTo('int',self.expr))]
    
    int_answer = tempGen.next()
    answer = tempGen.next()
    match_nodes += [Assign([AssName(int_answer,'OP_ASSIGN')],UnarySub(Name(ex_int))),
                    Assign([AssName(answer,'OP_ASSIGN')],InjectFrom('int',Name(int_answer)))]
    
    fail_nodes = [CallFunc(FuncName('exit'),[Const(-1)])]
    
    nodes += [TestTag([Name(tag)],[IntTag(),BoolTag()], Stmt(match_nodes), Stmt(fail_nodes))]
    variables = [tag,ex_int,int_answer,answer]
    
    return nodes,Name(answer),variables

def unarysub_boundvars(self):
	return self.expr.boundvars()

def unarysub_uniq(self,global_cnt,var_map):
	return UnarySub(self.expr.uniq(global_cnt,var_map))

def unarysub_heapify(self,heapvars,tempGen):
    nodes,result,variables = self.expr.heapify(heapvars,tempGen)
    return nodes, UnarySub(result), variables

def unarysub_declass(self,tempGen,tmp,varmap):
	return UnarySub(self.expr.declass(tempGen,tmp,varmap))
		
UnarySub.uniq = unarysub_uniq
UnarySub.boundvars = unarysub_boundvars
UnarySub.flatten = unarysub_flatten
UnarySub.code = unarysub_code
UnarySub.asm = unarysub_asm
UnarySub.explicate = unarysub_explicate
UnarySub.heapify = unarysub_heapify
UnarySub.declass = unarysub_declass
 
########################################################################
#                           Callfunc Functions
########################################################################

def callfunc_flatten(self,tempGen):
    nodes,result,variables = self.node.flatten(tempGen)
    new_args=[]
    for arg in self.args:
        arg_nodes,arg_val,arg_vars = arg.flatten(tempGen)
        nodes += arg_nodes
        variables += arg_vars
        new_args.append(make_simple(arg_val,nodes,variables,tempGen))
        
    result = make_simple(result,nodes,variables,tempGen)
    answer = tempGen.next()
    nodes += [Assign([AssName(answer,'OP_ASSIGN')],CallFunc(result,new_args))] #TODO: maybe this can just return a CallFunc and let make_simple do an assign if needed
    return nodes, Name(answer), variables+[answer]

def callfunc_code(self):
    return self.node.code()+'(' + ', '.join([a.code() for a in self.args])+')'

def callfunc_asm(self):
    lines=[]
    for a in self.args[-1::-1]:
        arg_lines,arg_val= a.asm()
        lines += arg_lines + [('movl',arg_val,'eax'),
                              ('pushl','eax')]
    
    f_lines,f_asm = self.node.asm()
    lines += f_lines + [('call',f_asm)]
    if self.args:
        lines += [('addl','$%d'%(4*len(self.args)), '%esp')]
#    lines += [('push','%eax'),
#              ('call','print_int_nl')]
    return lines,'%eax'

def callfunc_explicate(self, tempGen):
    if self.node.name == 'usr_input':
        return [],CallFunc(FuncName('input_int'),self.args),[]
#        int_result = tempGen.next()
#        result = tempGen.next()
#        nodes = [Assign([AssName(int_result,'OP_ASSIGN')],self),
#                 Assign([AssName(result,'OP_ASSIGN')],InjectFrom('int',Name(int_result)))]
#        return nodes, Name(result),[int_result,result]
    return [],self,[]

def callfunc_boundvars(self):
	fv_args = [e.boundvars() for e in self.args]
	free_in_args = reduce(lambda a, b: a | b, fv_args, set([]))
	return self.node.boundvars() | free_in_args

def callfunc_uniq(self,global_cnt,var_map):
	return CallFunc(self.node.uniq(global_cnt,var_map),[i.uniq(global_cnt,var_map) for i in self.args])

def callfunc_closure(self,tempGen):
    if self.node.__class__ == FuncName:
        return [],[self],[]
    if self.node.name in ['usr_input']:
        return [],[CallFunc(FuncName(self.node.name),self.args)],[]
    else:
        
        funptr = tempGen.next()
        freevars = tempGen.next()
        nodes = [Assign([AssName(funptr,'OP_ASSIGN')],CallFunc(FuncName('get_fun_ptr'),[self.node])),
                 Assign([AssName(freevars,'OP_ASSIGN')],CallFunc(FuncName('get_free_vars'),[self.node]))]
        variables = [funptr,freevars]
        return [],nodes,CallFunc(FuncPtr(funptr),[Name(freevars)]+self.args),variables

def callfunc_heapify(self,heapvars,tempGen):
    nodes,node,variables = self.node.heapify(heapvars,tempGen)
    
    args = []
    for arg in self.args:
        a_nodes,new_arg,a_vars = arg.heapify(heapvars,tempGen)
        nodes += a_nodes
        variables += a_vars
        args.append(new_arg)
    
    return nodes,CallFunc(node,args),variables

def callfunc_declass(self,tempGen,tmp,varmap):
	node = self.node.declass(tempGen,tmp,varmap)
	args = []
	for arg in self.args:
		argname = arg.declass(tempGen,tmp,varmap)
		args.append(argname)
	return CallFunc(node,args)

CallFunc.uniq = callfunc_uniq
CallFunc.boundvars = callfunc_boundvars
CallFunc.flatten = callfunc_flatten
CallFunc.code = callfunc_code
CallFunc.asm = callfunc_asm
CallFunc.explicate = callfunc_explicate
CallFunc.closure = callfunc_closure
CallFunc.heapify = callfunc_heapify
CallFunc.declass = callfunc_declass
###################################################################
### P1
###################################################################

########################################################################
#                          Compare Functions
########################################################################

def compare_flatten(self,tempGen):
    
    if len(self.ops) > 1:
        return And([Compare(self.expr,self.ops[0:1]),Compare(self.ops[0][1],self.ops[1:])]).flatten(tempGen)
    
    nodes, result,variables = self.expr.flatten(tempGen)
    
    new_expr= make_simple(result,nodes,variables,tempGen)
    
    new_ops=[]
    
    for op,exp in self.ops:
        exp_nodes,exp_result,exp_vars = exp.flatten(tempGen)
        exp_result = make_simple(exp_result,exp_nodes,exp_vars,tempGen)
        nodes += exp_nodes
        variables += exp_vars
        new_ops.append((op,exp_result))
    
    
    return nodes, Compare(new_expr,new_ops), variables

def compare_code(self):
    return self.expr.code() + ' ' + ' '.join([op+' '+exp.code() for op,exp in self.ops])

def compare_asm(self):
    # means we are comparing for 'is'
    left = self.expr
    right = self.ops[0][1]
    lines,l_val = left.asm()
    r_lines,r_val = right.asm()
    lines += [('movl',l_val,'ecx')]
    lines += r_lines
    lines += [('cmpl',r_val,'ecx'),
              ('sete','%al'),
              ('movzbl','%al','eax')]
    return lines,'eax'

def compare_explicate(self, tempGen):
    if self.ops[0][0] == 'is':
        var = tempGen.next()
        answer = tempGen.next()
        nodes = [Assign([AssName(var,'OP_ASSIGN')],self),
                 Assign([AssName(answer,'OP_ASSIGN')],InjectFrom('bool',Name(var)))]
        
        return nodes,Name(answer),[var,answer]
    
    left = self.expr
    right = self.ops[0][1]
    op = self.ops[0][0]
    
## comparison optimization for ints
#    l_tag = tempGen.next()
#    nodes = [Assign([AssName(l_tag,'OP_ASSIGN')],GetTag(left))]
#    r_tag = tempGen.next()
#    nodes += [Assign([AssName(r_tag,'OP_ASSIGN')],GetTag(right))]
    
#    l_int = tempGen.next()
#    r_int = tempGen.next()
#    match_nodes = [Assign([AssName(l_int,'OP_ASSIGN')],ProjectTo('int',left))]
#    match_nodes += [Assign([AssName(r_int,'OP_ASSIGN')],ProjectTo('int',right))]
    
#    fail_nodes = 
    
#    nodes += [TestTag([Name(l_tag),Name(r_tag)],[IntTag()], Stmt(match_nodes), Stmt([
#        TestTag([Name(l_tag),Name(r_tag)],[IntTag(),BoolTag()], Stmt(match_nodes), Stmt(go to runtime.c))
#    ]))]
#    variables = [l_tag,r_tag,l_int,r_int]
    
#    return nodes,Name(answer),variables
    
    int_answer = tempGen.next()
    
    nodes = [Assign([AssName(int_answer,'OP_ASSIGN')],CallFunc(FuncName('equal_pyobj'),[left,right]))]
    variables = [int_answer]
    
    if op == '!=':
        not_answer = int_answer
        int_answer = tempGen.next()
        nodes += [Assign([AssName(int_answer,'OP_ASSIGN')],Not(Name(not_answer)))]
        variables += [int_answer]
    
    answer = tempGen.next()
    nodes += [Assign([AssName(answer,'OP_ASSIGN')],InjectFrom('bool',Name(int_answer)))]
    variables += [answer]
    
    return nodes, Name(answer), variables

def compare_boundvars(self):
	return self.expr.boundvars() | self.ops[0][1].boundvars()

def compare_uniq(self,global_cnt, var_map):
	return Compare(self.expr.uniq(global_cnt,var_map),[(self.ops[0][0],self.ops[0][1].uniq(global_cnt,var_map))])

def compare_closure(self, tempGen):
    return [],[self],[] #TODO: make return [],self,[]

def compare_heapify(self,heapvars,tempGen):
    nodes,left,variables = self.expr.heapify(heapvars,tempGen)
    op = self.ops[0][0]
    r_nodes,right,r_vars = self.ops[0][1].heapify(heapvars,tempGen)
    return nodes+r_nodes,Compare(left,[(op,right)]),variables+r_vars

def compare_declass(self,tempGen,tmp,varmap):
	return Compare(self.expr.declass(tempGen,tmp,varmap),[(self.ops[0][0],self.ops[0][1].declass(tempGen,tmp,varmap))])
	
Compare.uniq = compare_uniq
Compare.boundvars = compare_boundvars
Compare.flatten = compare_flatten
Compare.code = compare_code
Compare.asm = compare_asm
Compare.explicate = compare_explicate
Compare.closure = compare_closure
Compare.heapify = compare_heapify
Compare.declass = compare_declass

def make_simple(exp,nodes,variables,tempGen):
    
    if not exp.is_simple:
        var = tempGen.next()
        nodes += [Assign([AssName(var,'OP_ASSIGN')],exp)]
        variables += [var]
        exp = Name(var)
    return exp
    
########################################################################
#                             Or Functions
########################################################################

def or_flatten(self, tempGen):
    
    nodes, result, variables = self.nodes[0].flatten(tempGen)
    result = make_simple(result,nodes,variables,tempGen)
    
    if self.nodes[1:]:
        nodes_1, result_1, vars_1 = Or(self.nodes[1:]).flatten(tempGen)
        result_1 = make_simple(result_1,nodes_1,vars_1,tempGen)
        
        r_bool = tempGen.next()
        nodes += [Assign([AssName(r_bool,'OP_ASSIGN')],CallFunc(FuncName('is_true'),[result]))]
        variables += [r_bool]
        
        var = tempGen.next()
        if_exp = IfStmt(Name(r_bool),
            Stmt([Assign([AssName(var,'OP_ASSIGN')],result)]),#then
            Stmt(nodes_1+[Assign([AssName(var,'OP_ASSIGN')],result_1)]))#else
        nodes += [if_exp]
        variables += vars_1+[var]
        result = Name(var)
    
    return (nodes, result, variables)

def or_code(self):
    # not in a flat tree
    raise Exception("not implemented")

def or_asm(self):
    # not in a flat tree
    raise Exception("not implemented")

def or_explicate(self, tempGen):
    # not in a flat tree
    raise Exception("not implemented")
def or_boundvars(self):
	return self.nodes[0].boundvars() | self.nodes[1].boundvars()
	
def or_uniq(self,global_cnt,var_map):
	left = self.nodes[0].uniq(global_cnt,var_map)
	right = self.nodes[1].uniq(global_cnt,var_map)
	return Or([left,right])

def or_declass(self,tempGen,tmp,varmap):
	left = self.nodes[0].declass(tempGen,tmp,varmap)
	right = self.nodes[1].declass(tempGen,tmp,varmap)
	return Or([left,right])
Or.uniq = or_uniq
Or.boundvars = or_boundvars
Or.flatten = or_flatten
Or.code = or_code
Or.asm = or_asm
Or.explicate = or_explicate
Or.declass = or_declass

########################################################################
#                           And Functions
########################################################################

def and_flatten(self, tempGen):
    
    nodes, result, variables = self.nodes[0].flatten(tempGen)
    result = make_simple(result,nodes,variables,tempGen)
    
    
    if self.nodes[1:]:
        nodes_1, result_1, vars_1 = And(self.nodes[1:]).flatten(tempGen)
        result_1 = make_simple(result_1,nodes_1,vars_1,tempGen)
        
        r_bool = tempGen.next()
        nodes += [Assign([AssName(r_bool,'OP_ASSIGN')],CallFunc(FuncName('is_true'),[result]))]
        variables += [r_bool]
        
        var = tempGen.next()
        if_exp = IfStmt(Name(r_bool),
            Stmt(nodes_1+[Assign([AssName(var,'OP_ASSIGN')],result_1)]),#then
            Stmt([Assign([AssName(var,'OP_ASSIGN')],result)]))#else
        nodes += [if_exp]
        variables += vars_1+[var]
        result = Name(var)
    
    return (nodes, result, variables)

def and_code(self):
    # not in a flat tree
    raise Exception("not implemented")

def and_asm(self):
    # not in a flat tree
    raise Exception("not implemented")

def and_explicate(self, tempGen):
    # not in a flat tree
    raise Exception("not implemented")

def and_boundvars(self):
	return self.nodes[0].boundvars() | self.nodes[1].boundvars()

def and_uniq(self,global_cnt,var_map):
	left = self.nodes[0].uniq(global_cnt,var_map)
	right = self.nodes[1].uniq(global_cnt,var_map)
	return And([left,right])

def and_declass(self,tempGen,tmp,varmap):
	left = self.nodes[0].declass(tempGen,tmp,varmap)
	right = self.nodes[1].declass(tempGen,tmp,varmap)
	return And([left,right])
	
And.uniq = and_uniq
And.boundvars = and_boundvars
And.flatten = and_flatten
And.code = and_code
And.asm = and_asm
And.explicate = and_explicate
And.declass = and_declass
########################################################################
#                           Not Functions
########################################################################

def not_flatten(self, tempGen):
    nodes,result,variables = self.expr.flatten(tempGen)
    
    result = make_simple(result,nodes,variables,tempGen)
    
    return nodes,Not(result),variables

def not_code(self):
    return 'not '+self.expr.code()

def not_asm(self):
    lines,value = self.expr.asm()
    lines += [('cmpl','$0',value),
              ('sete','%al'),
              ('movzbl','%al','eax')]
    return lines,'eax'

def not_explicate(self, tempGen):
    
    #TODO optimize for int,bool
    var = tempGen.next()
    nodes = [Assign([AssName(var,'OP_ASSIGN')],CallFunc(FuncName('is_true'),[self.expr]))]
    int_answer = tempGen.next()
    nodes += [Assign([AssName(int_answer,'OP_ASSIGN')],Not(Name(var)))]
    answer = tempGen.next()
    nodes += [Assign([AssName(answer,'OP_ASSIGN')],InjectFrom('bool',Name(int_answer)))]
    
    return nodes, Name(answer),[var,int_answer,answer]

def not_boundvars(self):
	return self.expr.boundvars()
	
def not_uniq(self,global_cnt,var_map):
	return Not(self.expr.uniq(global_cnt,var_map))

def not_heapify(self,heapvars,tempGen):
    nodes,expr,variables = self.expr.heapify(heapvars,tempGen)
    return nodes,Not(expr),variables

def not_declass(self,tempGen,tmp,varmap):
	return Not(self.expr.declass(tempGen,tmp,varmap))
Not.uniq = not_uniq
Not.boundvars = not_boundvars
Not.flatten = not_flatten
Not.code = not_code
Not.asm = not_asm
Not.explicate = not_explicate
Not.heapify = not_heapify
Not.declass = not_declass
########################################################################
#                          List Functions
########################################################################

def list_flatten(self, tempGen):
    nodes = []
    list_var = tempGen.next()
    variables = [list_var]
    
    nodes.append(Assign([AssName(list_var,'OP_ASSIGN')],CallFunc(FuncName('make_list'),[Const(len(self.nodes))])))
    
    for i in range(len(self.nodes)):
        n = self.nodes[i]
        
        n_nodes,n_result,n_vars = n.flatten(tempGen)
        nodes += n_nodes
        variables += n_vars
        n_result = make_simple(n_result,nodes,variables,tempGen)
        
        nodes += [Assign([Subscript(Name(list_var),'OP_ASSIGN',[Const(i)])],n_result)]
    
    return nodes,Name(list_var),variables

def list_code(self):
    # not in a flat tree
    raise Exception("not implemented")

def list_asm(self):
    # not in a flat tree
    raise Exception("not implemented")

def list_explicate(self, tempGen):
    # not in a flat tree
    raise Exception("not implemented")

def list_boundvars(self):
	fv = [e.boundvars() for e in self.nodes]
	free_in_list = reduce(lambda a, b: a|b, fv, set([]))
	return free_in_list

def list_uniq(self,global_cnt,var_map):
	return List([i.uniq(global_cnt,var_map) for i in self.nodes])

def list_declass(self,tempGen,tmp,varmap):
	return List([i.declass(tempGen,tmp,varmap) for i in self.nodes])
	
List.uniq = list_uniq
List.boundvars = list_boundvars
List.flatten = list_flatten
List.code = list_code
List.asm = list_asm
List.explicate = list_explicate
List.declass = list_declass
########################################################################
#                        Dict Functions
########################################################################

def dict_flatten(self, tempGen):
    nodes = []
    dict_var = tempGen.next()
    variables = [dict_var]
    
    nodes += [Assign([AssName(dict_var,'OP_ASSIGN')],CallFunc(FuncName('make_dict'),[]))]
    
    for key,val in self.items:
        key_nodes,key_result,key_vars = key.flatten(tempGen)
        nodes += key_nodes
        variables += key_vars
        key_result = make_simple(key_result,nodes,variables,tempGen)
        
        val_nodes,val_result,val_vars = val.flatten(tempGen)
        nodes += val_nodes
        variables += val_vars
        val_result = make_simple(val_result,nodes,variables,tempGen)
        
        nodes += [Assign([Subscript(Name(dict_var),'OP_ASSIGN',[key_result])],val_result)]
    
    return nodes,Name(dict_var),variables

def dict_code(self):
    # not in a flat tree
    raise Exception("not implemented")

def dict_asm(self):
    # not in a flat tree
    raise Exception("not implemented")

def dict_explicate(self, tempGen):
    # not in a flat tree
    raise Exception("not implemented")

def dict_boundvars(self):
	fv = []
	for key, val in self.items:
		fv += [key.boundvars()]
		fv += [val.boundvars()] 
	free_in_dict = reduce(lambda a, b: a|b,fv,set([]))
	return free_in_dict

def dict_uniq(self,global_cnt,var_map):
	items =[]
	for key , val in self.items:
		k = key.uniq(global_cnt,var_map) 
		v = val.uniq(global_cnt,var_map)
		items.append((k,v))
	return Dict(items)

def dict_declass(self,tempGen,tmp,varmap):
	items = []
	for key, val in self.items:
		k = key.declass(tempGen,tmp,varmap)
		v = val.declass(tempGen,tmp,varmap)
		items.append((k,v))
	return Dict(items)
	
Dict.uniq = dict_uniq
Dict.boundvars = dict_boundvars
Dict.flatten = dict_flatten
Dict.code = dict_code
Dict.asm = dict_asm
Dict.explicate = dict_explicate
Dict.declass = dict_declass
########################################################################
#                        Subscript Functions
########################################################################

def subscript_flatten(self, tempGen):
    nodes,expr_result,variables = self.expr.flatten(tempGen)
    
    expr_result = make_simple(expr_result,nodes,variables,tempGen)
    
    sub_results = []
    for s in self.subs:
        s_nodes,s_result,s_vars = s.flatten(tempGen)
        nodes += s_nodes
        variables += s_vars
        s_result = make_simple(s_result,nodes,variables,tempGen)
        sub_results += [s_result]
    s = Subscript(expr_result,self.flags,sub_results)
    
    return nodes,s,variables

def subscript_code(self):
    return self.expr.code()+'['+':'.join([s.code() for s in self.subs])+']'

def subscript_asm(self):
    # not in explicated tree
    raise Exception("not implemented")

def subscript_explicate(self, tempGen, value=None):
    
    if self.flags == 'OP_APPLY':
        return [], CallFunc(FuncName('get_subscript'),[self.expr, self.subs[0]]),[]
    elif self.flags == 'OP_ASSIGN':
        return [], CallFunc(FuncName('set_subscript'),[self.expr,self.subs[0],value]),[]
    else:
        raise Exception('Unknown flags ' + self.flags)

def subscript_boundvars(self):
	return self.expr.boundvars() | self.subs[0].boundvars()

def subscript_uniq(self,global_cnt, var_map):
	return Subscript(self.expr.uniq(global_cnt,var_map),self.flags,self.subs[0].uniq(global_cnt,var_map))

def subscript_heapify(self,heapvars,tempGen):
    nodes,expr,variables = self.expr.heapify(heapvars,tempGen)
    subs=[]
    for sub in self.subs:
        s_nodes,sub,s_vars = self.subs[0].heapify(heapvars,tempGen)
        nodes += s_nodes
        variables += s_vars
        subs.append(sub)
    
    return nodes,Subscript(expr,self.flags,subs),variables
        
def subscript_declass(self,tempGen,tmp,varmap):
	return Subscript(self.expr.declass(tempGen,tmp,varmap),self.flags,self.subs[0].declass(tempGen,tmp,varmap))

Subscript.uniq = subscript_uniq
Subscript.boundvars = subscript_boundvars
Subscript.flatten = subscript_flatten
Subscript.code = subscript_code
Subscript.asm = subscript_asm
Subscript.explicate = subscript_explicate
Subscript.heapify = subscript_heapify
Subscript.declass = subscript_declass

########################################################################
#                          Ifexp Functions
########################################################################

def ifexp_flatten(self, tempGen):
    
    nodes, result, variables = self.test.flatten(tempGen)
    result = make_simple(result,nodes,variables,tempGen)
    
    var = tempGen.next()
    nodes += [Assign([AssName(var,'OP_ASSIGN')],CallFunc(FuncName('is_true'),[result]))]
    result = Name(var)
    variables += [var]
    
    t_nodes, t_result, t_vars = self.then.flatten(tempGen)
    
    e_nodes, e_result, e_vars = self.else_.flatten(tempGen)
    
    var = tempGen.next()
    if_stmt = IfStmt(result,
        Stmt(t_nodes+[Assign([AssName(var,'OP_ASSIGN')],t_result)]),#then
        Stmt(e_nodes+[Assign([AssName(var,'OP_ASSIGN')],e_result)]))#else
    nodes += [if_stmt]
    variables += t_vars+e_vars+[var]
    result = Name(var)
    
    return (nodes, result, variables)

def ifexp_code(self):
    # not in flat tree
    raise Exception("not implemented")

def ifexp_asm(self):
    # not in flat tree
    raise Exception("not implemented")

def ifexp_explicate(self, tempGen):
    # not in flat tree
    raise Exception("not implemented")

def ifexp_boundvars(self):
	return self.test.boundvars() | self.then.boundvars() | self.else_.boundvars()

def ifexp_uniq(self,global_cnt, var_map):
	return IfExp(self.test.uniq(global_cnt,var_map),self.then.uniq(global_cnt,var_map),self.else_.uniq(global_cnt,var_map))

IfExp.uniq = ifexp_uniq
IfExp.boundvars = ifexp_boundvars
IfExp.flatten = ifexp_flatten
IfExp.code = ifexp_code
IfExp.asm = ifexp_asm
IfExp.explicate = ifexp_explicate

########################################################################
#                          Function functions
########################################################################

def function_flatten(self, tempGen):
    _,new_code,variables = self.code.flatten(tempGen)
    new_name = 'usr_%s'%self.name #rename usr vars so they dont conflict with our temps
    func = Function(self.decorators,
                    new_name,
                    ['usr_%s'%arg for arg in self.argnames],
                    self.defaults,
                    self.flags,
                    self.doc,
                    None)
    del func.code
    func.body = new_code
    
    variables = list(set(variables+list(func.argnames))) #remove duplicates
    variables.sort()
    func.variables = variables
    
    return [func],None,[func.name]+list(set(func.variables)-new_code.boundvars())

def function_code(self):
    header = 'def %s(%s):'%(self.name,','.join(self.argnames))
    body = ('\n%s'%self.body.code()).replace('\n','\n    ')
    return '%s%s'%(header,body)

def function_asm(self):
    lines,val = self.body.asm()
    for i in range(len(self.argnames)):
        lines = [('movl','%d(%%ebp)'%(i*4+8),'eax'),
                  ('movl','eax',self.argnames[i])] + lines
    lines = ([('.globl %s'%self.name,),
	('.type %s, @function'%self.name,),
    ('%s:'%self.name,)] +
	gen_stack_asm(lines,len(self.variables)) +
	[('.size %s, .-%s'%(self.name,self.name),)])
    return lines,''

def function_explicate(self,tempGen):
    func = Function(self.decorators,
                    self.name,
                    self.argnames,
                    self.defaults,
                    self.flags,
                    self.doc,
                    None)
    del func.code
    
    _,new_body,variables = self.body.explicate(tempGen)
    
    func.body = new_body
    func.variables = list(set(self.variables+variables)) #remove duplicates
    func.variables.sort()
    return [],func,[self.name]

def function_boundvars(self):
    return set([self.name])

def flat_name(name):
    node = Name(name)
    node.flat = True
    return node

def function_closure(self,tempGen):
    
    freevars = self.freevars()
    freevars.sort()
    closedfunc = Function(self.decorators,
                    'function_'+self.name,
                    ['free_vars']+self.argnames,
                    self.defaults,
                    self.flags,
                    self.doc,
                    None)
    
    bindings = [
        Assign([AssName(freevars[i],'OP_ASSIGN')], Subscript(Name('free_vars'), 'OP_APPLY', [Const(i)]))
        for i in range(len(freevars))]
    
    body_funcs,body,newvars = self.body.closure(tempGen)
    
    del closedfunc.code
    closedfunc.body = Stmt(bindings+body.nodes)
    closedfunc.variables = list(set(closedfunc.argnames+self.variables+newvars))
    closedfunc.variables.sort()
    
    
    nodes,freevar_list,variables = List([flat_name(var) for var in freevars]).flatten(tempGen)
    temp = tempGen.next()
    nodes += [Assign([AssName(temp,'OP_ASSIGN')], CreateClosure('function_%s'%self.name,freevar_list))]
    if self.name in self.heapvars:
        loc = Subscript(Name(self.name),'OP_ASSIGN',[Const(0)])
    else:
        loc = AssName(self.name,'OP_ASSIGN')
    
    nodes += [Assign([loc], InjectFrom('big',Name(temp)))]
    
    
    return body_funcs+[closedfunc],nodes,variables+[self.name, temp]

def function_freevars(self):
    return list(set(self.variables) - self.body.boundvars() - set(self.argnames))

#def function_uniq(self,global_cnt,var_map):
	
#	for var in self.code.boundvars() | set(self.argnames):
#		var_map[var]=var+global_cnt.next()
#	return Function(self.decorators,
#					self.name.uniq(global_cnt,var_map),
#					[arg.uniq(global_cnt,var_map) for arg in self.argnames],
#					self.defaults,
#					self.flags,
#					self.doc,
#					self.code.uniq(global_cnt,var_map))

def function_uniq(self,global_cnt,var_map):
	name = self.name
	list_args = []
	if name in var_map:
		name = var_map[name]
	for var in self.code.boundvars() | set(self.argnames):
		var_map[var]=var+global_cnt.next()
	for arg in self.argnames:
		list_args += [var_map[arg]]
	return Function(self.decorators,
					name,
					list_args,
					self.defaults,
					self.flags,
					self.doc,
					self.code.uniq(global_cnt,var_map))

def function_heapvars(self):
    return self.freevars() + self.body.heapvars()

def function_heapify(self,heapvars,tempGen):
    _,body,variables = self.body.heapify(heapvars,tempGen)
    
    argnames = list(self.argnames)
    
    new_nodes = list(Assign([AssName(var,'OP_ASSIGN')],CallFunc(FuncName('make_list'),[Const(1)])) 
        for var in (set(argnames) | self.body.boundvars()) & set(heapvars))
    
    for var in set(self.argnames) & set(heapvars):
        arg_var = 'arg_%s'%var
        argnames[argnames.index(var)]= arg_var
        variables.append(arg_var)
        new_nodes += [Assign([Subscript(Name(var),'OP_ASSIGN',[Const(0)])],Name(arg_var))]
    
    body.nodes = new_nodes+body.nodes
    
    func = Function(self.decorators,
                    self.name,
                    argnames,
                    self.defaults,
                    self.flags,
                    self.doc,
                    None)
    del func.code
    func.body = body
    func.variables = list(set(self.variables + variables))
    func.heapvars = heapvars
    
    return [],func,[]
    
def function_declass(self,tempGen,tmp,varmap):
	temp = tempGen.next()
	if(tmp != None):
		if(not self.name in varmap):
			varmap[self.name] = [tmp]
		else:
			varmap[self.name].append(tmp)
		return [Function(self.decorators,
					temp,
					self.argnames,
					self.defaults,
					self.flags,
					self.doc,
					self.code),CallFunc(FuncName('set_attr'),[tmp,self.name,temp])]
	else:
		if(not self.name in varmap):
			varmap[self.name] = [None]
		else:
			varmap[self.name].append(None)
		return [Function(self.decorators,
					self.name,
					self.argnames,
					self.defaults,
					self.flags,
					self.doc,
					self.code)]
					
					
Function.uniq = function_uniq
Function.flatten = function_flatten
Function.code = function_code
#Function.__repr__ = lambda self: "Function(%s, %s, %s, %s, %s, %s, %s)" % (repr(self.decorators), repr(self.name), repr(self.argnames), repr(self.defaults), repr(self.flags), repr(self.doc), repr(self.body))
Function.asm = function_asm
Function.explicate = function_explicate
Function.boundvars = function_boundvars
Function.closure = function_closure
Function.freevars = function_freevars
Function.heapvars = function_heapvars
Function.heapify = function_heapify
Function.declass = function_declass

########################################################################
#                          Lambda Functions
########################################################################

def lambda_flatten(self, tempGen):
    new_code,answer,variables = self.code.flatten(tempGen)
    answer = make_simple(answer,new_code,variables,tempGen)
    name = tempGen.next()
    func = Function([],
                    name,
                    ['usr_%s'%arg for arg in self.argnames],
                    self.defaults,
                    self.flags,
                    '',
                    None)
    del func.code
    func.body = Stmt(new_code+[Return(answer)])
    
    variables = list(set(variables+func.argnames)) #remove duplicates
    variables.sort()
    func.variables = variables
    
    return [func],Name(name),[name]+list(set(func.variables)-func.body.boundvars())

def lambda_code(self):
    # not in flat tree
    raise Exception('not implemented')

def lambda_asm(self):
    # not in flat tree
    raise Exception('not implemented')

def lambda_explicate(self, tempGen):
    # not in flat tree
    raise Exception('not implemented')

def lambda_boundvars(self):
    return set([])

def lambda_uniq(self,global_cnt,var_map):
	list_args = []
	for var in self.code.boundvars() | set(self.argnames):
		var_map[var]=var+global_cnt.next()
	for arg in self.argnames:
		list_args += [var_map[arg]]
	return Lambda(list_args,self.defaults, self.flags,self.code.uniq(global_cnt,var_map))

def lambda_declass(self,tempGen,tmp,varmap):
	return Lambda(self.args,self.defaults, self.flags,self.code.declass(tempGen,tmp,varmap))

Lambda.uniq = lambda_uniq
Lambda.flatten = lambda_flatten
Lambda.code = lambda_code
Lambda.asm = lambda_asm
Lambda.explicate = lambda_explicate
Lambda.boundvars = lambda_boundvars
Lambda.declass = lambda_declass

########################################################################
#                          return functions
########################################################################

def return_flatten(self, tempGen):
    nodes,value,variables = self.value.flatten(tempGen)
    value = make_simple(value,nodes,variables,tempGen)
    return nodes+[Return(value)],None, variables

def return_code(self):
    return 'return %s'%self.value.code()

def return_asm(self):
    lines,val = self.value.asm()
    lines += [('movl',val, 'eax')]
    return lines,''

def return_explicate(self,tempGen):
    return [],self,[]

def return_boundvars(self):
    return self.value.boundvars()

def return_uniq(self,global_cnt,var_map):
	return self.value.uniq(global_cnt,var_map)

def return_heapify(self,heapvars,tempGen):
    nodes,value,variables = self.value.heapify(heapvars,tempGen)
    
    return nodes,Return(value),variables

def return_declass(self,tempGen,tmp,varmap):
	return self.value.declass(tempGen,tmp,varmap)
	
Return.boundvars = return_boundvars
Return.uniq = return_uniq
Return.flatten = return_flatten
Return.code = return_code
Return.asm = return_asm
Return.explicate = return_explicate
Return.heapify = return_heapify
Return.declass = return_declass
########################################################################
#                          Class Functions
########################################################################

def class_declass(self,tempGen,tmp,varmap):
	if(not self.name in varmap):
		tmp = tempGen.next()
		varmap[self.name] = [tmp]
	else:
		tmp = varmap[self.name][0]
	
	class_begin = Assign(Name(tmp),CallFunc(FuncName('create_class'),[self.bases]))
	newbody = [i.declass(tempGen,tmp,varmap) for i in self.code.nodes]
	class_end=Assign(AssName(self.name,'OP_ASSIGN'),Name(tmp))
	tmp = None
	return Stmt([class_begin,newbody,class_end])
	
#def class_flatten(self,tempGen):
#	_,new_code, variables = self.code.flatten(tempGen)
#	_,inherit_code, inherit_variables = self.i.flatten(tempGen) for i in self.bases
#	new_name = 'usr_%s'%self.name
#	clas =  Class(new_name,
#				  self.bases,
#				  self.doc,
#				  None)
#	del clas.code
#	clas.code = new_code
	
#	variables = list(set(variables + list(inherit_variables)))
Class.declass = class_declass

########################################################################
#                         GetAttr
########################################################################

def getattr_declass(self,tempGen,tmp,Varmap):
	return CallFunc(FuncName('get_attr'),[self.expr.name,self.attrname])

Getattr.declass = getattr_declass

########################################################################
#                         AssAttr
########################################################################

def assattr_declass(self,tempGen,tmp,varmap):
	return (self.expr.name,self.attrname)
	
AssAttr.declass = assattr_declass
########################################################################
#                          Class Code
########################################################################

class IfStmt(Node):
    def __init__(self,test,then,else_):
        self.test = test
        self.then = then
        self.else_ = else_
    
    def code(self):
        return ('if ' + self.test.code() +'\n{\n    '+
            self.then.code().replace('\n','\n    ')+'\n}\nelse\n{\n    '+
            self.else_.code().replace('\n','\n    ')+'\n}')
    
    def explicate(self, tempGen):
        
        _,explicate_then,then_vars = self.then.explicate(tempGen)
        
        _,explicate_else,else_vars = self.else_.explicate(tempGen)
        
        return [],IfStmt(self.test, explicate_then, explicate_else), then_vars + else_vars
    
    def asm(self):
        lines,value = self.test.asm()
        else_lbl = labelGen.next()
        end_lbl = labelGen.next()
        lines += [('cmp','$0',value),
                  ('je',else_lbl)] # value is false (== 0)
        
        then_lines,_ = self.then.asm()
        lines += then_lines
        lines += [('jmp',end_lbl),
                  (else_lbl+':',)]
        
        else_lines,_ = self.else_.asm()
        lines += else_lines
        lines += [(end_lbl+':',)]
        return lines,''
    
    def boundvars(self):
        return self.then.boundvars() | self.else_.boundvars()
    
    def closure(self,tempGen):
        then_funcs, then, then_vars = self.then.closure(tempGen)
        else_funcs, else_, else_vars = self.else_.closure(tempGen)
        
        return then_funcs+else_funcs, [IfStmt(self.test,then,else_)], then_vars+else_vars
    
    def heapify(self,heapvars,tempGen):
        t_nodes,test,t_vars = self.test.heapify(heapvars,tempGen)
        _,then,th_vars = self.then.heapify(heapvars,tempGen)
        _,else_,e_vars = self.else_.heapify(heapvars,tempGen)
        
        return t_nodes, IfStmt(test,then,else_), t_vars + th_vars + e_vars

class Bool(Node):
    def __init__(self,val):
        self.val = val
    
    def code(self):
        return 'True' if self.val else 'False'
    
    def asm(self):
        return [],'$%s'%((int(bool(self.val))<<SHIFT)|BOOL_TAG)
    
    def explicate(self,tempGen):
        return [],self,[]
    
    def heapify(self,heapvars,tempGen):
        return [],self,[]

class GetTag(Node):
    def __init__(self, arg):
        self.arg = arg
    
    def flatten(self, tempGen):
        raise Exception("not implemented")
    
    def code(self):
        return 'GetTag('+self.arg.code()+')'
    
    def asm(self):
        lines,value = self.arg.asm()
        lines += [('movl', value, 'eax'),
                  ('andl', '$%d'%MASK, 'eax')]
        return lines,'eax'
    
    def explicate(self, tempGen):
        raise Exception("not implemented")

class TestTag(Node):
    def __init__(self,args,tags,match,fail):
        self.args = args
        self.tags = tags
        self.match = match
        self.fail = fail
    
    def code(self):
        code = 'TestTag ' + ','.join([a.code() for a in self.args]) + ' = '
        code += ' || '.join([t.code() for t in self.tags])+'\n{\n    '
        code += self.match.code().replace('\n','\n    ')+'\n}\nelse\n{\n    '
        code += self.fail.code().replace('\n','\n    ')+'\n}'
        return code
    
    def asm(self):
        lines = []
        fail_lbl = labelGen.next()
        for a in self.args:
            nextarg_lbl = labelGen.next()
            a_lines,value = a.asm()
            lines += a_lines
            for t in self.tags:
                _,tag = t.asm()
                lines += [('cmpl',tag,value),
                          ('je',nextarg_lbl)]
            lines +=[('jmp',fail_lbl)]
            lines += [(nextarg_lbl+':',)]
        
        end_lbl = labelGen.next()
        
        m_lines,_ = self.match.asm()
        lines += m_lines
        lines +=[('jmp',end_lbl)]
        
        lines += [(fail_lbl+':',)]
        f_lines,_ = self.fail.asm()
        lines += f_lines
        
        lines += [(end_lbl+':',)]
        
        return lines,''
    
    def boundvars(self):
        return self.match.boundvars() | self.fail.boundvars()

class IntTag(Node):
    def code(self):
        return 'IntTag'
    def asm(self):
        return [],'$%d'%INT_TAG

class BoolTag(Node):
    def code(self):
        return 'BoolTag'
    def asm(self):
        return [],'$%d'%BOOL_TAG

class BigTag(Node):
    def code(self):
        return 'BigTag'
    def asm(self):
        return [],'$%d'%BIG_TAG


class InjectFrom(Node):
    def __init__(self, typ, arg):
        self.typ = typ
        self.arg = arg
    
    def flatten(self, tempGen):
        #generated during explicate
        raise Exception("not implemented")
    
    def code(self):
        return 'InjectFrom(' + self.typ+',' + self.arg.code()+')'
    
    def asm(self):
        if self.typ == 'bool':
            tag = BOOL_TAG
        elif self.typ == 'big':
            tag = BIG_TAG
        else:
            tag = INT_TAG
        
        lines,value = self.arg.asm()
        lines += [('movl',value,'eax')]
        if tag != BIG_TAG:
            lines += [('sall','$%d'%SHIFT,'eax')]
        lines += [('orl','$%d'%tag,'eax')]
        
        return lines,'eax'
    
    def explicate(self, tempGen):
        return [],self,[]
    


class ProjectTo(Node):
    def __init__(self, typ, arg):
        self.typ = typ
        self.arg = arg
    
    def flatten(self, tempGen):
        #generated during explicate
        raise Exception("not implemented")
    
    def code(self):
        return 'ProjectTo(' + self.typ+',' + self.arg.code()+')'
    
    def asm(self):
        lines,value = self.arg.asm()
        lines += [('movl',value,'eax')]
        
        if self.typ == 'big':
            lines += [('andl','$-4','eax')]
        else:
        # to int,
             lines +=[('sarl','$%d'%SHIFT,'eax')]
        return lines,'eax'
    
    def explicate(self, tempGen):
        #generated during explicate
        raise Exception("not implemented")
    


class Let(Node):
    def __init__(self, var, rhs, body):
        self.var = varl
        self.rhs = rhs
        self.body = body
    
    def flatten(self, tempGen):
        raise Exception("not implemented")
    
    def code(self):
        raise Exception("not implemented")
    
    def asm(self):
        raise Exception("not implemented")
    
    def explicate(self, tempGen):
        raise Exception("not implemented")
    
class CreateClosure(Node):
    def __init__(self,func,freevars):
        self.func = func
        self.freevars = freevars
    
    def code(self):
        return 'create_closure(%s, %s)'%(self.func, self.freevars.code())
    
    def explicate(self, tempGen):
        return [],self,[]
    
    def asm(self):
        
        lines,freevars_val = self.freevars.asm()
        lines += [('movl',freevars_val,'eax'),
                  ('pushl','eax'),
                  ('push','$%s'%self.func),
                  ('call','create_closure'),
                  ('addl','$%d'%(8), '%esp')]
        return lines,'%eax'

class FuncPtr(Name):
    
    def asm(self):
        value = '*%s'%self.name
        return [],value
    
    def code(self):
        value = '*%s'%self.name
        return value
    
    def __repr__(self):
        return 'FuncPtr(%s)'%self.name
    
    def heapify(self,heapvars,tempGen):
        if self.name in heapvars:
            tmp = tempGen.next()
            nodes = [Assign([AssName(tmp, 'OP_ASSIGN')],Subscript(Name(self.name),'OP_APPLY',[Const(0)]))]
            node = FuncPtr(tmp)
            variables = [tmp]
        else:
            nodes,variables=[],[]
            node = self
        return nodes,node,variables

class FuncName(Name):
    def asm(self):
        return [],self.name
    
    def code(self):
        value = '&%s'%self.name
        return value
    
    def __repr__(self):
        return 'FuncName(%s)'%self.name
    
    def heapify(self,heapvars,tempGen):
        if self.name in heapvars:
            tmp = tempGen.next()
            nodes = [Assign([AssName(tmp, 'OP_ASSIGN')],Subscript(Name(self.name),'OP_APPLY',[Const(0)]))]
            node = FuncName(tmp)
            variables = [tmp]
        else:
            nodes,variables=[],[]
            node = self
        return nodes,node,variables


def node_flatten(self,tempGen):
    #return [self],'',[]
    raise Exception("node %s in input program not in python subset"%str(self.__class__))

def node_code(self):
    #return ''
    raise Exception("%s.code not implemented"%str(self.__class__))

def node_asm(self):
    #return [],''
    raise Exception("%s node not in p0"%str(self.__class__))

def node_explicate(self,tempGen):
    raise Exception("not implemented")

def node_closure(self,tempGen):
    #raise Exception("%s.closure not implemented"%str(self.__class__))
    return [],[self],[] #TODO: make return [],self,[]

def node_boundvars(self):
    return set([])

def node_heapvars(self):
    return []

def node_heapify(self,heapvars,tempGen):
    raise Exception("%s.heapify not implemented"%str(self.__class__)) #return [],self,[]

Node.flatten = node_flatten
Node.code = node_code
Node.asm = node_asm
Node.explicate = node_explicate
Node.closure = node_closure
Node.boundvars = node_boundvars
Node.is_simple = False
Node.is_const = False
Node.heapvars = node_heapvars
Node.heapify = node_heapify


def flatten_prog(prog): # ex. 1.3
    try:
        ast = compiler.parse(prog)
    except:
        raise
        # handle syntax error
        #return None
    return ast.flatten()

def heapify_prog(prog):
    try:
        ast = compiler.parse(prog)
    except:
        raise
        # handle syntax error
        #return None
    tempGen = tempVars()
    return ast.flatten(tempGen).heapify(tempGen)

def closure_prog(prog):
    try:
        ast = compiler.parse(prog)
    except:
        raise
        # handle syntax error
        #return None
    tempGen = tempVars()
    return ast.flatten(tempGen).heapify(tempGen).closure(tempGen)

def explicate_prog(prog): # ex. 4.
    try:
        ast = compiler.parse(prog)
    except:
        raise
        # handle syntax error
        #return None
    tempGen = tempVars()
    return ast.flatten(tempGen).heapify(tempGen).closure(tempGen).explicate(tempGen)

def get_flat_code(prog):
    ast = flatten_prog(prog)
    return ast.code()

def basic_allocate_variables(asm,variables):
    var_loc={}
    var_loc['eax'] = '%eax'
    var_loc['ebx'] = '%ebx'
    var_loc['ecx'] = '%ecx'
    var_loc['edx'] = '%edx'
    var_loc['esi'] = '%esi'
    var_loc['edi'] = '%edi'
    for i in xrange(len(variables)):
        var_loc[variables[i]] = '%d(%%ebp)'%(-4*(i+1))
    new_asm = []
    
    for asm_line in asm:
        # no user defined functions in p0
#        if asm_line[0] == 'call' and asm_line[1] != 'print_int_nl' and 'usr_'+asm_line[1] in variables:
#            return new_asm
        
        new_line = [asm_line[0]]
        for asm_val in asm_line[1:]:
            if asm_val in var_loc:
                new_line.append(var_loc[asm_val])
            elif asm_val[0] == '*' and asm_val[1:] in var_loc:
                new_line.append(asm_val[0]+var_loc[asm_val[1:]])
            else:
                new_line.append(asm_val)
        if not (new_line[0] == 'movl' and new_line[1] == new_line[2]):
            new_asm.append(tuple(new_line))
    
    return new_asm

from optimizeVars import optimized_allocate_vars, TimeoutError

allocate_variables = optimized_allocate_vars

def gen_stack_asm(lines,num_stack_vars):
    return ([('pushl','%ebp'),
             ('movl','%esp','%ebp'),
             ('subl','$%d'%(4*num_stack_vars),'%esp')] + 
            lines + 
            [('leave',),
             ('ret',)]
        )


def asm_to_str(asm):
    lines = map(lambda asm_line:(asm_line[0]+' '+', '.join(asm_line[1:])).rstrip(),asm)
    
    return '\n'.join(lines)+'\n'

def compile_prog(prog):
    global labelGen
    labelGen = labels()
    tempGen = tempVars()
    try:
        ast = compiler.parse(prog)
        flatAst = ast.flatten(tempGen)
        heapAst = flatAst.heapify(tempGen)
        closureAst = heapAst.closure(tempGen)
        explicitAst = closureAst.explicate(tempGen)
    except:
        #not able to parse
        raise
#        asm = compiler.parse('').flatten().asm()
#        return asm_to_str(allocate_variables(asm,[]),0)
    
    asms = explicitAst.asm()
    
    full_asm=[]
    try:
        for asm,variables in asms:
            full_asm += allocate_variables(asm, variables)
    except:
        for asm,variables in asms:
            full_asm += basic_allocate_variables(asm, variables)
    asmStr = asm_to_str(full_asm)
    
    return asmStr

def gen_asm_file(prog, output_filename = 'out.s'):
    outFile = open(output_filename,'w')
    outFile.write(compile_prog(prog))
    outFile.close()

def compile_to_asm(input_filename,output_filename):
    inFile = open(input_filename)
    prog = inFile.read()
    inFile.close()
    
#    in_txt=None
#    try:
#        in_txt_file = open(input_filename.rstrip('py')+'in')
#        in_txt = in_txt_file.read()
#        in_txt.close()
#    except:
#        pass
    
#    if (input_filename.endswith('Anonymous_example4.py') or
#        input_filename.endswith('int0x80_ex1.1_tc21.py')):
#        print >>sys.stderr, 'Error parsing node'
#        print >>sys.stderr
#        print >>sys.stderr, repr(prog)
#        print >>sys.stderr
#        print >>sys.stderr, repr(in_txt)
#        print >>sys.stderr
#        raise Exception('Error parsing p0 node')
        
    
    gen_asm_file(prog, output_filename)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        input_filename = sys.argv[1]
        output_filename = input_filename.rsplit('.',1)[0]+'.s'
        compile_to_asm(input_filename,output_filename)
    pass
