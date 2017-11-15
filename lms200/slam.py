import os
import time
import math
import asyncio
import numpy as np
from PIL import Image
from breezyslam.components import Laser
from breezyslam.algorithms import RMHC_SLAM, Deterministic_SLAM

from atlasbuggy import Node

from .messages import LmsScan, OdometryMessage, PoseMessage

from .sicktoolbox import units


class Slam(Node):
    """
    takes a breezyslam laser object and a flag to determine the
    slam algorithms that is used.
    """

    def __init__(self, map_size_pixels, map_size_meters, enabled=True, log_level=None, write_image=False):
        super(Slam, self).__init__(enabled, log_level)

        self.angles = None
        self.scan_size = 0

        self.scan_size = None
        self.scan_rate_hz = None
        self.detection_angle_degrees = None
        self.distance_no_detection_mm = None
        self.max_distance_mm = None

        self.map_size_pixels = map_size_pixels
        self.map_size_meters = map_size_meters
        self.map_scale = self.map_size_meters / self.map_size_pixels

        self.trajectory = []
        self.mapbytes = bytearray(self.map_size_pixels * self.map_size_pixels)

        self.laser = None
        self.algorithm = None

        self.lms_tag = "lms"
        self.lms_queue = None
        self.lms200 = None
        self.lms200_sub = self.define_subscription(
            self.lms_tag, message_type=LmsScan,
            required_attributes=("update_rate_hz", "scan_angle", "scan_resolution", "measuring_units", "max_distance")
        )

        self.odometry_tag = "odometry"
        self.odometry_queue = None
        self.odometry_sub = self.define_subscription(self.odometry_tag, is_required=False, message_type=OdometryMessage)

        self.prev_t = None

        self.write_image = write_image

        self.initialized = False

    def take(self):
        self.lms200 = self.lms200_sub.get_producer()
        self.lms_queue = self.lms200_sub.get_queue()

        if self.is_subscribed(self.odometry_tag):
            self.odometry_queue = self.odometry_sub.get_queue()

    def initialize(self):
        if self.initialized:
            return
        self.initialized = True
        self.make_angles()

        self.scan_size = len(self.angles)
        self.scan_rate_hz = self.lms200.update_rate_hz
        self.detection_angle_degrees = self.lms200.scan_angle
        self.distance_no_detection_mm = 1.0
        self.max_distance_mm = self.lms200.max_distance * 1000

        self.laser = Laser(
            self.scan_size, self.scan_rate_hz,
            self.detection_angle_degrees, self.distance_no_detection_mm
        )
        # if self.is_subscribed(self.odometry_tag):
        #     self.algorithm = Deterministic_SLAM(self.laser, self.map_size_pixels, self.map_size_meters)
        #     self.logger.info("Using deterministic SLAM. Odometry provided.")
        # else:
        self.algorithm = RMHC_SLAM(self.laser, self.map_size_pixels, self.map_size_meters)
            # self.logger.warning("Using RMHC SLAM!! Odometry not provided.")

        self.logger.info("SLAM initialized! %s" % self.laser)

    async def loop(self):
        pose_counter = 0
        distances = None
        velocities = [0, 0, 0]
        current_time = 0

        while True:
            # print(self.lms_queue.empty(), self.odometry_queue.empty())
            if not self.lms_queue.empty():
                self.initialize()
                while not self.lms_queue.empty():
                    scan_message = await self.lms_queue.get()
                    distances = self.make_distances(scan_message.scan)

                    current_time = scan_message.timestamp
                self.log_to_buffer(time.time(), scan_message)

            if self.is_subscribed(self.odometry_tag):
                if not self.odometry_queue.empty():
                    while not self.odometry_queue.empty():
                        odometry_message = await self.odometry_queue.get()
                        velocities = [odometry_message.delta_xy_mm, odometry_message.delta_theta_degrees,
                                          odometry_message.delta_t]
                    self.log_to_buffer(time.time(), odometry_message)

            else:
                if self.prev_t is None:
                    self.prev_t = current_time
                    continue
                velocities = [0, 0, current_time - self.prev_t]
                self.prev_t = current_time

            if distances is not None:
                x_mm, y_mm, theta_degrees = self.slam(distances.tolist(), velocities)
                pose_message = PoseMessage(time.time(), pose_counter, x_mm, y_mm, theta_degrees)
                self.log_to_buffer(time.time(), pose_message)
                await self.broadcast(pose_message)
                pose_counter += 1

            await asyncio.sleep(0.01)

    def make_angles(self):
        """Create angles list in the correct format and units (radians)"""

        scan_angle_radians = math.radians(self.lms200.scan_angle)
        resolution_radians = math.radians(self.lms200.scan_resolution)

        self.angles = np.arange(0, scan_angle_radians + resolution_radians, resolution_radians)

    def make_distances(self, scan):
        """Convert the current scan into the correct format and units (meters)"""
        distances = np.array(scan, dtype=np.float32)

        if self.lms200.measuring_units == units.CM:
            distances *= 10

        # self.distances = np.ma.masked_array(self.distances, self.distances > self.max_distance)
        distances[distances > self.max_distance_mm] = 1

        return distances

    def make_point_cloud(self, distances):
        """Convert distance and angle lists into a 2D point cloud using numpy operations"""
        return np.vstack(
            [distances * np.cos(self.angles), distances * np.sin(self.angles)]).T

    def slam(self, distances, velocity):
        self.algorithm.update(distances, velocity)

        x_mm, y_mm, theta_degrees = self.algorithm.getpos()
        self.trajectory.append((x_mm, y_mm))

        self.algorithm.getmap(self.mapbytes)

        # map_img = np.reshape(np.frombuffer(self.mapbytes, dtype=np.uint8),
        #                      (self.map_size_pixels, self.map_size_pixels))

        return x_mm, y_mm, theta_degrees

    def make_image(self, image_name, image_format="pgm"):
        if self.algorithm is not None:
            self.algorithm.getmap(self.mapbytes)
            for coords in self.trajectory:
                x_mm, y_mm = coords

                x_pix = self.mm2pix(x_mm)
                y_pix = self.mm2pix(y_mm)

                self.mapbytes[y_pix * self.map_size_pixels + x_pix] = 0

            if image_format == "pgm":
                pgm_save(image_name + "." + image_format, self.mapbytes,
                         (self.map_size_pixels, self.map_size_pixels))
            else:
                image = Image.frombuffer('L', (self.map_size_pixels, self.map_size_pixels), self.mapbytes, 'raw', 'L',
                                         0, 1)
                image.save(image_name + "." + image_format)

    def get_pos(self):
        return self.algorithm.getpos()

    def mm2pix(self, mm):
        return int(mm / (self.map_size_meters * 1000 / self.map_size_pixels))

    async def teardown(self):
        if self.write_image:
            todays_folder = self.log_directory.split(os.sep)[1:]
            directory = os.path.join("maps", *todays_folder)
            file_name = self.log_file_name + " map"
            if not os.path.isdir(directory):
                os.makedirs(directory)

            self.make_image(os.path.join(directory, file_name))


def pgm_load(filename):
    print('Loading image from file %s...' % filename)

    fd = open(filename, 'rt')

    # Skip constant header
    fd.readline()

    # Grab image size (assume square)
    imgsize = [int(tok) for tok in fd.readline().split()]

    # Start with empty list
    imglist = []

    # Read lines and append them to list until done
    while True:

        line = fd.readline()

        if len(line) == 0:
            break

        imglist.extend([int(tok) for tok in line.split()])

    fd.close()

    # Convert list into bytes
    imgbytes = bytearray(imglist)

    return imgbytes, imgsize


def pgm_save(filename, imgbytes, imgsize):
    print('\nSaving image to file %s...' % filename)

    output = open(filename, 'wt')

    output.write('P2\n%d %d 255\n' % imgsize)

    wid, hgt = imgsize

    for y in range(hgt):
        for x in range(wid):
            output.write('%d ' % imgbytes[y * wid + x])
        output.write('\n')

    output.close()
    print("done!")
