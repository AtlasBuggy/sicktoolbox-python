import argparse

from atlasbuggy import Orchestrator, run

from lms200 import Slam, LMS200, LmsPlayback

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--play", help="run in playback mode", action="store_true")
args = parser.parse_args()

playback = args.play

map_size_pixels = 1600
map_size_meters = 50

# file_name = "2017_Sep_27/LMS200/18;13;53.log"
# file_name = "2017_Aug_27/LMS200/12;14;05.log"
# file_name = "2017_Sep_16/LMS200/12;17;56.log"
file_name = "2017_Sep_16/LMS200/13;28;47.log"

slam = Slam(map_size_pixels, map_size_meters, write_image=True, enabled=True)


class PlaybackOrchestrator(Orchestrator):
    def __init__(self, event_loop):
        super(PlaybackOrchestrator, self).__init__(event_loop)

        sicklms = LmsPlayback(file_name, "converted")
        self.add_nodes(sicklms, slam)
        self.subscribe(sicklms, slam, slam.lms_tag)


class LiveOrchestrator(Orchestrator):
    def __init__(self, event_loop):
        super(LiveOrchestrator, self).__init__(event_loop)

        sicklms = LMS200(
            # "/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller-if00-port0"
            "/dev/cu.usbserial"
        )
        self.add_nodes(sicklms, slam)
        self.subscribe(sicklms, slam, slam.lms_tag)


if playback:
    run(PlaybackOrchestrator)
else:
    run(LiveOrchestrator)
