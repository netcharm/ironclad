using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

using Ironclad.Structs;

using Microsoft.Scripting;

using IronPython.Runtime;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;

namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        private IntPtr
        IC_PyString_Concat_Core(IntPtr str1Ptr, IntPtr str2Ptr)
        {
            try
            {
                // why read them, not retrieve them? can't cast string subtypes to string.
                string str1 = this.ReadPyString(str1Ptr);
                string str2 = this.ReadPyString(str2Ptr);
                return this.Store(str1 + str2);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }


        public override void
        PyString_Concat(IntPtr str1PtrPtr, IntPtr str2Ptr)
        {
            IntPtr str1Ptr = Marshal.ReadIntPtr(str1PtrPtr);
            if (str1Ptr == IntPtr.Zero)
            {
                return;
            }
            IntPtr str3Ptr = IntPtr.Zero;
            if (str2Ptr != IntPtr.Zero)
            {
                str3Ptr = this.IC_PyString_Concat_Core(str1Ptr, str2Ptr);
            }
            Marshal.WriteIntPtr(str1PtrPtr, str3Ptr);
            this.DecRef(str1Ptr);
        }

        public override void
        PyString_ConcatAndDel(IntPtr str1PtrPtr, IntPtr str2Ptr)
        {
            this.PyString_Concat(str1PtrPtr, str2Ptr);
            this.DecRef(str2Ptr);
        }


        public override IntPtr 
        PyString_FromString(IntPtr stringData)
        {
            IntPtr current = stringData;
            List<byte> bytesList = new List<byte>();
            while (CPyMarshal.ReadByte(current) != 0)
            {
                bytesList.Add(CPyMarshal.ReadByte(current));
                current = CPyMarshal.Offset(current, 1);
            }
            byte[] bytes = new byte[bytesList.Count];
            bytesList.CopyTo(bytes);
            IntPtr strPtr = this.CreatePyStringWithBytes(bytes);
            this.map.Associate(strPtr, this.StringFromBytes(bytes));
            return strPtr;
        }
        
        public override IntPtr
        PyString_FromStringAndSize(IntPtr stringData, int length)
        {
            if (stringData == IntPtr.Zero)
            {
                IntPtr data = this.AllocPyString(length);
                this.incompleteObjects[data] = UnmanagedDataMarker.PyStringObject;
                return data;
            }
            else
            {
                byte[] bytes = new byte[length];
                Marshal.Copy(stringData, bytes, 0, length);
                IntPtr strPtr = this.CreatePyStringWithBytes(bytes);
                this.map.Associate(strPtr, this.StringFromBytes(bytes));
                return strPtr;
            }
        }

        public override IntPtr
        PyString_InternFromString(IntPtr stringData)
        {
            IntPtr newStrPtr = PyString_FromString(stringData);
            IntPtr newStrPtrPtr = Marshal.AllocHGlobal(Marshal.SizeOf(typeof(IntPtr)));
            CPyMarshal.WritePtr(newStrPtrPtr, newStrPtr);
            this.PyString_InternInPlace(newStrPtrPtr);
            return CPyMarshal.ReadPtr(newStrPtrPtr);
        }

        public override void
        PyString_InternInPlace(IntPtr strPtrPtr)
        {
            IntPtr intStrPtr = IntPtr.Zero;
            IntPtr strPtr = CPyMarshal.ReadPtr(strPtrPtr);
            string str = (string)this.Retrieve(strPtr);

            if (this.internedStrings.ContainsKey(str))
            {
                intStrPtr = this.internedStrings[str];
            }
            else
            {
                intStrPtr = strPtr;
                this.internedStrings[str] = intStrPtr;
                this.IncRef(intStrPtr);
            }
            this.IncRef(intStrPtr);
            this.DecRef(strPtr);
            CPyMarshal.WritePtr(strPtrPtr, intStrPtr);
        }
        
        public override IntPtr
        PyString_AsString(IntPtr strPtr)
        {
            try
            {
                if (CPyMarshal.ReadPtrField(strPtr, typeof(PyObject), "ob_type") != this.PyString_Type)
                {
                    throw PythonOps.TypeError("PyString_AsString: not a string");
                }
                return CPyMarshal.Offset(strPtr, Marshal.OffsetOf(typeof(PyStringObject), "ob_sval"));
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }
        
        public override int
        PyString_AsStringAndSize(IntPtr strPtr, IntPtr dataPtrPtr, IntPtr sizePtr)
        {
            try
            {
                if (CPyMarshal.ReadPtrField(strPtr, typeof(PyObject), "ob_type") != this.PyString_Type)
                {
                    throw PythonOps.TypeError("PyString_AsStringAndSize: not a string");
                }
                
                IntPtr dataPtr = CPyMarshal.Offset(strPtr, Marshal.OffsetOf(typeof(PyStringObject), "ob_sval"));
                CPyMarshal.WritePtr(dataPtrPtr, dataPtr);
                
                int length = CPyMarshal.ReadIntField(strPtr, typeof(PyStringObject), "ob_size");
                if (sizePtr == IntPtr.Zero)
                {
                    for (int i = 0; i < length; ++i)
                    {
                        if (CPyMarshal.ReadByte(CPyMarshal.Offset(dataPtr, i)) == 0)
                        {
                            throw PythonOps.TypeError("PyString_AsStringAndSize: string contains embedded 0s, but sizePtr is null");
                        }
                    }
                }
                else
                {
                    CPyMarshal.WriteInt(sizePtr, length);
                }
                return 0;
            }
            catch (Exception e)
            {
                this.LastException = e;
                return -1;
            }
        }
        
        private int
        _PyString_Resize_Grow(IntPtr strPtrPtr, int newSize)
        {
            IntPtr oldStr = CPyMarshal.ReadPtr(strPtrPtr);
            IntPtr newStr = IntPtr.Zero;
            try
            {
                newStr = this.allocator.Realloc(
                    oldStr, Marshal.SizeOf(typeof(PyStringObject)) + newSize);
            }
            catch (OutOfMemoryException e)
            {
                this.LastException = e;
                this.PyObject_Free(oldStr);
                return -1;
            }
            CPyMarshal.WritePtr(strPtrPtr, newStr);
            this.incompleteObjects.Remove(oldStr);
            this.incompleteObjects[newStr] = UnmanagedDataMarker.PyStringObject;
            return this._PyString_Resize_NoGrow(newStr, newSize);
        }
        
        private int
        _PyString_Resize_NoGrow(IntPtr strPtr, int newSize)
        {
            IntPtr ob_sizePtr = CPyMarshal.Offset(
                strPtr, Marshal.OffsetOf(typeof(PyStringObject), "ob_size"));
            CPyMarshal.WriteInt(ob_sizePtr, newSize);
            IntPtr bufPtr = CPyMarshal.Offset(
                strPtr, Marshal.OffsetOf(typeof(PyStringObject), "ob_sval"));
            IntPtr terminatorPtr = CPyMarshal.Offset(
                bufPtr, newSize);
            CPyMarshal.WriteByte(terminatorPtr, 0);
            return 0;
        }
        
        
        public override int
        _PyString_Resize(IntPtr strPtrPtr, int newSize)
        {
            IntPtr strPtr = CPyMarshal.ReadPtr(strPtrPtr);
            PyStringObject str = (PyStringObject)Marshal.PtrToStructure(strPtr, typeof(PyStringObject));
            if (str.ob_size < newSize)
            {
                return this._PyString_Resize_Grow(strPtrPtr, newSize);
            }
            else
            {
                return this._PyString_Resize_NoGrow(strPtr, newSize);
            }
        }
        
        public override int
        PyString_Size(IntPtr strPtr)
        {
            return CPyMarshal.ReadIntField(strPtr, typeof(PyStringObject), "ob_size");
        }
        
        private IntPtr 
        AllocPyString(int length)
        {
            int size = Marshal.SizeOf(typeof(PyStringObject)) + length;
            IntPtr data = this.allocator.Alloc(size);
            
            PyStringObject s = new PyStringObject();
            s.ob_refcnt = 1;
            s.ob_type = this.PyString_Type;
            s.ob_size = (uint)length;
            s.ob_shash = -1;
            s.ob_sstate = 0;
            Marshal.StructureToPtr(s, data, false);
            
            IntPtr terminator = CPyMarshal.Offset(data, size - 1);
            CPyMarshal.WriteByte(terminator, 0);
        
            return data;
        }
        
        private static char
        CharFromByte(byte b)
        {
            return (char)b;
        }
        
        private static byte
        ByteFromChar(char c)
        {
            return (byte)c;
        }
        
        private string
        StringFromBytes(byte[] bytes)
        {
            char[] chars = Array.ConvertAll<byte, char>(
                bytes, new Converter<byte, char>(CharFromByte));
            return new string(chars);
        }
        
        private IntPtr
        CreatePyStringWithBytes(byte[] bytes)
        {
            IntPtr strPtr = this.AllocPyString(bytes.Length);
            IntPtr bufPtr = CPyMarshal.Offset(
                strPtr, Marshal.OffsetOf(typeof(PyStringObject), "ob_sval"));
            Marshal.Copy(bytes, 0, bufPtr, bytes.Length);
            return strPtr;
        }
        
        private IntPtr
        Store(string str)
        {
            char[] chars = str.ToCharArray();
            byte[] bytes = Array.ConvertAll<char, byte>(
                chars, new Converter<char, byte>(ByteFromChar));
            IntPtr strPtr = this.CreatePyStringWithBytes(bytes);
            this.map.Associate(strPtr, str);
            return strPtr;
        }

        private string
        ReadPyString(IntPtr ptr)
        {
            IntPtr typePtr = CPyMarshal.ReadPtrField(ptr, typeof(PyObject), "ob_type");
            if (PyType_IsSubtype(typePtr, this.PyString_Type) == 0)
            {
                throw new ArgumentTypeException("ReadPyString: Expected a str, or subclass thereof");
            }
            IntPtr buffer = CPyMarshal.Offset(ptr, Marshal.OffsetOf(typeof(PyStringObject), "ob_sval"));
            int length = CPyMarshal.ReadIntField(ptr, typeof(PyStringObject), "ob_size");
            byte[] bytes = new byte[length];
            Marshal.Copy(buffer, bytes, 0, length);
            char[] chars = Array.ConvertAll<byte, char>(
                bytes, new Converter<byte, char>(CharFromByte));
            return new string(chars);
        }
        
        private void
        ActualiseString(IntPtr ptr)
        {
            string str = this.ReadPyString(ptr);
            this.incompleteObjects.Remove(ptr);
            this.map.Associate(ptr, str);
        }

        public IntPtr
        IC_PyString_Str(IntPtr ptr)
        {
            try
            {
                return this.Store(this.ReadPyString(ptr));
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }

        public override IntPtr
        PyString_Repr(IntPtr ptr)
        {
            try
            {
                return this.Store(Builtin.repr(this.scratchContext, this.ReadPyString(ptr)));
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }
    }
}