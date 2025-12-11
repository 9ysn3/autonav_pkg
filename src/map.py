#!/usr/bin/env python3
import rospy
import math
import numpy as np
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import OccupancyGrid
from nav_msgs.msg import Odometry

class MapBuilder:
    def __init__(self):
        rospy.init_node("map_builder")

        # Map parameters
        self.resolution = 0.1     # meters/cell
        self.size_x = 100         # number of cells in x
        self.size_y = 100         # number of cells in y
        self.origin_x = -5.0      # map origin (meters)
        self.origin_y = -5.0

        # Robot state
        self.robot_x = 0.0
        self.robot_y = 0.0
        self.robot_yaw = 0.0

        # Initialize map (unknown = -1)
        self.grid = -1 * np.ones((self.size_y, self.size_x), dtype=np.int8)

        # Publishers & Subscribers
        self.map_pub = rospy.Publisher("/map", OccupancyGrid, queue_size=10, latch=True)
        rospy.Subscriber("/scan", LaserScan, self.scan_cb)
        rospy.Subscriber("/odom", Odometry, self.odom_cb)

        rospy.loginfo("Map builder started.")
        rospy.spin()

    def odom_cb(self, msg):
        # Robot position from odometry
        self.robot_x = msg.pose.pose.position.x
        self.robot_y = msg.pose.pose.position.y

        # Extract yaw from quaternion
        self.robot_yaw = msg.pose.pose.orientation.z

    def scan_cb(self, scan):
    #	self.grid = -1 * np.ones((self.size_y, self.size_x), dtype=np.int8)
        # Update map with lidar readings
        self.grid = -1 * np.ones((self.size_y, self.size_x), dtype=np.int8)
        for i, r in enumerate(scan.ranges):
            if scan.range_min < r < scan.range_max:
                angle = self.robot_yaw + scan.angle_min + i * scan.angle_increment
                ox = self.robot_x + r * math.cos(angle)
                oy = self.robot_y + r * math.sin(angle)

                # Convert world coords → map indices
                mx = int((ox - self.origin_x) / self.resolution)
                my = int((oy - self.origin_y) / self.resolution)

                if 0 <= mx < self.size_x and 0 <= my < self.size_y:
                    self.grid[my, mx] = 100   # occupied

        self.publish_map()

    def publish_map(self):
        grid_msg = OccupancyGrid()
        grid_msg.header.stamp = rospy.Time.now()
        grid_msg.header.frame_id = "world"

        grid_msg.info.resolution = self.resolution
        grid_msg.info.width = self.size_x
        grid_msg.info.height = self.size_y
        grid_msg.info.origin.position.x = self.origin_x
        grid_msg.info.origin.position.y = self.origin_y
        grid_msg.info.origin.orientation.w = 1.0

        # Flatten 2D numpy array into 1D list
        grid_msg.data = self.grid.flatten().tolist()

        self.map_pub.publish(grid_msg)

if __name__ == "__main__":
    try:
        MapBuilder()
    except rospy.ROSInterruptException:
        pass
