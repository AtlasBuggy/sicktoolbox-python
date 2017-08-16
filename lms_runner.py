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

log_parser = LogParser("logs/2017_Aug_15/22;32;12.log.xz", enabled=simulated, update_rate=0.005)

slam = Slam(map_size_pixels, map_size_meters)
plotter = LivePlotter(2, matplotlib_events=dict(key_press_event=key_press_fn))

slam.subscribe(Feed(slam.lms_tag, sicklms))
slam.subscribe(Subscription(slam.plotter_tag, plotter))
log_parser.subscribe(Subscription(sicklms.name, sicklms))

robot.run(log_parser, sicklms, plotter, slam)
