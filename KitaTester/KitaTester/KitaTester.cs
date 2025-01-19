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
    [Robot(AccessRights = AccessRights.FullAccess, TimeZone = "UTC", AddIndicators = true)]
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
        private Bars mMinute1bar;
        private Bars mHour1bar;
        private Bars mHour2bar;
        private Bars mDay1bar;
        //private Semaphore mResultReady2PySemaphore;
        #endregion

        protected override void OnStart()
        {
            if (IsLaunchDebugger)
                Debugger.Launch();

            mMemoryMappedFile = MemoryMappedFile.CreateOrOpen("TaskMemoryMap", 1024);
            mQuoteReady2PySemaphore = new Semaphore(0, 1, "QuoteReady2PySemaphore");
            mQuoteAccFromPySemaphore = new Semaphore(0, 1, "QuoteAccFromPySemaphore");
            mMinute1bar = MarketData.GetBars(TimeFrame.Minute);
            mHour1bar = MarketData.GetBars(TimeFrame.Hour);
            mHour2bar = MarketData.GetBars(TimeFrame.Hour2);
            mDay1bar = MarketData.GetBars(TimeFrame.Daily);
        }

        protected override void OnTick()
        {
            // Step 1: Send a QuoteMessage to Python and wait for a response
            QuoteMessage quoteMessage = new QuoteMessage
            {
                Timestamp = Time.ToNativeMs(),
                Bid = Symbol.Bid,
                Ask = Symbol.Ask,
                Minute1Open = mMinute1bar.Last(1).Open,
                Hour1Open = mHour1bar.Last(1).Open,
                Hour2Open = mHour2bar.Last(1).Open,
                Day1Open = mDay1bar.Last(1).Open,
                Hour1High = mHour1bar.Last(1).High,
                Hour1Low = mHour1bar.Last(1).Low,
                Hour1Close = mHour1bar.Last(1).Close,
                Hour2High = mHour2bar.Last(1).High,
                Hour2Low = mHour2bar.Last(1).Low,
                Hour2Close = mHour2bar.Last(1).Close,
                Day1Timestamp = mDay1bar.Last(1).OpenTime.ToNativeMs(),
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

    public static class Extensions
    {
        public const int HECTONANOSEC_PER_SEC = (10000000);
        static public readonly DateTime TimeInvalid = new DateTime(1970, 1, 1, 0, 0, 0, 0); // needed to convert DateTime and Mt4 datetime
        static public readonly long DateTime2EpocDiff = TimeInvalid.Ticks / HECTONANOSEC_PER_SEC;

        /// <summary>
        /// Get seconds since 1.1.1970 as in MQL
        /// </summary>
        /// <returns>Seconds since 1.1.1970 as in MT4</returns>
        public static long ToNativeSec(this DateTime time)
        {
            return time.Ticks / HECTONANOSEC_PER_SEC - DateTime2EpocDiff;
        }

        /// <summary>
        /// Get seconds since 1.1.1970 as in MQL
        /// </summary>
        /// <returns>Seconds since 1.1.1970 as in MT4</returns>
        public static long ToNativeMs(this DateTime time)
        {
            return (time.Ticks - TimeInvalid.Ticks) / (HECTONANOSEC_PER_SEC / 1000);
        }
    }
}
