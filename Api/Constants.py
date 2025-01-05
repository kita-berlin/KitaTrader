class Constants:
    # 1 sec = 1000 millisec = 1,000,000 microsec = 1,000,000,000 nanosec = 10,000,000 100-nanosec
    # 1 microsec = 1000 nanosec = 10 100-nanosec
    # 100 nanosec = 0.1 microsec
    # / <summary>
    # / Milliseconds per second.
    # / </summary>
    MILLISEC_PER_SEC: int = 1000

    # / <summary>
    # / Microseconds per second.
    # / </summary>
    MICROSEC_PER_SEC: int = 1000000

    # / <summary>
    # / Nanoseconds per second.
    # / </summary>
    NANOSEC_PER_SEC: int = 1000000000

    # / <summary>
    # / Hectonanoseconds per second.
    # / </summary>
    HECTONANOSEC_PER_SEC: int = 10000000

    # / <summary>
    # / Nanoseconds per millisecond.
    # / </summary>
    NANOSEC_PER_MILLISEC: int = 1000000

    # / <summary>
    # / Nanoseconds per microsecond.
    # / </summary>
    NANOSEC_PER_MICROSEC: int = 1000

    # / <summary>
    # / Hours per day.
    # / </summary>
    HOUR_PER_DAY: int = 24

    # / <summary>
    # / Minutes per hour.
    # / </summary>
    MIN_PER_HOUR: int = 60

    # / <summary>
    # / Minutes per day.
    # / </summary>
    MIN_PER_DAY: int = MIN_PER_HOUR * HOUR_PER_DAY

    # / <summary>
    # / Seconds per minute.
    # / </summary>
    SEC_PER_MINUTE: int = 60

    # / <summary>
    # / Seconds per hour.
    # / </summary>
    SEC_PER_HOUR: int = MIN_PER_HOUR * SEC_PER_MINUTE

    # / <summary>
    # / Seconds per day.
    # / </summary>
    SEC_PER_DAY: int = SEC_PER_HOUR * 24

    # / <summary>
    # / Seconds per day.
    # / </summary>
    SEC_PER_WEEK: int = SEC_PER_DAY * 7

    # / <summary>
    # / MT4 Epoc datetime starts on 1.1.1970 what was a Thursday (WeekOfDay == 4).
    # / Add this offset to get Sunday
    # / </summary>
    EPOC_WEEKDAY_SEC_OFFSET: int = 3 * SEC_PER_DAY


# end of file
