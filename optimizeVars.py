#!/usr/bin/env python

registers = ['%eax','%ecx','%edx','%ebx','%esi','%edi'] #ordered by preference

timeout=8.0;
from time import time

class TimeoutError(Exception):
    pass

def find_live_sets(asm,tstart):
    global time
    time = 0
    live_sets = [set([])]
    counts = {}
    graph = {}
    
    for line in asm[-1::-1]:
        if time()-tstart > timeout:
            raise TimeoutError('timeout')
        written=set()
        read=set()
        registers_written = set()
        
        if line[0] == 'call':
            registers_written = set(['%eax','%ecx','%edx'])
        elif line[0] == 'pushl':
            read.add(line[1])
        elif line[0] == 'movl':
            written.add(line[2])
            read.add(line[1])
        elif line[0] == 'addl':
            written.add(line[2])
            read |= set([line[1],line[2]])
        elif line[0] == 'negl':
            written.add(line[1])
            read.add(line[1])
        
        written = set(s for s in written if s[0].isalpha())
        read = set(s for s in read if s[0].isalpha())
        
        for var in written|read:
            if var in counts:
                counts[var] = counts[var]+1
            else:
                counts[var] = 1
        
        new_set = (live_sets[-1]-written-set(registers))|read|registers_written
        
        l=list(new_set)
        for i in range(len(l)):
            var0name = l[i]
            if not var0name in graph:
                var0 = Var(var0name)
                graph[var0name] = var0
            else:
                var0 = graph[var0name]
            
            for var1name in l[i+1:]:
                
                if not var1name in graph:
                    var1 = Var(var1name)
                    graph[var1name] = var1
                else:
                    var1 = graph[var1name]
                
                var0.add_neighbor(var1)
                var1.add_neighbor(var0)
        
        live_sets.append(new_set)
    
    live_sets.reverse()
    
    return live_sets, counts,graph
    
class Var(object):
    def __init__(self,name):
        self.name = name
        self.home = -1
        self.neighbors = set()
        self.invalid = set()
    
    def add_neighbor(self,neighbor):
        if neighbor != self:
            self.neighbors.add(neighbor)
    
    def invalidate(self,home):
        self.invalid.add(home)
    
    def set_home(self,home):
        self.home = home
        
        for n in self.neighbors:
            n.invalidate(home)
    
    def pick_home(self):
        home = 0
        while home in self.invalid:
            home += 1
        self.set_home(home)
    
    def __str__(self):
        return '<'+self.name+' in '+str(self.home)+' {'+', '.join(n.name for n in self.neighbors)+'}>'
    def __repr__(self):
        return str(self)
        
def gen_priority_list(counts,tstart):
    priority_list = [(counts[var],var) for var in counts]
    priority_list.sort()
    priority_list =  [var for count,var in priority_list]
    
    register_list=[]
    for var in priority_list:
        if time()-tstart > timeout:
            raise TimeoutError('timeout')
        if var.startswith('e'):
            register_list.append(var)
    
    for var in register_list:
        if time()-tstart > timeout:
            raise TimeoutError('timeout')
        priority_list.remove(var)
    
    return register_list+priority_list

def color_graph(graph,priority_list,tstart):
    
    for register in registers:
        if register in graph:
            graph[register].set_home(registers.index(register))
    for var in priority_list:
        if time()-tstart > timeout:
            raise TimeoutError('timeout')
        if graph[var].home < 0:
            graph[var].pick_home()
    return graph

def optimized_allocate_vars(asm,variables):
    
    tstart = time()
    live_sets,counts,graph = find_live_sets(asm,tstart)
    
#    for i in range(len(asm)):
#        print live_sets[i]
#        print asm[i]
    
    priority_list = gen_priority_list(counts,tstart)
    
    for var in priority_list:
        if var not in graph:
            graph[var] = Var(var)
    
    color_graph(graph,priority_list,tstart)
    
#    print graph
    
    new_asm = []
    homes = set()
    for i in range(len(asm)):
        if time()-tstart > timeout:
            raise TimeoutError('timeout')
        asm_line = asm[i]
        # no user defined functions in p0
        if asm_line[0] == 'call' and asm_line[1] != 'print_int_nl' and 'usr_'+asm_line[1] in variables:
            return new_asm

        # check for writes to dead vars, which is unnecesary
        if (((asm_line[0] == 'movl' or asm_line[0] == 'addl') 
              and asm_line[2] not in live_sets[i+1])
            or
            (asm_line[0] == 'negl'
              and asm_line[1] not in live_sets[i+1])
            ):
            continue
        
        new_line = [asm_line[0]]
        for asm_val in asm_line[1:]:
            if asm_val in graph:
                homes.add(graph[asm_val].home)
                if graph[asm_val].home < len(registers):
                    new_line.append(registers[graph[asm_val].home])
                else:
                    new_line.append('%d(%%ebp)'%(-4*(graph[asm_val].home-len(registers)+1)))
            else:
                new_line.append(asm_val)
        
        
        # check for moves to/from the same spot, which is unnecesary
        if not (new_line[0] == 'movl' and new_line[1] == new_line[2]):
            new_asm.append(tuple(new_line))
    
    return new_asm 
