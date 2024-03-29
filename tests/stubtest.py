
import os
import shutil
import tempfile

from tests.utils.process import spawn
from tests.utils.runtest import automakesuite, run
from tests.utils.testcase import TestCase

from tools.utils.subprocess import popen
from tools.utils.io import read_set

def GetPexportsLines(path):
    stream = popen("pexports", path.replace('/cygdrive/c', 'c:'))
    try:
        return set(map(lambda s: s.strip(), stream.readlines()))
    finally:
        stream.close()

class PythonStubTest(TestCase):

    def testPythonStub(self):
        path = os.path.join('tests', 'data', 'python26-pexports')
        python26exports = read_set(path)
        generatedExports = GetPexportsLines("build/ironclad/python26.dll")
        self.assertEquals(python26exports - generatedExports, set())

suite = automakesuite(locals())
if __name__ == '__main__':
    run(suite)
