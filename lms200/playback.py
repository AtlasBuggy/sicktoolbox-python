import asyncio

from atlasbuggy.log.playback import PlaybackNode

from .messages import LmsScan


class LmsPlayback(PlaybackNode):
    def __init__(self, file_name, directory=None, enabled=True, log_level=None):
        super(LmsPlayback, self).__init__(file_name, directory=directory, enabled=enabled)

        self.session_baud = None

        self.scan_resolution = 0.0
        self.scan_angle = 0.0
        self.measuring_units = None
        self.max_distance = 0.0

        self.num_scans = 0
        self.update_rate_hz = 5.0
        self.avg_update_hz = None

        self.operating_mode = None
        self.measuring_mode = None

        self.scan = None

        self.parse_flags = {
            "Selected baud: ": (int, "session_baud"),
            "Operating mode: ": (int, "operating_mode"),
            "Measuring mode: ": (int, "measuring_mode"),
            "Measuring units: ": (int, "measuring_units"),
            "Scan resolution: ": (float, "scan_resolution"),
            "Scan angle: ": (float, "scan_angle"),
            "Max distance: ": (float, "max_distance"),
        }

    async def parse(self, line):
        message = line.message

        flag_parsed = False
        for flag, (value_type, variable_name) in self.parse_flags.items():
            if message.startswith(flag):
                self.__dict__[variable_name] = value_type(message[len(flag):])
                flag_parsed = True

        if not flag_parsed:
            lms_message = LmsScan.parse(message)
            if lms_message is not None:
                await self.broadcast(lms_message)
            else:
                self.logger.info("message failed to parse: %s" % message)
        await asyncio.sleep(0.0)
