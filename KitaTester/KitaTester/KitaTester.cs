using System;
using System.Diagnostics;
using System.IO.MemoryMappedFiles;
using System.Runtime.Versioning;
using System.Threading;
using cAlgo.API;
using cAlgo.API.Collections;
using cAlgo.API.Indicators;
using cAlgo.API.Internals;
using Google.Protobuf;

namespace cAlgo.Robots
{
    [SupportedOSPlatform("windows")]
    [Robot(AccessRights = AccessRights.FullAccess, AddIndicators = true)]
    public class KitaTester : Robot
    {
        #region Parameters
        [Parameter("Launch Debugger", Group = "System", DefaultValue = false)]
        public bool IsLaunchDebugger
        {
            get; set;
        }
        #endregion

        #region Members
        private MemoryMappedFile mMemoryMappedFile;
        private Semaphore mQuoteReady2PySemaphore;
        private Semaphore mQuoteAccFromPySemaphore;
        //private Semaphore mResultReady2PySemaphore;
        #endregion

        protected override void OnStart()
        {
            if (IsLaunchDebugger)
                Debugger.Launch();

            mMemoryMappedFile = MemoryMappedFile.CreateOrOpen("TaskMemoryMap", 1024);
            mQuoteReady2PySemaphore = new Semaphore(0, 1, "QuoteReady2PySemaphore");
            mQuoteAccFromPySemaphore = new Semaphore(0, 1, "QuoteAccFromPySemaphore");
            //mResultReady2PySemaphore = new Semaphore(0, 1, "ResultReady2PySemaphore");
        }

        protected override void OnTick()
        {
            // Step 1: Send a QuoteMessage to Python and wait for a response
            QuoteMessage quoteMessage = new QuoteMessage
            {
                Id = 1,
                Timestamp = Time.Subtract(new DateTime(1970, 1, 1)).TotalSeconds,
                Bid = Symbol.Bid,
                Ask = Symbol.Ask
            };

            // Write QuoteMessage to memory-mapped file
            using (var accessor = mMemoryMappedFile.CreateViewStream())
            {
                using (var codedOutput = new CodedOutputStream(accessor))
                {
                    int messageSize = quoteMessage.CalculateSize();
                    accessor.Write(BitConverter.GetBytes(messageSize), 0, 4); // Write size as 4-byte integer
                    quoteMessage.WriteTo(codedOutput);
                    codedOutput.Flush();
                }
            }

            // Signal Python that the QuoteMessage is ready
            mQuoteReady2PySemaphore.Release();

            // wait for acknowledgement from Python
            mQuoteAccFromPySemaphore.WaitOne();

            // Read response message from memory-mapped file
            PythonResponseMessage response;
            using (var accessor = mMemoryMappedFile.CreateViewStream())
            {
                // Read message length
                byte[] lengthBytes = new byte[4];
                accessor.Read(lengthBytes, 0, 4);
                int messageSize = BitConverter.ToInt32(lengthBytes, 0);

                // Read serialized message
                byte[] messageBytes = new byte[messageSize];
                accessor.Read(messageBytes, 0, messageSize);

                // Parse the message
                response = PythonResponseMessage.Parser.ParseFrom(messageBytes);
            }
        }

        protected override void OnStop()
        {
            mMemoryMappedFile?.Dispose();
            mQuoteAccFromPySemaphore?.Dispose();
            //mResultReady2PySemaphore?.Dispose();
        }
    }
}
