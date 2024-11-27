import locale


class ConvertUtils:
    # s_us_culture = locale.setlocale(locale.LC_NUMERIC, 'en_US.UTF-8')

    @staticmethod
    def double_to_string(value: float, digits: int):
        if value == float("inf") or value != value:
            return "NaN"
        format_str = "{:." + str(digits) + "f}"
        return format_str.format(value)

    @staticmethod
    def integer_to_string(n: int):
        return str(n)

    @staticmethod
    def string_to_double(s: str):
        try:
            return locale.atof(s)
        except ValueError:
            return 0

    @staticmethod
    def string_to_integer(s: str):
        try:
            return int(s)
        except ValueError:
            return 0


# end of file