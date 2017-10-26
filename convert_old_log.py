import re
import os
import glob
import time
import logging
import datetime
import lzma as xz


class LogParser:
    """
    Parse a log file to simulate how the robot behaved that day
    """

    def __init__(self, file_name, directory="", compressed=False):
        # regex string code. Logs follow a certain format. Parse out these pieces of info.
        self.pattern = re.compile(
            r"(((?P<name>[a-zA-Z0-9]*) @ "
            r"(?P<filename>.*\.py):"
            r"(?P<linenumber>[0-9]*)\]\["
            r"(?P<loglevelstr>[A-Z]*)\] "
            r"(?P<year>[0-9]*)-"
            r"(?P<month>[0-9]*)-"
            r"(?P<day>[0-9]*) "
            r"(?P<hour>[0-9]*):"
            r"(?P<minute>[0-9]*):"
            r"(?P<second>[0-9]*),"
            r"(?P<millisecond>[0-9]*): )"
            r"(?P<message>([.\S\s]+?(\n\[))))"
        )

        # info about the log file path
        self.file_name = file_name
        self.directory = directory
        self.full_path = os.path.join(self.directory, self.file_name)

        self.logged_streams = {}
        self.encountered_names = set()

        # current line of the log we're on
        self.line_number = 0
        self.line = ""

        self.prev_time = None

        # decompress the log file
        with open(self.full_path, 'rb') as log_file:
            if compressed:
                self.content = xz.decompress(log_file.read()).decode()
            else:
                self.content = log_file.read().decode()

        # all pieces information in each line
        self.matches = re.finditer(self.pattern, self.content)

        self.lines = []
        self.start_index = 0

        self.run()

    def make_line_info(self):
        return dict(
            name="", filename="", linenumber=0, loglevelstr="", loglevel=0,
            year=0, month=0, day=0, hour=0, minute=0, second=0, millisecond=0, timestamp=0,
            message="", header="", full=""
        )

    def find_start(self):
        for match_num, match in enumerate(self.matches):
            line_info = self.make_line_info()
            self._post_match(line_info, match_num, match)
            if line_info["name"] == "Robot" and \
                            line_info["filename"] == "robot.py" and \
                            line_info["loglevel"] == 10 and \
                            line_info["message"] == "Starting coroutine":
                self.start_index = match_num
                break

    def run(self):
        self.find_start()
        # find all matches in the log

        for match_num, match in enumerate(self.matches):
            line_info = self.make_line_info()
            self._post_match(line_info, match_num, match)

    def _post_match(self, line_info, match_num, match):
        self.line_number = match_num

        for line_key, line_value in match.groupdict().items():
            # convert the matched element to the corresponding line_info's type
            # if line_info["year"] is of type int, convert the match to an int and assign the value to line_info
            line_info[line_key] = type(line_info[line_key])(line_value)

        # a quirk of the way I'm parsing with regex. Move the last character of the message to the beginning and
        # remove trailing newlines
        line = match.group()
        self.line = (line[-1] + line[:-1]).strip("\n")
        line_info["message"] = line_info["message"][:-1].strip("\n")

        # under scrutiny, not sure what this was for
        # if self.prev_time is not None:
        #     self.prev_time = line_info["timestamp"]

        # create a unix timestamp using the date
        current_date = datetime.datetime(
            line_info["year"],
            line_info["month"],
            line_info["day"],
            line_info["hour"],
            line_info["minute"],
            line_info["second"],
            line_info["millisecond"])

        # make timestamp from unix epoch
        line_info["timestamp"] = time.mktime(current_date.timetuple()) + current_date.microsecond / 1e3

        # convert string to logging integer code
        line_info["loglevel"] = logging.getLevelName(line_info["loglevelstr"])

        # notify stream if its name is found in the log
        if line_info["name"] in self.logged_streams:
            stream = self.logged_streams[line_info["name"]]
            stream._receive_log(line_info["loglevel"], line_info["message"], line_info)

        if line_info["name"] not in self.encountered_names:
            self.encountered_names.add(line_info["name"])

        line_info["full"] = match.group(1)
        line_info["full"] = (line_info["full"][-1] + line_info["full"][:-1]).strip("\n")
        line_info["header"] = "[" + match.group(2)

        self.lines.append(line_info)


def convert_log(path):
    log = LogParser(path, compressed=True)

    split = log.full_path.split(os.sep)[1:]
    old_dir = split[:-1]
    old_name = split[-1]
    new_dir = os.path.join("converted", *old_dir)
    new_name = os.path.splitext(old_name)[0]

    log_files = {}
    for name in log.encountered_names:
        log_dir = os.path.join(new_dir, name)
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        log_files[name] = open(os.path.join(log_dir, new_name), 'w')

    for line in log.lines:
        name = line["name"]
        message_text = "[%(name)s @ %(filename)s:%(linenumber)s][%(loglevelstr)s] " \
                       "%(year)s-%(month)s-%(day)s %(hour)s:%(minute)s:%(second)s,%(millisecond)s: %(message)s\n" % line
        log_files[name].write(message_text)

    for log_file in log_files.values():
        log_file.close()


def convert_lms_log(path):
    log = LogParser(path)
    new_path = os.path.splitext(path)[0] + "-new.log"
    new_file = open(new_path, 'w')

    scan_num = ""
    avg_update_hz = ""

    scan_info_header = "scan #"
    info_split = " @ "
    scan_header = "scan: ("

    for line in log.lines:
        message = line["message"]
        if message.startswith(scan_info_header):
            raw_info = message[len(scan_info_header):]
            split_index = raw_info.find(info_split)
            scan_num = raw_info[:split_index]
            avg_update_hz = raw_info[split_index + len(info_split):]

        elif message.startswith(scan_header):
            raw_scan = message[len(scan_header):-1].replace(" ", "")

            new_line = "%sLmsScan(t=%s, n=%s, avg=%s, scan=%s)\n" % (
                line["header"], line["timestamp"], scan_num, avg_update_hz, raw_scan
            )
            new_file.write(new_line)
        elif message.startswith("posted scan"):
            pass
        else:
            new_file.write(line["full"] + "\n")
    new_file.close()

    os.rename(new_path, path)


def convert_all():
    for directory in glob.glob("logs/*"):
        for path in glob.glob(directory + "/*"):
            convert_log(path)
            directory, file_name = path.split(os.sep)[1:]

            new_file_name = os.path.splitext(file_name)[0]
            new_path = os.path.join("converted", directory.split(os.sep)[-1], "LMS200", new_file_name)

            convert_lms_log(new_path)


convert_all()
