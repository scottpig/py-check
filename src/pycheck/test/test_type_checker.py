'''
Created on Dec 22, 2012

@author: Scott Pigman
'''
import unittest
import sys
from pycheck import checked


@checked
def int_to_int(x : int) -> int:
    'Docstring'
    return x*x

@checked
def int_to_int_bad(x : int) -> int:
    'Docstring'
    return 'badval' 

@checked
def float_to_int(x:float) -> int:
    return int(x)

@checked
def unchecked_to_int(y) -> int:
    'doc of unchecked_to_int'
    return y * 2  

@checked
def int_to_float(x : int) -> float:
    'int_to_float doc'
    return x/x**x

@checked
def int_to_none(x : int) -> None:
    pass

@checked
def int_to_none_bad(x : int) -> None:
    return x # fails rtype test


@checked
def void_to_unchecked():
    return 9

@checked
def default_values(x : int, y : int=None) -> int:
    if y is None:
        y = 3
    return x*y

@checked
def returns_good_set() -> {set:int}:
    return set([1,2,3,4,5])

@checked
def returns_bad_set() -> {set:int}:
    return set([1,2,3,4,5.0])


@checked
def checked_arg(*params:int) -> int:
    return len(params)

@checked
def checked_kwd(**kwds:int) -> int:
    return len(kwds)

@checked
def every_type_of_param(required:int, defaulted:float=4.5, *pos:str, **named:str):
    pass



@checked
def bad_default_val(x:int=1.0):
    pass

class TestCase(unittest.TestCase):

    if sys.version < '3.2':
        # assertRaisesRegex() is not available in this version, so just fall back to 
        # standard assertRaises()
        def assertRaisesRegex(self, excClass, regx, callableObj):
            return self.assertRaises(excClass, callableObj)
        
        # assertIsInstance() not available, so implement it:
        def assertIsInstance(self, obj, expected_type):
            return self.assertTrue(isinstance(obj, expected_type))
       
    def test_docstring_preserved(self):       
        self.assertEqual(int_to_int.__doc__, 'Docstring', int_to_int.__doc__ )

    def test_name_preserved(self):        
        self.assertEqual(unchecked_to_int.__name__, 'unchecked_to_int', unchecked_to_int.__name__)

    def test_rtype_valid(self):            
        self.assertIsInstance(int_to_int(1), int)
        self.assertIsInstance(unchecked_to_int(2), int)
        self.assertIsInstance(int_to_float(3), float)
        self.assertIsInstance(float_to_int(4.5), int)
        
    @unittest.skipUnless(__debug__, "Errors only raised in debug mode")
    def test_paramtype_invalid(self):
        self.assertRaisesRegex(TypeError, 
                               r"int_to_int\(\): Parameter number 1, x=1\.1: Declared type=<int>, actual type=<float>\.", 
                               lambda: int_to_int(1.1)   )
        self.assertRaises(TypeError, lambda: int_to_float(3.0) )
        self.assertRaises(TypeError, lambda: float_to_int(4)   )
        
    def test_rtype_none_valid(self):                
        self.assertIsNone( int_to_none(8) )
        
    @unittest.skipUnless(__debug__, "Errors only raised in debug mode")
    def test_rtype_none_invalid(self):
        self.assertRaisesRegex( TypeError, 
                                r"int_to_none_bad\(\): return value=6: Declared type=<None>, actual type=<int>.", 
                                lambda: int_to_none_bad(6) )
        
    @unittest.skipUnless(__debug__, "Errors only raised in debug mode")
    def test_cannot_cast_rval(self):
        self.assertRaisesRegex( TypeError, 
                                r"unchecked_to_int\(\) -> <int>: Actual type of return value, <foofoo>, is <str>", 
                                lambda: unchecked_to_int("foo") )
        
        
    @unittest.skipUnless(__debug__, "Errors only raised in debug mode")
    def test_misc(self):    
        self.assertRaisesRegex( TypeError, 
                                r"default_values\(\): Parameter number 2, y=6\.0: Declared type=<int>, actual type=<float>.", 
                                lambda: default_values(4,6.0) 
                                )
        self.assertRaises( TypeError, lambda: default_values(4,y=6.0) )

        
        self.assertRaises( TypeError, lambda: default_values(4.0,6) )
        self.assertRaises( TypeError, lambda: default_values(x=4.0) )

        self.assertRaises( TypeError, lambda: default_values(x=4.0,y=6) )

        self.assertRaises( TypeError, lambda: default_values(4.0,6.0) )

        self.assertIsInstance( default_values(5), int)
        self.assertIsInstance( default_values(4,3), int)
        self.assertRaises(TypeError, lambda: default_values(2.3, 4.1) )
        
        self.assertRaises(TypeError, lambda: int_to_int_bad(8))
        
    def test_result_is_container(self):
        self.assertIsInstance(returns_good_set(), set)
    @unittest.skipUnless(__debug__, "Errors only raised in debug mode")
    def test_result_is_container_error(self):
        self.assertRaisesRegex(TypeError, "XXX", returns_bad_set)
        
    def test_checked_arg(self):
        self.assertEqual(checked_arg(1,3,4,4), 4)
    
    @unittest.skipUnless(__debug__, "Errors only raised in debug mode")
    def test_checked_arg_error(self):
        self.assertRaisesRegex(TypeError, 
                               r"checked_arg\(\): Parameter number 4, params=4\.0: Declared type=<int>, actual type=<float>\.", 
                               lambda: checked_arg(1,2,3,4.0))
        
        
    def test_every_type_of_param(self):
        self.assertIsNone( every_type_of_param(1) )
        self.assertIsNone( every_type_of_param(required=1) )
        self.assertIsNone( every_type_of_param(1,2.0) )
        self.assertIsNone( every_type_of_param(1,defaulted=2.0) )
        
        self.assertIsNone( every_type_of_param(required=1,defaulted=2.0) )
        
        self.assertIsNone( every_type_of_param(1,2.0,'a') )
        self.assertIsNone( every_type_of_param(1,2.0,'a','b') )
        self.assertIsNone( every_type_of_param(1,2.0,'a','b','c') )

        self.assertIsNone( every_type_of_param(1,x='foo') )
        self.assertIsNone( every_type_of_param(required=1,x='foo') )
        
        self.assertIsNone( every_type_of_param(1,2.0,x='foo') )
        self.assertIsNone( every_type_of_param(1,defaulted=2.0,x='foo') )
        self.assertIsNone( every_type_of_param(required=1,defaulted=2.0,x='foo') )

        self.assertIsNone( every_type_of_param(1,2.0,'a',x='foo'))
        self.assertIsNone( every_type_of_param(1,2.0,'a','b','c', x='boo', y='bar') )

    @unittest.skipUnless(__debug__, "Errors only raised in debug mode")
    def test_every_type_of_param_bad1(self):
        self.assertRaises(TypeError, lambda: every_type_of_param(1.0) )
        self.assertRaises(TypeError, lambda: every_type_of_param(required=1.0) )
        
        self.assertRaises(TypeError, lambda: every_type_of_param(1.0,2.0) )
        self.assertRaises(TypeError, lambda: every_type_of_param(1,2) )

        self.assertRaises(TypeError, lambda: every_type_of_param(1.0,defaulted=2.0) )
        self.assertRaises(TypeError, lambda: every_type_of_param(1,defaulted=2) )

        
        self.assertRaises(TypeError, lambda: every_type_of_param(1.0,2.0,'a') ) # first arg
        self.assertRaises(TypeError, lambda: every_type_of_param(1,2,'a') ) # second arg
        self.assertRaises(TypeError, lambda: every_type_of_param(1.0,x='foo') )
        

        
    @unittest.skipUnless(__debug__, "Errors only raised in debug mode")
    def test_every_type_of_param_bad3(self):
        self.assertRaises(TypeError, lambda: every_type_of_param(required=1.0,x='2') )
        
    @unittest.skipUnless(__debug__, "Errors only raised in debug mode")
    def test_every_type_of_param_bad5(self):
        
        self.assertRaises(TypeError, lambda: every_type_of_param(1.0,2.0,x='3') )
        self.assertRaises(TypeError, lambda: every_type_of_param(1,2,x='3') )
        

    @unittest.skipUnless(__debug__, "Errors only raised in debug mode")
    def test_every_type_of_param_bad7(self):
        self.assertRaises(TypeError, lambda: every_type_of_param(1.0,defaulted=2.0,x='3') )
        self.assertRaises(TypeError, lambda: every_type_of_param(1,defaulted=2,x='3') )
        

    @unittest.skipUnless(__debug__, "Errors only raised in debug mode")
    def test_every_type_of_param_bad9(self):
        
        self.assertRaises(TypeError, lambda: every_type_of_param(required=1.0,defaulted=2.0,x='3') )
        self.assertRaises(TypeError, lambda: every_type_of_param(required=1,defaulted=2,x='3') )

        
    @unittest.skipUnless(__debug__, "Errors only raised in debug mode")
    def test_every_type_of_param_bad11(self):
        self.assertRaises(TypeError, lambda: every_type_of_param(1.0,2.0, '3', x='4'))
    
    @unittest.skipUnless(__debug__, "Errors only raised in debug mode")
    def test_bad_positional_arg(self):
        self.assertRaises(TypeError, lambda: every_type_of_param(1,2.0, 3, x='4'))
        self.assertRaises(TypeError, lambda: every_type_of_param(1,2.0, 3.0) ) # third arg
    
    
    @unittest.skipUnless(__debug__, "Errors only raised in debug mode")
    def test_bad_kwd_only_param(self):
        self.assertRaises(TypeError, lambda: every_type_of_param(1  ,2.0, '3', x=4)) 
        self.assertRaises(TypeError, lambda: every_type_of_param(1,2.0,x=3) ) 
        self.assertRaises(TypeError, lambda: every_type_of_param(1,x=2) ) 
        self.assertRaises(TypeError, lambda: every_type_of_param(required=1,x=2) )
        self.assertRaises(TypeError, lambda: every_type_of_param(1,defaulted=2.0,x=3) ) 
        self.assertRaises(TypeError, lambda: every_type_of_param(required=1,defaulted=2.0,x=3) )
        self.assertRaises(TypeError, lambda: every_type_of_param(1  ,2.0, '3', x=4)) 


    def test_collections(self):

        @checked
        def collection_fcn(required:{set:int}, 
                           defaulted:{set:float}=set([1.0]), 
                           *positional:{set:str},
                           **named:{set:bytes}
                           ) -> None:
            return      
        
          
        self.assertIsNone(collection_fcn(set([1])) )
        self.assertRaises(TypeError, lambda: collection_fcn(set([1.0])) )
        
        self.assertIsNone(collection_fcn(required=set([1])) )
        self.assertRaises(TypeError, lambda: collection_fcn(required=set([1.0])) )

        self.assertIsNone(collection_fcn(set([1]), set([2.0]) ) )
        self.assertIsNone(collection_fcn(required=set([1]), defaulted=set([2.0]) ) )
        self.assertIsNone(collection_fcn(defaulted=set([1.0]), required=set([2]) ) )
        self.assertIsNone(collection_fcn(set([1]), defaulted=set([2.0]) ) )

        self.assertRaises(TypeError, lambda: collection_fcn(set([1.0]), set([2.0])) )
        self.assertRaises(TypeError, lambda: collection_fcn(set([1]), set([2])) )
        
        self.assertIsNone(collection_fcn(set([1]), set([2.0]), set(['3.0']), x=set([b'4.0'] ) ) )
        self.assertRaises(TypeError, lambda: collection_fcn(set([1]), set([2.0]), set([3.0])) )
        
        self.assertIsNone(collection_fcn(set([1]), set([2.0]), set(['3.0']), x=set([b'4.0'] ) ) )
        self.assertRaises(TypeError, lambda: collection_fcn(set([1]), set([2.0]), set(['3.0']), x=set([4.0])))
        
        # passing bad collection type:
        self.assertRaises(TypeError, lambda: collection_fcn([1,2,3]) )
        # collection_fcn([1,2,3])
        # collection_fcn(set([1,2.0,'3']))
        
    @unittest.expectedFailure
    def test_bad_annotation(self):
        self.assertRaisesRegex(TypeError, "^$", lambda: bad_default_val() )
        
    def test_preconditions(self):
        
        @checked
        def f(x:lambda x: x>=0) -> (lambda y:y>0):
            return x+1

        @checked
        def g(x:lambda x: x>=0) -> (lambda y:y>0):
            return x-1 
               
        self.assertEqual(f(0), 1)
        self.assertRaisesRegex(TypeError, 
                               r"(TestCase\.test_preconditions\.<locals>\.)?f\(\): Parameter number 1, x=-1:  Fails condition check\.", 
                               lambda: f(-1))
        
    @unittest.skipUnless(__debug__, "Errors only raised in debug mode")
    def test_multiple_types(self):
        
        @checked
        def good(x:(int, str)) -> (float, bytes):
            try:
                return x.encode()
            except:
                return float(x)
            
        @checked
        def bad(x:(int, str)) -> (float, bytes):
            return x
        
        self.assertEqual(good(1), 1.0)
        self.assertEqual(good("x"), b"x")
        
        self.assertRaises(TypeError, lambda: good(1.0))
        self.assertRaises(TypeError, lambda: good(b'foo'))
        
        
        self.assertRaises(TypeError, lambda: bad("x"))
        self.assertRaises(TypeError, lambda: bad(1))
        
        
    def test_type_or_none(self):
        @checked
        def f(x:(str,None))->(int,None):
            return len(x) if x else None
        
        self.assertEqual(f("foo"), 3)
        self.assertEqual(f(None), None)
        
#    int_to_int(2.0)
if __name__ == '__main__':
    import cProfile
    cProfile.run('unittest.main()', 'checked.prof')
#    import pstats
#    p = pstats.Stats('checked.prof')
#    p.sort_stats('name')
#    p.print_stats()


