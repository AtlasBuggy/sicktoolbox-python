from atlasbuggy import Robot
from atlasbuggy.subscriptions import *
from atlasbuggy.plotters import LivePlotter

from slam import Slam
from lms200 import LMS200


def key_press_fn(event):
    if event.key == "q":
        plotter.exit()


robot = Robot()

map_size_pixels = 1600
map_size_meters = 50

sicklms = LMS200("/dev/cu.usbserial")
slam = Slam(map_size_pixels, map_size_meters)
plotter = LivePlotter(2, matplotlib_events=dict(key_press_event=key_press_fn))

slam.subscribe(Feed(slam.lms_tag, sicklms))
slam.subscribe(Subscription(slam.plotter_tag, plotter))

robot.run(sicklms, plotter, slam)
