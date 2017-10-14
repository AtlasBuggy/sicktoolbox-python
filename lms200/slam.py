import os
import math
import numpy as np
from PIL import Image
import matplotlib.cm as colormap
from breezyslam.components import Laser
from breezyslam.algorithms import RMHC_SLAM, Deterministic_SLAM

from atlasbuggy import ThreadedStream
from atlasbuggy.subscriptions import *
from atlasbuggy.plotters import RobotPlot, RobotPlotCollection

from .sicktoolbox import units


class OdometryMessage:
    def __init__(self, vx=0.0, vy=0.0, angular_v=0.0):
        self.vx = vx
        self.vy = vy
        self.angular_v = angular_v

    def __str__(self):
        return "vx: %0.4f, vy: %0.4f, ang_v: %0.4f" % (self.vx, self.vy, self.angular_v)


class Slam(ThreadedStream):
    """
    takes a breezyslam laser object and a flag to determine the
    slam algorithms that is used.
    """

    def __init__(self, map_size_pixels, map_size_meters, enabled=True, log_level=None, write_image=False,
                 plot_slam=True, perform_slam=True):
        super(Slam, self).__init__(enabled, log_level)

        self.angles = None
        self.scan_size = 0

        self.point_cloud_plot = RobotPlot("Point cloud", marker='.', linestyle='')

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
        self.enable_slam = perform_slam

        self.slam_plot = RobotPlot("slam")
        self.trajectory_plot = RobotPlot("trajectory")
        self.full_slam_plot = RobotPlotCollection("full_plot", self.slam_plot, self.trajectory_plot,
                                                  window_resizing=False, enabled=plot_slam)

        self.trajectory_arrow = None

        self.plotter_tag = "plotter"
        self.plotter = None
        self.slam_plot_axes = None
        self.require_subscription(self.plotter_tag, Subscription, is_suggestion=True)

        self.lms_tag = "lms"
        self.lms_feed = None
        self.lms200 = None
        self.require_subscription(
            self.lms_tag, Feed,
            required_attributes=("update_rate_hz", "scan_angle", "scan_resolution", "measuring_units", "max_distance")
        )

        self.odometry_tag = "odometry"
        self.odometry_feed = None
        self.require_subscription(self.odometry_tag, Update, is_suggestion=True, required_message_classes=OdometryMessage)

        self.map_service_tag = "map"
        self.add_service(self.map_service_tag, lambda data: data.copy())

        self.prev_t = 0.0

        self.write_image = write_image

    def take(self, subscriptions):
        self.lms200 = subscriptions[self.lms_tag].get_stream()
        self.lms_feed = subscriptions[self.lms_tag].get_feed()

        if self.plotter_tag in subscriptions:
            self.plotter = subscriptions[self.plotter_tag].get_stream()

            self.plotter.add_plots(self.point_cloud_plot, self.full_slam_plot)

            if self.full_slam_plot.enabled:
                self.slam_plot_axes = self.plotter.get_axis(self.full_slam_plot)
                self.slam_plot_axes.set_aspect("auto")
                self.slam_plot_axes.set_autoscale_on(True)
                self.slam_plot_axes.set_xlim([0, self.map_size_pixels])
                self.slam_plot_axes.set_ylim([0, self.map_size_pixels])

                ticks = np.arange(0, self.map_size_pixels + 100, 50)
                labels = [str(self.map_scale * tick) for tick in ticks]
                self.slam_plot_axes.xaxis.set_ticks(ticks)
                self.slam_plot_axes.set_xticklabels(labels)
                self.slam_plot_axes.yaxis.set_ticks(ticks)
                self.slam_plot_axes.set_yticklabels(labels)

                self.slam_plot_axes.set_xlabel('X (mm)')
                self.slam_plot_axes.set_ylabel('Y (mm)')

                self.slam_plot_axes.grid(False)

        if self.odometry_tag in subscriptions:
            self.odometry_feed = self.get_feed(self.odometry_tag)

    def start(self):
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
        # else:
        self.algorithm = RMHC_SLAM(self.laser, self.map_size_pixels, self.map_size_meters)

    def run(self):
        while self.is_running():
            if not self.lms_feed.empty():
                while not self.lms_feed.empty():
                    scan, scan_num = self.lms_feed.get()
                    self.logger.debug("received scan #%s" % scan_num)
                    distances = self.make_distances(scan)

                    point_cloud = self.make_point_cloud(distances)

                    if self.is_subscribed(self.plotter_tag):
                        self.point_cloud_plot.update(point_cloud[:, 0], point_cloud[:, 1])

                    if self.enable_slam:
                        current_time = self.dt()
                        delta_t = current_time - self.prev_t
                        self.prev_t = current_time

                        if self.is_subscribed(self.odometry_tag):
                            if not self.odometry_feed.empty():
                                odometry_message = self.odometry_feed.get()
                                delta_xy_mm = math.sqrt(odometry_message.vx ** 2 + odometry_message.vy ** 2) * 1000 * delta_t
                                delta_theta_degrees = math.degrees(odometry_message.angular_v)
                                velocities = [delta_xy_mm, delta_theta_degrees, delta_t]
                            else:
                                velocities = None

                        else:
                            velocities = [0, 0, delta_t]

                        if velocities is not None:
                            self.slam(distances.tolist(), velocities)

                    self.lms_feed.task_done()

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

        map_img = np.reshape(np.frombuffer(self.mapbytes, dtype=np.uint8),
                             (self.map_size_pixels, self.map_size_pixels))
        self.plotter.draw_image(self.full_slam_plot, map_img, cmap=colormap.gray)

        if self.trajectory_arrow is not None:
            self.trajectory_arrow.remove()
        dx, dy = self.plt_rotate(0, 0, 0.1, theta_degrees)
        if self.full_slam_plot.enabled:
            self.trajectory_arrow = self.slam_plot_axes.arrow(
                x_mm * self.map_scale, y_mm * self.map_scale, dx, dy, width=10
            )
            self.trajectory_plot.append(x_mm * self.map_scale, y_mm * self.map_scale)

        self.post((x_mm * 0.001, y_mm * 0.001, math.radians(theta_degrees)))
        self.post(map_img, self.map_service_tag)

    @staticmethod
    def plt_rotate(x, y, r, deg):
        rad = math.radians(deg)
        c = math.cos(rad)
        s = math.sin(rad)
        dx = r * c
        dy = r * s
        return x + dx, y + dy

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

    def stopped(self):
        if self.write_image:
            todays_folder = os.path.split(self._log_info["directory"])[-1]
            directory = os.path.join("maps", todays_folder)
            file_name = self._log_info["file_name"] + " map"
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
    print('\nSaving image to file %s' % filename)

    output = open(filename, 'wt')

    output.write('P2\n%d %d 255\n' % imgsize)

    wid, hgt = imgsize

    for y in range(hgt):
        for x in range(wid):
            output.write('%d ' % imgbytes[y * wid + x])
        output.write('\n')

    output.close()
