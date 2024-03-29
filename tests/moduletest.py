import sys
from tests.utils.runtest import makesuite, run

from tests.utils.cpython import MakeItemsTablePtr, MakeMethodDef, MakeTypePtr
from tests.utils.memory import CreateTypes
from tests.utils.pythonmapper import MakeAndAddEmptyModule
from tests.utils.testcase import TestCase, WithMapper, WithMapperSubclass

from System import IntPtr

from Ironclad import Dispatcher, PythonMapper
from Ironclad.Structs import METH


class Py_InitModule4_SetupTest(TestCase):
    
    @WithMapper
    def testNewModuleHasDispatcher(self, mapper, _):
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = mapper.Retrieve(modulePtr)
        _dispatcher = module._dispatcher
        
        self.assertEquals(isinstance(_dispatcher, Dispatcher), True, "wrong dispatcher class")
        self.assertEquals(_dispatcher.mapper, mapper, "dispatcher had wrong mapper")
        

MODULE_PTR = IntPtr(54321)

class Py_InitModule4_Test(TestCase):

    def assert_Py_InitModule4_withSingleMethod(self, mapper, methodDef, TestModule):
        methods, deallocMethods = MakeItemsTablePtr([methodDef])
        try:
            modulePtr = mapper.Py_InitModule4(
                "test_module",
                methods,
                "test_docstring",
                MODULE_PTR,
                12345)

            module = mapper.Retrieve(modulePtr)
            test_module = sys.modules['test_module']

            for item in dir(test_module):
                self.assertEquals(getattr(module, item) is getattr(test_module, item),
                                  True, "%s didn't match" % item)
            TestModule(test_module, mapper)
        finally:
            mapper.Dispose()
            deallocMethods()


    def test_Py_InitModule4_CreatesPopulatedModule(self):
        mapper = PythonMapper()
        method, deallocMethod = MakeMethodDef(
            "harold", lambda _, __: IntPtr.Zero, METH.VARARGS, "harold's documentation")
        
        def testModule(test_module, _):
            self.assertEquals(test_module.__doc__, 'test_docstring',
                              'module docstring not remembered')
            self.assertTrue(callable(test_module.harold),
                            'function not remembered')
            self.assertTrue(callable(test_module._dispatcher.table['harold']),
                            'delegate not remembered')
            self.assertEquals(test_module.harold.__doc__, "harold's documentation",
                              'function docstring not remembered')

        self.assert_Py_InitModule4_withSingleMethod(mapper, method, testModule)
        deallocMethod()
        

    def test_Py_InitModule4_NoArgsFunction(self):
        mapper = PythonMapper()
        deallocTypes = CreateTypes(mapper)
        result = object()
        resultPtr = mapper.Store(result)
        mapper.IncRef(resultPtr)
        
        def func(_, __):
            self.assertEquals((_, __), (MODULE_PTR, IntPtr.Zero))
            return resultPtr
        method, deallocMethod = MakeMethodDef("func", func, METH.NOARGS)
        
        def testModule(module, mapper):
            self.assertEquals(module.func(), result, "not hooked up")
            
        self.assert_Py_InitModule4_withSingleMethod(mapper, method, testModule)
        deallocMethod()
        deallocTypes()


    def test_Py_InitModule4_OldargsFunction_OneArg(self):
        mapper = PythonMapper()
        deallocTypes = CreateTypes(mapper)
        arg = object()
        result = object()
        resultPtr = mapper.Store(result)
        mapper.IncRef(resultPtr)
        
        def func(_, argPtr):
            self.assertEquals(_, MODULE_PTR)
            self.assertEquals(mapper.Retrieve(argPtr), arg)
            return resultPtr
        method, deallocMethod = MakeMethodDef("func", func, METH.OLDARGS)
        
        def testModule(module, mapper):
            self.assertEquals(module.func(arg), result, "not hooked up")
            
        self.assert_Py_InitModule4_withSingleMethod(mapper, method, testModule)
        deallocMethod()
        deallocTypes()


    def test_Py_InitModule4_OldargsFunction_SomeArgs(self):
        mapper = PythonMapper()
        deallocTypes = CreateTypes(mapper)
        args = (object(), object())
        result = object()
        resultPtr = mapper.Store(result)
        mapper.IncRef(resultPtr)
        
        def func(_, argsPtr):
            self.assertEquals(_, MODULE_PTR)
            self.assertEquals(mapper.Retrieve(argsPtr), args)
            return resultPtr
        method, deallocMethod = MakeMethodDef("func", func, METH.OLDARGS)
        
        def testModule(module, mapper):
            self.assertEquals(module.func(*args), result, "not hooked up")
            
        self.assert_Py_InitModule4_withSingleMethod(mapper, method, testModule)
        deallocMethod()
        deallocTypes()


    def test_Py_InitModule4_ObjargFunction(self):
        mapper = PythonMapper()
        deallocTypes = CreateTypes(mapper)
        arg = object()
        result = object()
        resultPtr = mapper.Store(result)
        mapper.IncRef(resultPtr)
        
        def func(_, argPtr):
            self.assertEquals(_, MODULE_PTR)
            self.assertEquals(mapper.Retrieve(argPtr), arg)
            return resultPtr
        method, deallocMethod = MakeMethodDef("func", func, METH.O)
        
        def testModule(module, mapper):
            self.assertEquals(module.func(arg), result, "not hooked up")
            
        self.assert_Py_InitModule4_withSingleMethod(mapper, method, testModule)
        deallocMethod()
        deallocTypes()


    def test_Py_InitModule4_VarargsFunction(self):
        mapper = PythonMapper()
        deallocTypes = CreateTypes(mapper)
        args = (object(), object())
        result = object()
        resultPtr = mapper.Store(result)
        mapper.IncRef(resultPtr)
        
        def func(_, argsPtr):
            self.assertEquals(_, MODULE_PTR)
            self.assertEquals(mapper.Retrieve(argsPtr), args)
            return resultPtr
        method, deallocMethod = MakeMethodDef("func", func, METH.VARARGS)
        
        def testModule(module, mapper):
            self.assertEquals(module.func(*args), result, "not hooked up")
            
        self.assert_Py_InitModule4_withSingleMethod(mapper, method, testModule)
        deallocMethod()
        deallocTypes()


    def test_Py_InitModule4_VarargsKwargsFunction(self):
        mapper = PythonMapper()
        deallocTypes = CreateTypes(mapper)
        args = (object(), object())
        kwargs = {'a': object(), 'b': object()}
        result = object()
        resultPtr = mapper.Store(result)
        mapper.IncRef(resultPtr)
        
        def func(_, argsPtr, kwargsPtr):
            self.assertEquals(_, MODULE_PTR)
            self.assertEquals(mapper.Retrieve(argsPtr), args)
            self.assertEquals(mapper.Retrieve(kwargsPtr), kwargs)
            return resultPtr
        method, deallocMethod = MakeMethodDef("func", func, METH.VARARGS | METH.KEYWORDS)
        
        def testModule(module, mapper):
            self.assertEquals(module.func(*args, **kwargs), result, "not hooked up")
            
        self.assert_Py_InitModule4_withSingleMethod(mapper, method, testModule)
        deallocMethod()
        deallocTypes()
        
        
class PyModule_Functions_Test(TestCase):
    
    @WithMapper
    def testGetsDict(self, mapper, _):
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = mapper.Retrieve(modulePtr)
        
        moduleDict = mapper.Retrieve(mapper.PyModule_GetDict(modulePtr))
        moduleDict['random'] = 4
        
        self.assertEquals(module.random, 4, 'modified wrong dict')
        
    
    @WithMapper
    def testAddConstants(self, mapper, _):
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = mapper.Retrieve(modulePtr)
        
        self.assertEquals(mapper.PyModule_AddIntConstant(modulePtr, "i_am_an_int", -31000), 0, "reported failure")
        self.assertEquals(module.i_am_an_int, -31000)
        
        self.assertEquals(mapper.PyModule_AddStringConstant(modulePtr, "i_am_a_string", "how_long"), 0, "reported failure")
        self.assertEquals(module.i_am_a_string, "how_long")
        

    @WithMapper
    def testAddObjectToUnknownModuleFails(self, mapper, _):
        self.assertEquals(mapper.PyModule_AddObject(IntPtr.Zero, "zorro", IntPtr.Zero), -1,
                          "bad return on failure")


    @WithMapper
    def testAddObjectWithExistingReferenceAddsMappedObjectAndDecRefsPointer(self, mapper, _):
        testObject = object()
        testPtr = mapper.Store(testObject)
        mapper.IncRef(testPtr)
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = mapper.Retrieve(modulePtr)

        result = mapper.PyModule_AddObject(modulePtr, "testObject", testPtr)
        self.assertEquals(result, 0, "bad value for success")
        self.assertEquals(mapper.RefCount(testPtr), 1)
        self.assertEquals(module.testObject, testObject, "did not store real object")


    @WithMapper
    def assertAddsTypeWithData(self, tp_name, itemName, class__module__, class__name__, class__doc__, mapper, addDealloc):
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = mapper.Retrieve(modulePtr)
        
        typeSpec = {
            "tp_name": tp_name,
            "tp_doc": class__doc__
        }
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        addDealloc(deallocType)
        result = mapper.PyModule_AddObject(modulePtr, itemName, typePtr)
        self.assertEquals(result, 0, "reported failure")

        mappedClass = mapper.Retrieve(typePtr)
        generatedClass = getattr(module, itemName)
        self.assertEquals(mappedClass, generatedClass,
                          "failed to add new type to module")

        self.assertEquals(mappedClass.__doc__, class__doc__, "unexpected docstring")
        self.assertEquals(mappedClass.__name__, class__name__, "unexpected __name__")
        self.assertEquals(mappedClass.__module__, class__module__, "unexpected __module__")


    def testAddModule(self):
        self.assertAddsTypeWithData(
            "some.module.Klass",
            "KlassName",
            "some.module",
            "Klass",
            "Klass is some sort of class.\n\nYou may find it useful.",
        )
        self.assertAddsTypeWithData(
            "Klass",
            "KlassName",
            "",
            "Klass",
            "Klass is some sort of class.\nBeware, for its docstring contains '\\n's and similar trickery.",
        )


    @WithMapper
    def testPyModule_New(self, mapper, _):
        modulePtr = mapper.PyModule_New("forsooth")
        module = mapper.Retrieve(modulePtr)
        self.assertEquals(module.__name__, "forsooth")
        self.assertEquals(module.__doc__, "")
        


class ImportTest(TestCase):
    
    @WithMapper
    def testPyImport_ImportModule(self, mapper, _):
        modulePtr = mapper.Py_InitModule4(
            "test_module",
            IntPtr.Zero,
            "test_docstring",
            IntPtr.Zero,
            12345)
        
        self.assertEquals(mapper.PyImport_ImportModule("test_module"), modulePtr)
        self.assertEquals(mapper.RefCount(modulePtr), 2, "did not incref")
    
    @WithMapper
    def testPyImport_Import(self, mapper, _):
        modulePtr = mapper.Py_InitModule4(
            "test_module",
            IntPtr.Zero,
            "test_docstring",
            IntPtr.Zero,
            12345)
        
        self.assertEquals(mapper.PyImport_Import(mapper.Store("test_module")), modulePtr)
        self.assertEquals(mapper.RefCount(modulePtr), 2, "did not incref")
    
    @WithMapper
    def testPyImport_AddModule(self, mapper, _):
        sysPtr = mapper.PyImport_ImportModule("sys")
        modules = mapper.Retrieve(sysPtr).modules
        
        foobarbazPtr = mapper.PyImport_AddModule("foo.bar.baz")
        self.assertEquals(mapper.Retrieve(foobarbazPtr), modules['foo.bar.baz'])
        self.assertEquals('foo.bar' in modules, True)
        self.assertEquals(modules['foo.bar'].baz, modules['foo.bar.baz'])
        self.assertEquals('foo' in modules, True)
        self.assertEquals(modules['foo'].bar, modules['foo.bar'])

    
    @WithMapper
    def testPyImport_GetModuleDict(self, mapper, _):
        modulesPtr = mapper.PyImport_GetModuleDict()
        modules = mapper.Retrieve(modulesPtr)
        self.assertEquals(modules is sys.modules, True)
        
        mapper.IncRef(modulesPtr)
        mapper.ReleaseGIL()
        self.assertEquals(mapper.RefCount(modulesPtr), 1, 'borrowed reference not cleaned up')
        mapper.EnsureGIL()


    @WithMapper
    def testPyImport_ImportFunctions_Failure(self, mapper, _):
        self.assertEquals(mapper.PyImport_Import(mapper.Store('this_module_does_not_exist')), IntPtr.Zero)
        self.assertMapperHasError(mapper, ImportError)
        
        self.assertEquals(mapper.PyImport_ImportModule('this_module_does_not_exist'), IntPtr.Zero)
        self.assertMapperHasError(mapper, ImportError)



class NastyImportDetailsTest(TestCase):
    
    @WithMapperSubclass
    def testNameFixing_PyImport_AddModule_NamesMatch(self, mapper, _):
        mapper.importNames.Push('hungry.hungry.hippo')
        mapper.PyImport_AddModule("hippo")
        
        self.assertEquals(sys.modules.has_key("hippo"), False)
        self.assertEquals(sys.modules.has_key('hungry.hungry.hippo'), True)
        
        for key in sys.modules.keys():
            if key.startswith('hungry'):
                del sys.modules[key]
    
    
    @WithMapperSubclass
    def testNameFixing_PyImport_AddModule_NoMatch(self, mapper, _):
        mapper.importNames.Push('hungry.hungry.hippo')
        mapper.importNames.Push('angry.angry.alligator')
        mapper.PyImport_AddModule("hippo")
        
        self.assertEquals(sys.modules.has_key("hippo"), True)
        self.assertEquals(sys.modules.has_key('angry.angry.alligator'), False)
    
        del sys.modules['hippo']
        
    
    @WithMapperSubclass
    def testNameFixing_Py_InitModule4_NamesMatch(self, mapper, _):
        mapper.importFiles.Push('hippo_file')
        mapper.importNames.Push('hungry.hungry.hippo')
        mapper.Py_InitModule4("hippo", IntPtr.Zero, "test_docstring", IntPtr.Zero, 12345)
        
        self.assertEquals(sys.modules.has_key("hippo"), False)
        self.assertEquals(sys.modules['hungry.hungry.hippo'].__doc__, 'test_docstring')
        self.assertEquals(sys.modules['hungry.hungry.hippo'].__file__, 'hippo_file')
        
        for key in sys.modules.keys():
            if key.startswith('hungry'):
                del sys.modules[key]
    
    
    @WithMapperSubclass
    def testNameFixing_Py_InitModule4_NoMatch(self, mapper, _):
        mapper.importName = 'angry.angry.alligator'
        mapper.Py_InitModule4("hippo", IntPtr.Zero, "test_docstring", IntPtr.Zero, 12345)
        
        self.assertEquals(sys.modules.has_key("hippo"), True)
        self.assertEquals(sys.modules.has_key('angry.angry.alligator'), False)
    
        del sys.modules['hippo']
        



# not sure this is the right place for these tests
class BuiltinsTest(TestCase):
    
    @WithMapper
    def testPyEval_GetBuiltins(self, mapper, _):
        builtinsPtr = mapper.PyEval_GetBuiltins()
        import __builtin__
        self.assertEquals(mapper.Retrieve(builtinsPtr), __builtin__.__dict__)
        
        
        
class SysTest(TestCase):
    
    @WithMapper
    def testPySys_GetObject(self, mapper, _):
        modulesPtr = mapper.PySys_GetObject('modules')
        modules = mapper.Retrieve(modulesPtr)
        self.assertEquals(modules is sys.modules, True)


suite = makesuite(
    Py_InitModule4_SetupTest,
    Py_InitModule4_Test,
    PyModule_Functions_Test,
    ImportTest,
    NastyImportDetailsTest,
    BuiltinsTest, 
    SysTest, 
)

if __name__ == '__main__':
    run(suite)
