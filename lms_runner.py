from atlasbuggy import Robot, LogParser
from atlasbuggy.subscriptions import *
from atlasbuggy.plotters import LivePlotter

from slam import Slam
from lms200 import LMS200, LmsSimulator

simulated = True


def key_press_fn(event):
    if event.key == "q":
        plotter.exit()


robot = Robot(write=not simulated, log_level=10)

map_size_pixels = 1600
map_size_meters = 50

if simulated:
    sicklms = LmsSimulator()
else:
    sicklms = LMS200("/dev/cu.usbserial")

file_name = "2017_Sep_27/18;13;53.log.xz"
# file_name = "2017_Aug_15/23;30;01.log.xz"
# file_name = "2017_Aug_15/22;32;12.log.xz"
log_parser = LogParser(file_name, "logs", enabled=simulated)

slam = Slam(map_size_pixels, map_size_meters, write_image=True, enabled=True)
plotter = LivePlotter(2, matplotlib_events=dict(key_press_event=key_press_fn))

slam.subscribe(Feed(slam.lms_tag, sicklms))
slam.subscribe(Subscription(slam.plotter_tag, plotter))
log_parser.subscribe(Subscription(sicklms.name, sicklms))

robot.run(log_parser, sicklms, plotter, slam)
