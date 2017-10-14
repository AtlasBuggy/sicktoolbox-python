import re
import time
import asyncio
import multiprocessing
from multiprocessing.managers import BaseManager

from atlasbuggy import ThreadedStream, AsyncStream

from .sicktoolbox import SickLMS, units, bauds, measuring_modes, SickIOException


class LMS200(ThreadedStream):
    def __init__(self, address, baud=38400, enabled=True, log_level=None):
        super(LMS200, self).__init__(enabled, log_level)

        self.session_baud = baud

        self.scan_resolution = 0.0
        self.scan_angle = 0.0
        self.measuring_units = None
        self.max_distance = 0.0

        self.num_scans = 0
        self.update_rate_hz = 5.0
        self._sum_update_hz = 0.0
        self._avg_update_hz = multiprocessing.Value('d')

        self.operating_mode = None
        self.measuring_mode = None

        BaseManager.register("SickLMS", SickLMS)
        self.manager = BaseManager()
        self.manager.start()
        self.lms = self.manager.SickLMS(address)

        self.process_exit_event = multiprocessing.Event()
        self.initialized_event = multiprocessing.Event()
        self.process = multiprocessing.Process(target=self.process_fn, args=(self.lms,))
        self.process_queue = multiprocessing.Queue()
        self.process_lock = multiprocessing.Lock()

    def get_config(self):
        self.operating_mode = self.lms.get_operating_mode()
        self.measuring_mode = self.lms.get_measuring_mode()
        self.measuring_units = self.lms.get_measuring_units()
        self.scan_resolution = self.lms.get_scan_resolution()
        self.scan_angle = self.lms.get_scan_angle()

        self.logger.debug("Operating mode: %s" % self.operating_mode)
        self.logger.debug("Measuring mode: %s" % self.measuring_mode)
        self.logger.debug("Measuring units: %s" % self.measuring_units)
        self.logger.debug("Scan resolution: %s" % self.scan_resolution)
        self.logger.debug("Scan angle: %s" % self.scan_angle)
        self.logger.debug("Update rate: %s" % self.update_rate_hz)

        self.max_distance = self.get_max_dist(self.measuring_mode)
        self.logger.debug("Max distance: %s" % self.max_distance)

    def get_max_dist(self, measuring_mode):
        if measuring_mode in (measuring_modes.MODE_8_OR_80_FA_FB_DAZZLE, measuring_modes.MODE_8_OR_80_REFLECTOR,
                              measuring_modes.MODE_8_OR_80_FA_FB_FC):
            return 8.0
        elif measuring_mode in (measuring_modes.MODE_16_REFLECTOR, measuring_modes.MODE_16_FA_FB):
            return 16.0
        elif measuring_mode in (measuring_modes.MODE_32_REFLECTOR, measuring_modes.MODE_32_FA,
                                measuring_modes.MODE_32_IMMEDIATE):
            return 32.0
        else:
            return 0.0

    @property
    def avg_update_hz(self):
        with self._avg_update_hz.get_lock():
            return self._avg_update_hz.value

    def start(self):
        self.initialize()
        self.process.start()

    def initialize(self):
        self.logger.debug("Selected baud: %s" % self.session_baud)

        if self.session_baud == 9600:
            baud = bauds.SICK_BAUD_9600
            self.update_rate_hz = 1.0
        elif self.session_baud == 19200:
            baud = bauds.SICK_BAUD_19200
            self.update_rate_hz = 2.5
        elif self.session_baud == 38400:
            baud = bauds.SICK_BAUD_38400
            self.update_rate_hz = 5.0
        else:
            raise ValueError("Invalid baud: %s" % self.session_baud)

        self.lms.initialize(baud)

        # try:
        # except SickIOException as error:
        #     self.logger.exception(error)
        #     print("something")
        self.get_config()

    def process_fn(self, lms):
        try:
            while not self.process_exit_event.is_set():
                t0 = time.time()
                scan = lms.get_scan()
                self.num_scans += 1
                self.process_queue.put((scan, self.num_scans))
                t1 = time.time()

                self._sum_update_hz += 1 / (t1 - t0)
                with self._avg_update_hz.get_lock():
                    self._avg_update_hz.value = self._sum_update_hz / self.num_scans
                self.logger.info("scan #%s @ %shz" % (self.num_scans, self._avg_update_hz.value))

        except BaseException as error:
            self.logger.debug("Catching exception in lms200 process")
            self.logger.exception(error)
        finally:
            lms.uninitialize()

    def run(self):
        while self.is_running():
            scan, scan_num = self.process_queue.get()
            self.post((scan, scan_num))
            self.logger.debug("posted scan #%s" % scan_num)
            self.logger.debug("scan: %s" % str(scan))

    def stop(self):
        self.process_exit_event.set()


class LmsSimulator(AsyncStream):
    def __init__(self, enabled=True, log_level=None):
        super(LmsSimulator, self).__init__(enabled, log_level, LMS200.__name__)

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

    async def run(self):
        while self.is_running():
            if self.scan is not None:
                await self.post((self.scan, self.num_scans))
                self.scan = None
            await asyncio.sleep(0.01)


    def receive_log(self, log_level, message, line_info):
        flag = "Selected baud: "
        if message.startswith(flag):
            self.session_baud = int(message[len(flag):])

        flag = "Operating mode: "
        if message.startswith(flag):
            self.operating_mode = int(message[len(flag):])

        flag = "Measuring mode: "
        if message.startswith(flag):
            self.measuring_mode = int(message[len(flag):])

        flag = "Measuring units: "
        if message.startswith(flag):
            self.measuring_units = int(message[len(flag):])

        flag = "Scan resolution: "
        if message.startswith(flag):
            self.scan_resolution = float(message[len(flag):])

        flag = "Scan angle: "
        if message.startswith(flag):
            self.scan_angle = float(message[len(flag):])

        flag = "Max distance: "
        if message.startswith(flag):
            self.max_distance = float(message[len(flag):])

        flag = "scan: "
        if message.startswith(flag):
            self.scan = tuple(map(int, message[len(flag) + 1: -1].split(", ")))

        match = re.match(r"scan #([0-9]*) @ ([0-9.-]*)hz", message)
        if match is not None:
            self.num_scans = int(match.group(1))
            self.avg_update_hz = float(match.group(2))
