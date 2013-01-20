'''
Created on Jan 20, 2013

@author: Scott Pigman
'''
from inspect import isfunction, ismethod 
import itertools


class TypeDeclarationViolation(AssertionError):
    pass

try:
    # python 3.3+    
    from collections.abc import Iterable, Mapping
except ImportError:
    # python < 3.3    
    from collections import Iterable, Mapping
    
if hasattr(object, '__qualname__'):
    # python 3.3+
    def get_name(obj):
        return obj.__qualname__
else:
    # python < 3.3
    def get_name(obj):
        return obj.__name__ 

def get_type_str(type_declaration):
    try:
        return get_name(type_declaration)
    except AttributeError:
        return ('None' if type_declaration is None 
                else ', '.join(get_name(t) for t in type_declaration) )

def get_value_str(value):
    rep = str(value)
    if len(rep) > 32:
        rep = rep[:32] + '...'
    return rep


def check_condition(f, position, argname, argval, check_fcn):
    if not check_fcn(argval):
        raise_error(f, position, argname, argval, declared_types=(), condition=True)
        
def check_collection_contents(f, position, argname, collection, declared_type):
    if not all( isinstance(item, declared_type) for item in collection ):
        bad_types = set( type(i) for i in collection if type(i) is not declared_type )
        bad_values = set( v for v in collection if type(v) in bad_types )
        raise_error(f, position, argname, bad_values, declared_types={type(collection):declared_type}, actual_types=bad_types)


def check_collection(f, position, argname, collection, type_declaration:Mapping):
    actual_type = type(collection)
    if actual_type in type_declaration:
        check_collection_contents(f, position, argname, collection, type_declaration[actual_type])
    
    else:
        raise_error(f, position, argname, collection, declared_types=type_declaration.keys())


def check_declaration(f, position, argname, argval, declared_type):
    
    none_is_valid = declared_type is None
                
    if isinstance(declared_type, Iterable) and None in declared_type:
        declared_type = tuple( t for t in declared_type if t is not None)
        none_is_valid = True
                
    if isinstance(declared_type, Mapping):
        check_collection(f, position, argname, argval, declared_type)
        
    elif isfunction(declared_type) or ismethod(declared_type):
        check_condition(f, position, argname, argval, declared_type)
                    
    elif not ( (argval is None and none_is_valid) 
               or isinstance(argval, declared_type)
               ):
        raise_error(f, position, argname, argval, declared_types=declared_type )


def check_return(f, rvalue, argspec):
    if 'return' in argspec.annotations:
        rtype_declaration = argspec.annotations['return']
        
        if rtype_declaration is None:
            if rvalue is None:
                return rvalue
            else:
                raise_error(f, None, 'return value', rvalue, rtype_declaration)
        
        none_is_valid = rtype_declaration is None
        if (isinstance(rtype_declaration, Iterable) and None in rtype_declaration):
            none_is_valid = True
            rtype_declaration = tuple(t for t in rtype_declaration if t is not None)
        
        if (rvalue is None):
            if none_is_valid:
                return rvalue
            raise_error(f, None, 'return value', rvalue, rtype_declaration)
             
        elif isinstance(rtype_declaration, Mapping):
            check_collection(f, None, 'return value', rvalue, rtype_declaration)

        elif isfunction(rtype_declaration) or ismethod(rtype_declaration):
            check_condition(f, None, 'return value', rvalue, rtype_declaration)
                    
        elif not isinstance(rvalue, rtype_declaration):
            raise TypeDeclarationViolation(
                "%(func)s() -> <%(declared_rtype)s>: Actual type of return value, <%(rvalue)s>, is <%(actual_rtype)s>" 
                % (dict(func=get_name(f), 
                        declared_rtype=get_type_str(rtype_declaration), 
                        actual_rtype=get_type_str(type(rvalue)),
                        rvalue=get_value_str(rvalue))))
     
    return rvalue 

            
def raise_error(f, position, argname, argval, declared_types, actual_types=None, condition=False):
    if actual_types is None and not condition:
        actual_types = type(argval)
    raise TypeDeclarationViolation(
                    (
                     "%(func)s(): "
                     "%(parameter)s%(positional_info)s%(argname)s"
                     "=%(value)s: "
                     + ("Declared type=<%(declared_types)s>, " if not condition else "")
                     + ("actual type=<%(actual_types)s>." if not condition else "")         
                     + (" Fails condition check." if condition else "")
                    ) % 
                    dict(func=get_name(f), 
                         parameter='Parameter ' if position is not None else '',
                         positional_info="" if position is None else ("number %d, " % position), 
                         argname=argname, 
                         actual_types =get_type_str(actual_types), 
                         declared_types=get_type_str(declared_types) if not condition else '', 
                         value=get_value_str(argval)
                         )
                    )


def check_arg(f, position, argname, argval, argspec):
    if argname in argspec.annotations:
        declared_type = argspec.annotations[argname]
        check_declaration(f, position, argname, argval, declared_type)

def check_kwd(f, argname, argval, argspec):
    if argname in argspec.annotations:
        # parameter is a "regular" parameter passed in as a kw:
        # def f(x:int):
        #    ...
        # f(x=1) 
        declared_type = argspec.annotations[argname]
        check_declaration(f, None, argname, argval, declared_type)
        
    elif ( argname not in argspec.args # not a formally named parameter
           and argspec.varkw in argspec.annotations ): # parameters list includes "**kwds"
        
        # must be kw only argname. argspec.varkw is the name of the 
        # kw-only parameter:
        #
        # def f(**kwds):
        #    ...
        # f(x=1, y=2) # x & y will be handled by this branch
        declared_type = argspec.annotations[ argspec.varkw ]
        check_declaration(f, None, argname, argval, declared_type)

def check_kwds(f, kwds, argspec):
    for argname in kwds:
        check_kwd(f, argname, kwds[argname], argspec)
                
def check_args(f, args, argspec): 
    # extra args are positional only "*args" type of parameters.
    # the name of the *arg parameter is given by argspec.varags,
    # for for all of the extra positional parameters we pass that
    # name to the checker.               
    n_varargs = max(len(args) - len(argspec.args), 0)
    
    # If there are no "*args" params to process this will be
    # an empty list, []. If there are it will be name of the "*args"
    # parameter repeated as many times as there are varargs to process,
    # ['args', 'args',...,'args'].
    varargs = list(itertools.repeat(argspec.varargs, n_varargs))
    
    # if there are extra positional parameters (*args) then the zipped
    # list will look something like [ ('x',1), '('y',2), ('args',3), ('args',4)...]
    position = itertools.count(1)
    for (position, argname, argval) in zip(position, argspec.args + varargs, args):
        check_arg(f, position, argname, argval, argspec)        