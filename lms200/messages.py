import re

from atlasbuggy import Message


class LmsScan(Message):
    message_regex = r"LmsScan\(t=([\d.]*), n=(\d*), avg=([\d.]*), scan=\((.+)\)\)"

    def __init__(self, timestamp, n, avg_update_hz, scan):
        self.avg_update_hz = avg_update_hz
        self.scan = scan
        super(LmsScan, self).__init__(timestamp, n)

    @classmethod
    def parse(cls, message):
        match = re.match(cls.message_regex, message)
        if match is None:
            return None
        else:
            message_time = float(match.group(1))
            n = int(match.group(2))
            avg_update_rate = float(match.group(3))
            scan = match.group(4)
            scan = tuple(map(int, scan.split(",")))

            return LmsScan(message_time, n, avg_update_rate, scan)

    def __str__(self):
        return "%s(t=%s, n=%s, avg=%s, scan=%s)" % (
            self.__class__.__name__, self.timestamp, self.n, self.avg_update_hz, self.scan)


class OdometryMessage(Message):
    message_regex = r"OdometryMessage\(t=([\d.]*)), n=(\d*), xy=([\d.]*)), th=([\d.]*)), dt=([\d.]*))\)"

<<<<<<< HEAD
    def __init__(self, timestamp=None, n=None, delta_xy_mm=0.0, delta_theta_degrees=0.0, delta_t=0.0):
=======
    def __init__(self, timestamp=None, n=0, delta_xy_mm=0.0, delta_theta_degrees=0.0, delta_t=0.0):
>>>>>>> fce8987e10dea6ad2b805fdbf6817dae31fd61a9
        self.delta_xy_mm = delta_xy_mm
        self.delta_theta_degrees = delta_theta_degrees
        self.delta_t = delta_t

        super(OdometryMessage, self).__init__(timestamp, n)

    @classmethod
    def parse(cls, message):
        match = re.match(cls.message_regex, message)
        if match is None:
            return None
        else:
            message_time = float(match.group(1))
            n = int(match.group(2))
            delta_xy_mm = float(match.group(3))
            delta_theta_degrees = float(match.group(4))
            delta_t = float(match.group(3))

            return OdometryMessage(message_time, n, delta_xy_mm, delta_theta_degrees, delta_t)

    def __str__(self):
        return "%s(t=%s, n=%s, xy=%s, th=%s, dt=%s)" % (
            self.__class__.__name__, self.timestamp, self.n, self.delta_xy_mm, self.delta_theta_degrees, self.delta_t)


class PoseMessage(Message):
    message_regex = r"PoseMessage\(t=([\d.]*)), n=(\d*), x=([\d.]*)), y=([\d.]*)), th=([\d.]*))\)"

    def __init__(self, timestamp, n, x_mm, y_mm, theta_degrees):
        self.x_mm = x_mm
        self.y_mm = y_mm
        self.theta_degrees = theta_degrees

        super(PoseMessage, self).__init__(timestamp, n)

    @classmethod
    def parse(cls, message):
        match = re.match(cls.message_regex, message)
        if match is None:
            return None
        else:
            message_time = float(match.group(1))
            n = int(match.group(2))
            x_mm = float(match.group(3))
            y_mm = float(match.group(4))
            theta_degrees = float(match.group(3))

            return PoseMessage(message_time, n, x_mm, y_mm, theta_degrees)

    def __str__(self):
        return "%s(t=%s, n=%s, x=%s, y=%s, th=%s)" % (
            self.__class__.__name__, self.timestamp, self.n, self.x_mm, self.y_mm, self.theta_degrees)
