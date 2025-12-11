#!/usr/bin/env python3
import rospy
import math
import tf2_ros
import tf2_geometry_msgs
from sensor_msgs.msg import LaserScan
from visualization_msgs.msg import MarkerArray
from geometry_msgs.msg import TransformStamped, PointStamped

# --- Settings ---
SCAN_ANGLE_MIN = -math.pi/2
SCAN_ANGLE_MAX = math.pi/2
SCAN_INC = math.radians(1)
SCAN_MAX = 10.0

obstacles = []  # list of dicts: {'x', 'y', 'radius'}

def markers_callback(msg):
    global obstacles
    obstacles = []
    for m in msg.markers:
        size = max(m.scale.x, m.scale.y) / 2.0  # radius approximation
        obstacles.append({'x': m.pose.position.x,
                          'y': m.pose.position.y,
                          'radius': size})

# --- Compute distance from robot to obstacle along a ray ---
def ray_distance(ray_angle, robot_x, robot_y):
    min_dist = SCAN_MAX
    ray_dx = math.cos(ray_angle)
    ray_dy = math.sin(ray_angle)
    for obs in obstacles:
        dx = obs['x'] - robot_x
        dy = obs['y'] - robot_y
        proj = dx*ray_dx + dy*ray_dy
        if proj > 0:
            perp = abs(dx*ray_dy - dy*ray_dx)
            if perp <= obs['radius']:
                dist = proj - math.sqrt(obs['radius']**2 - perp**2)
                if dist < min_dist:
                    min_dist = dist
    return min_dist

# --- Main Node ---
rospy.init_node("lidar_from_markers_tf")
pub = rospy.Publisher("/scan", LaserScan, queue_size=10)
rospy.Subscriber("/obstacles", MarkerArray, markers_callback)

# TF listener to get robot position dynamically
tf_buffer = tf2_ros.Buffer()
tf_listener = tf2_ros.TransformListener(tf_buffer)

rate = rospy.Rate(10)
angles = [SCAN_ANGLE_MIN + i*SCAN_INC for i in range(int((SCAN_ANGLE_MAX - SCAN_ANGLE_MIN)/SCAN_INC)+1)]

while not rospy.is_shutdown():
    try:
        trans = tf_buffer.lookup_transform('world', 'body', rospy.Time(0), rospy.Duration(1.0))
        robot_x = trans.transform.translation.x
        robot_y = trans.transform.translation.y
        robot_yaw = math.atan2(2*(trans.transform.rotation.w*trans.transform.rotation.z),
                               1-2*(trans.transform.rotation.z**2))
    except:
        rospy.logwarn("TF not found: using previous position")
        continue

    scan = LaserScan()
    scan.header.frame_id = "lidar"
    scan.header.stamp = rospy.Time.now()
    scan.angle_min = SCAN_ANGLE_MIN
    scan.angle_max = SCAN_ANGLE_MAX
    scan.angle_increment = SCAN_INC
    scan.range_min = 0.0
    scan.range_max = SCAN_MAX

    scan.ranges = [ray_distance(robot_yaw + a, robot_x, robot_y) for a in angles]

    pub.publish(scan)
    rate.sleep()
