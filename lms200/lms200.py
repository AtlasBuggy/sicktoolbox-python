import time
import asyncio
import multiprocessing
from multiprocessing.managers import BaseManager

from atlasbuggy.device import Generic

from .sicktoolbox import SickLMS, units, bauds, measuring_modes, SickIOException
from .messages import LmsScan


class LMS200(Generic):
    def __init__(self, address, baud=38400, enabled=True):
        super(LMS200, self).__init__(enabled)

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

    async def setup(self):
        self.initialize()
        self.device_process.start()
        time.sleep(0.5)  # wait for device to warm up

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

        try:
            self.lms.initialize(baud)
        except:
            self.stop_device()
            raise

        self.get_config()

    def poll_device(self):
        self.logger.info("polling device")

        while self.device_active():
            t0 = time.time()
            scan = self.lms.get_scan()
            self.num_scans += 1
            self.device_read_queue.put((t0, scan, self.num_scans))
            t1 = time.time()

            self._sum_update_hz += 1 / (t1 - t0)
            with self._avg_update_hz.get_lock():
                self._avg_update_hz.value = self._sum_update_hz / self.num_scans

    async def loop(self):
        t0 = time.time()
        prev_scan_num = 0
        acquisition_rate = 3
        start_time = time.time()

        while self.device_active():
            if not self.empty():
                timestamp, scan, scan_num = self.read()

                message = LmsScan(timestamp, scan_num, self.avg_update_hz, scan)
                self.log_to_buffer(timestamp, message)

                t1 = time.time()
                if (t1 - t0) > acquisition_rate:
                    self.logger.info("received %s scan in %s seconds. %s received in total (avg=%0.1f scans/sec)" % (
                        scan_num - prev_scan_num, acquisition_rate, scan_num, scan_num / (t1 - start_time)
                    ))
                    t0 = time.time()

                await self.broadcast(message)
            else:
                await asyncio.sleep(0.001)
        self.logger.info("Device no longer active. Shutting down.")

    async def teardown(self):
        self.device_exit_event.set()
        await asyncio.sleep(0.01)  # wait for device to exit
        self.lms.uninitialize()
