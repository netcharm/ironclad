using System;
using System.Threading;


namespace Ironclad
{
    
    public class LockException : Exception
    {
        public LockException(string message): base(message)
        {
        }
    }
    
    public class Lock
    {
        private IntPtr hMutex;
        private int count;
        private int owner;
        
        private const int INFINITE = -1;
        private const int ABANDONED = 0x80;
        private const int TIMEOUT = 0x102;
        
        public Lock()
        {
            this.hMutex = Unmanaged.CreateMutex(IntPtr.Zero, 0, IntPtr.Zero);
            this.count = 0;
        }
        
        ~Lock()
        {
            this.Dispose(false);
        }
        
        public void 
        Dispose()
        {
            this.Dispose(true);
            GC.SuppressFinalize(this);
        }
        
        protected virtual void 
        Dispose(bool disposing)
        {
            while (this.count > 0)
            {
                this.Release();
            }
            Unmanaged.CloseHandle(this.hMutex);
        }
        
    
        public int
        Acquire()
        {
            if (Unmanaged.WaitForSingleObject(this.hMutex, INFINITE) == ABANDONED)
            {
                Console.WriteLine("warning: mutex abandoned\n{0}", System.Environment.StackTrace);
            }
            
            this.owner = Thread.CurrentThread.ManagedThreadId;
            this.count += 1;
            //Console.WriteLine(
            //    "Acquired on thread id {0} (count: {1})", Thread.CurrentThread.ManagedThreadId, this.count);
            return this.count;
        }
        
        public bool
        TryAcquire()
        {
            int result = Unmanaged.WaitForSingleObject(this.hMutex, 0);
            if (result == TIMEOUT)
            {
                return false;
            }
            if (result == ABANDONED)
            {
                Console.WriteLine("warning: mutex abandoned\n{0}", System.Environment.StackTrace);
            }
            
            this.owner = Thread.CurrentThread.ManagedThreadId;
            this.count += 1;
            //Console.WriteLine(
            //    "Acquired on thread id {0} (count: {1})", Thread.CurrentThread.ManagedThreadId, this.count);
            return true;
        }
        
        public bool
        IsAcquired
        {
            get
            {
                return (owner == Thread.CurrentThread.ManagedThreadId) && (count > 0);
            }
        }
        
        public void
        Release()
        {
            if (!this.IsAcquired)
            {
                throw new LockException("you can't release a lock you don't own");
            }
            //Console.WriteLine(
            //    "Releasing on thread id {0} (count: {1})\n", Thread.CurrentThread.ManagedThreadId, this.count);
            this.count -= 1;
            if (this.count == 0)
            {
                this.owner = -1;
            }
            if (Unmanaged.ReleaseMutex(this.hMutex) == 0)
            {
                throw new LockException("ReleaseMutex failed, even though we're pretty certain we do own this lock");
            }
        }
    }
}