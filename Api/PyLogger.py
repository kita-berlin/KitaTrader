import os
from pickle import FALSE


class PyLogger:
    def __init__(self, cbot):
        self.log_stream_writer = None
        self.algo_bot = cbot
        self.mode = None
        self.write_header = None

    @property
    def is_open(self):
        return self.log_stream_writer is not None

    def log_open(self, pathName, filename, append, mode):
        self.mode = mode
        dir_path = os.path.join(os.path.dirname(pathName), os.path.dirname(filename))
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        new_file = self.make_unique_logfile_name(
            os.path.join(dir_path, os.path.basename(filename))
        )
        ret_val = os.path.exists(new_file)
        try:
            self.log_stream_writer = open(new_file, "a" if append else "w")
        except Exception:
            pass
        return ret_val

    def make_log_path(self):
        # terminal_common_data_path = os.path.join(os.environ.get("CALGO_SOURCES"), "..", "LogFiles")
        return os.path.join("Files", "Algo.csv")

    def add_text(self, text):
        if not self.is_open:
            return
        self.log_stream_writer.write(text)

    def flush(self):
        if not self.is_open:
            return
        self.log_stream_writer.flush()

    def close(self, header_line=""):
        if not self.is_open:
            return
        # to_do: Insert headerline at the beginning of the file
        self.log_stream_writer.close()

    def make_unique_logfile_name(self, path_name):
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
