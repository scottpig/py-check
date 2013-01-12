'''
    Created on Dec 22, 2012
    
    @author: PigmaR
'''
from collections.abc import Mapping
import functools
import inspect
import itertools


def checked(f):
    argspec = inspect.getfullargspec(f)

    def type_repr(type_declaration):
        try:
            return type_declaration.__qualname__
        except AttributeError:
            # type declaration is a tuple of types
            return ', '.join(t.__qualname__ for t in type_declaration)
        
    def value_repr(value):
        rep = str(value)
        if len(repr) > 32:
            rep = repr[:32] + '...'
        return rep
    
    def check_collection_contents(position, argname, collection, type_specification):
        
        expected_type = type_specification[type(collection)]
        
        if not all( isinstance(item, expected_type) for item in collection ):
            bad_types = set( type(i).__qualname__ for i in collection if type(i) is not expected_type )
            raise TypeError("%(func)s(): "
                            "Parameter %(positional_info)%(argname): "
                            "Allowed type(s): %(col_type)s containing %(allowed_types)s. "
                            "Actual type(s): %(actual_type)s"
                            % dict(func=f.__qualname__, 
                                   positional_info="" if position is None else ("number %d, " % position),
                                   col_type=type(collection).__qualname__,
                                   argname=argname, 
                                   actual_type=', '.join(t for t in bad_types), 
                                   allowed_types=type_repr(type_specification.keys())
                                   )
                            )


    def check_collection(position, argname, collection, type_specification:Mapping):
        
        if type(collection) in type_specification:
            check_collection_contents(position, argname, collection, type_specification)
        
        else:
            raise TypeError("%(func)s(): "
                            "Parameter %(positional_info)%(argname): "
                            "Allowed type(s): %(allowed_types)s. "
                            "Actual type: %(actual_type)s"
                            % dict(func=f.__qualname__, 
                                   positional_info="" if position is None else ("number %d, " % position),
                                   argname=argname, 
                                   actual_type=type(collection), 
                                   allowed_types=type_repr(type_specification.keys())
                                   )
                            )

            

    def check_type(position, argname, argval, argtype):
        if isinstance(argtype, Mapping):
            check_collection(position, argname, argval, argtype)
                        
        elif not isinstance(argval, argtype):
            
            raise TypeError("%(func)s(): "
                            "Parameter %(positional_info)%(argname): "
                            "Allowed type(s): %(allowed_type)s. "
                            "Actual type: %(actual_type)s. "
                            "Value = %(value)s"
                            % dict(
                                   func=f.__qualname__,
                                   positional_info="" if position is None else ("number %d, " % position),
                                   argname=argname, 
                                   actual_type=type(argval), 
                                   allowed_type=type_repr(argtype),
                                   value=value_repr(argval)
                                   )
                            )
                

    def cast_rvalue(rvalue, rtype):
        try:
            rvalue = rtype(rvalue)
        except (TypeError, ValueError):
            raise TypeError(
                "%(func)s(...) -> %(rtype)s: Cannot convert return value <%(rvalue)s> to %(rtype)s" 
                % (dict(func=f.__qualname__, 
                        rtype=rtype, 
                        rvalue=value_repr(rvalue)))) from None

        return rvalue

    def check_none_rtype(rvalue):
        if rvalue is not None:
            raise TypeError(
                             "%(func)s expected to return <None> but returns <%(rvalue)s>" 
                             % dict(func=f.__qualname__, rvalue=value_repr(rvalue))
                             )

    def check_return(rvalue):
        if 'return' in argspec.annotations:
            rtype = argspec.annotations['return']
            
            if rtype is None:
                check_none_rtype(rvalue)
            
            elif isinstance(rtype, Mapping):
                check_collection(0, 'return', rvalue, rtype)
            
            elif not isinstance(rvalue, rtype):
                    rvalue = cast_rvalue(rvalue, rtype)
            
        return rvalue  
    def check_arg_type(position, argname, argval):
        if argname in argspec.annotations:
            argtype = argspec.annotations[argname]
            check_type(position, argname, argval, argtype)

    def check_kwd_type(argname, argval):
        if argname in argspec.annotations:
            # parameter is a "regular" parameter passed in as a kw:
            # def f(x:int):
            #    ...
            # f(x=1) 
            argtype = argspec.annotations[argname]
            check_type(None, argname, argval, argtype)
            
        elif ( argname not in argspec.args # not a formally named parameter
               and argspec.varkw in argspec.annotations ): # parameters list includes "**kwds"
            
            # must be kw only argname. argspec.varkw is the name of the 
            # kw-only parameter:
            #
            # def f(**kwds):
            #    ...
            # f(x=1, y=2) # x & y will be handled by this branch
            argtype = argspec.annotations[ argspec.varkw ]
            check_type(None, argname, argval, argtype)
            
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
            return check_return(f(*args, **kwds))
        except TypeError as e:
            raise TypeError(str(e)) from None
        
    return checked_f


