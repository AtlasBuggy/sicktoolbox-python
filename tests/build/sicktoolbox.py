import time
from lms200 import LMS200, Bauds

sicklms = LMS200("/dev/cu.usbserial")
try:
    sicklms.initialize(Bauds.SICK_BAUD_38400)

    scan = sicklms.get_scan()
    print(scan)
    while True:
        t0 = time.time()
        scan = sicklms.get_scan()
        t1 = time.time()
        print(1 / (t1 - t0), len(scan))
except BaseException as error:
    raise
finally:
    sicklms.uninitialize()
