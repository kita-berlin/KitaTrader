import os


class PyLogger:
    HEADER_AND_SEVERAL_LINES: int = 0
    NO_HEADER: int = 1
    ONE_LINE: int = 2
    SELF_MADE: int = 4
    mode: int

    def __init__(self):
        self.log_stream_writer = None
        self.mode: int = self.HEADER_AND_SEVERAL_LINES
        self.write_header = None

    @property
    def is_open(self):
        return self.log_stream_writer is not None

    def log_open(self, pathName: str, filename: str, append: bool, mode: int):
        self.mode = mode
        folder = os.path.join(os.path.dirname(pathName), os.path.dirname(filename))
        if not os.path.exists(folder):
            os.makedirs(folder)

        new_file = self.make_unique_logfile_name(os.path.join(folder, os.path.basename(filename)))
        ret_val = os.path.exists(new_file)
        try:
            self.log_stream_writer = open(new_file, "a" if append else "w")
        except Exception:
            pass
        return ret_val

    def make_log_path(self):
        return os.path.join(r"C:\Users\HMz\Documents\cAlgo\Logfiles", "Algo.csv")

    def add_text(self, text: str):
        if not self.is_open:
            return
        self.log_stream_writer.write(text)  # type: ignore

    def flush(self):
        if not self.is_open:
            return
        self.log_stream_writer.flush()  # type: ignore

    def close(self, header_line: str = ""):
        if not self.is_open:
            return
        # to_do: Insert headerline at the beginning of the file
        self.log_stream_writer.close()  # type: ignore

    def make_unique_logfile_name(self, path_name: str) -> str:
        """
        while os.path.exists(path_name):
            fn_ex = path_name.split('.')
            split_ex_size = len(fn_ex)
            if split_ex_size < 2:
                return ""

            name = '_'.join(fn_ex[:-1])
            ext = fn_ex[-1]

            fn_num = name.split('_')
            path_name = f"{fn_num[0]}_{int(fn_num[1]) + 1}.{ext}" if len(fn_num) > 1 else f"{name}_1.{ext}"
        """
        return path_name


# end of file
