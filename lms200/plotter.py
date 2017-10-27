import asyncio
import math
import numpy as np

from atlasbuggy import Node

class LMSPlotter(Node):
    def __init__(self):
        super(LMSPlotter, self).__init__()

        self.lms_tag = 'lms'
        self.lms = None
        self.lms_queue = None
        self.lms_sub = self.define_subscription(self.lms_tag)

        self.plotter_tag = 'plotter'
        self.plotter = None
        self.plotter_sub = self.define_subscription(self.plotter_tag)

        self.angles = None

    def take(self):
        self.lms = self.lms_sub.get_producer()
        self.lms_queue = self.lms_sub.get_queue()
        self.plotter = self.plotter_sub.get_producer()

    async def setup(self):
        self.plotter.add_plot("LMS200")

    async def loop(self):
        while True:
            if self.lms_queue.empty():
                await asyncio.sleep(0.0)
                continue

            lms_msg = await self.lms_queue.get()
            x, y = self.get_point_cloud(lms_msg.scan)

            self.plotter.plot("LMS200", x, y)

            await asyncio.sleep(0.0)

    def get_point_cloud(self, scan):
        x = []
        y = []
        num_points = len(scan)
        for i, r in enumerate(scan):
            if r > self.lms.max_distance * 1000:
                continue
            angle = i * ((2*math.pi)/num_points)
            x.append(r * np.cos(angle))
            y.append(r * np.sin(angle))

        return x, y

    def make_angles(self):
        """Create angles list in the correct format and units (radians)"""

        scan_angle_radians = math.radians(self.lms.scan_angle)
        resolution_radians = math.radians(self.lms.scan_resolution)

        self.angles = np.arange(0, scan_angle_radians + resolution_radians, resolution_radians)

    def make_distances(self, scan):
        """Convert the current scan into the correct format and units (meters)"""
        distances = np.array(scan, dtype=np.float32)

        if self.lms.measuring_units == units.CM:
            distances *= 10

        # self.distances = np.ma.masked_array(self.distances, self.distances > self.max_distance)
        distances[distances > self.max_distance_mm] = 1

        return distances

    def make_point_cloud(self, distances):
        """Convert distance and angle lists into a 2D point cloud using numpy operations"""
        return np.vstack(
            [distances * np.cos(self.angles), distances * np.sin(self.angles)]).T
