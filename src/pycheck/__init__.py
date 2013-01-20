'''
    Created on Dec 22, 2012
    
    @author: Scott Pigman
'''

from .proxy import type_proxy

try:
    # python 3.3 and up:
    from collections.abc import Iterable
except ImportError:
    from collections import Iterable

#TODO: how to specify that return type is a tuple of heterogeneous types?
#TODO: How to specify generators that yield specific types of objects?

if __debug__:
    def checked(f):
        try:
            # python 3.3+
            from collections.abc import Mapping
        except ImportError:
            from collections import Mapping
            
        from inspect import isfunction, ismethod    
        import functools
        import inspect
        import itertools
        import sys
        
        argspec = inspect.getfullargspec(f)
        
        if sys.version < '3.3.3':
            def get_name(obj):
                return obj.__name__ 
        else:
            def get_name(obj):
                obj.__qualname__
        
        def type_repr(type_declaration):
            try:
                return get_name(type_declaration)
            except AttributeError:
                return ('None' if type_declaration is None 
                        else ', '.join(get_name(t) for t in type_declaration) )
        
        def value_repr(value):
            rep = str(value)
            if len(rep) > 32:
                rep = rep[:32] + '...'
            return rep
        
        def raise_error(position, argname, argval, declared_types, actual_types=None, condition=False):
            if actual_types is None:
                actual_types = ( type(argval), )
            raise TypeError(
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
                                 actual_types =type_repr(actual_types), 
                                 declared_types=type_repr(declared_types), 
                                 value=value_repr(argval)
                                 )
                            )

        def raise_error_return_none(rvalue):
            raise TypeError(
                             "%(func)s()->None returns <%(rvalue)s>"
                             % dict(func=get_name(f), rvalue=value_repr(rvalue))
                             )
    
    
        def check_condition(position, argname, argval, check_fcn):
            if not check_fcn(argval):
                raise_error(position, argname, argval, declared_types=(), condition=True)
                
        def check_collection_contents(position, argname, collection, declared_type):
            if not all( isinstance(item, declared_type) for item in collection ):
                bad_types = set( type(i) for i in collection if type(i) is not declared_type )
                bad_values = set( v for v in collection if type(v) in bad_types )
                raise_error(position, argname, bad_values, declared_types={type(collection):declared_type}, actual_types=bad_types)
    
    
        def check_collection(position, argname, collection, type_declaration:Mapping):
            actual_type = type(collection)
            if actual_type in type_declaration:
                check_collection_contents(position, argname, collection, type_declaration[actual_type])
            
            else:
                raise_error(position, argname, collection, declared_types=type_declaration.keys())
    
        
        def check_type(position, argname, argval, declared_type):
            
            none_is_valid = declared_type is None
                        
            if isinstance(declared_type, Iterable) and None in declared_type:
                declared_type = tuple( t for t in declared_type if t is not None)
                none_is_valid = True
                        
            if isinstance(declared_type, Mapping):
                check_collection(position, argname, argval, declared_type)
                
            elif isfunction(declared_type) or ismethod(declared_type):
                check_condition(position, argname, argval, declared_type)
                            
            elif not ( (argval is None and none_is_valid) 
                       or isinstance(argval, declared_type)
                       ):
                raise_error(position, argname, argval, declared_types=declared_type )
                    
    
        def check_return(rvalue):
            if 'return' in argspec.annotations:
                rtype_declaration = argspec.annotations['return']
                
                if rtype_declaration is None:
                    if rvalue is None:
                        return rvalue
                    else:
                        raise_error(None, 'return value', rvalue, rtype_declaration)
                
                none_is_valid = rtype_declaration is None
                if (isinstance(rtype_declaration, Iterable) and None in rtype_declaration):
                    none_is_valid = True
                    rtype_declaration = tuple(t for t in rtype_declaration if t is not None)
                
                if (rvalue is None):
                    if none_is_valid:
                        return rvalue
                    raise_error(None, 'return value', rvalue, rtype_declaration)
                     
                elif isinstance(rtype_declaration, Mapping):
                    check_collection(None, 'return value', rvalue, rtype_declaration)
    
                elif isfunction(rtype_declaration) or ismethod(rtype_declaration):
                    check_condition(None, 'return value', rvalue, rtype_declaration)
                            
                elif not isinstance(rvalue, rtype_declaration):
                    raise TypeError(
                        "%(func)s() -> <%(declared_rtype)s>: Actual type of return value, <%(rvalue)s>, is <%(actual_rtype)s>" 
                        % (dict(func=get_name(f), 
                                declared_rtype=type_repr(rtype_declaration), 
                                actual_rtype=type_repr(type(rvalue)),
                                rvalue=value_repr(rvalue))))
                
            return rvalue  
        def check_arg_type(position, argname, argval):
            if argname in argspec.annotations:
                declared_type = argspec.annotations[argname]
                check_type(position, argname, argval, declared_type)
    
        def check_kwd_type(argname, argval):
            if argname in argspec.annotations:
                # parameter is a "regular" parameter passed in as a kw:
                # def f(x:int):
                #    ...
                # f(x=1) 
                declared_type = argspec.annotations[argname]
                check_type(None, argname, argval, declared_type)
                
            elif ( argname not in argspec.args # not a formally named parameter
                   and argspec.varkw in argspec.annotations ): # parameters list includes "**kwds"
                
                # must be kw only argname. argspec.varkw is the name of the 
                # kw-only parameter:
                #
                # def f(**kwds):
                #    ...
                # f(x=1, y=2) # x & y will be handled by this branch
                declared_type = argspec.annotations[ argspec.varkw ]
                check_type(None, argname, argval, declared_type)
        
        def check_kwds(kwds:dict):
            for argname in kwds:
                check_kwd_type(argname, kwds[argname])
                        
        def check_args(args): 
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
                check_arg_type(position, argname, argval)
                                
        @functools.wraps(f)
        def checked_f(*args:list, **kwds:dict):  
            try:          
                check_args(args)
                check_kwds(kwds)
            except TypeError as e:
                raise TypeError(str(e)) from (None if sys.version >= '3.3.3' else e)                
    
            # Since errors thrown here have to do with the actual implementation of the
            # checked function, f, we don't want to re-wrap any exceptions thrown
            # since they are actually caused by the user's code.
            rvalue = f(*args, **kwds)

            try:                
                return check_return(rvalue)
            except TypeError as e:
                raise TypeError(str(e)) from (None if sys.version >= '3.3.3' else e)
            
        return checked_f

else:
    def checked(f):
        return f
