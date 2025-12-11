#!/usr/bin/env python3
import rospy
from visualization_msgs.msg import Marker, MarkerArray

rospy.init_node("complex_obstacles_node")
pub = rospy.Publisher("/obstacles", MarkerArray, queue_size=10)

marker_array = MarkerArray()

# Helper function لعمل Marker
def create_marker(marker_id, type_, x, y, z, sx, sy, sz, r, g, b):
    marker = Marker()
    marker.header.frame_id = "world"
    marker.type = type_
    marker.id = marker_id
    marker.pose.position.x = x
    marker.pose.position.y = y
    marker.pose.position.z = z
    marker.scale.x = sx
    marker.scale.y = sy
    marker.scale.z = sz
    marker.color.r = r
    marker.color.g = g
    marker.color.b = b
    marker.color.a = 1.0
    return marker

# === walls ===
walls = [
    # x, y, z, sx, sy, sz
    (-2, 0, 0.5, 0.1, 3.5, 1),  # طول 6 على y
    (1, -4, 0.5, 4, 0.1, 1), # طول 6 على x
    (4, -2, 0.5, 2, 0.1, 1),
    (3, 3, 0.5, 0.1, 2, 1)     # طول 4 على y
]

for idx, (x, y, z, sx, sy, sz) in enumerate(walls):
    marker_array.markers.append(create_marker(idx, Marker.CUBE, x, y, z, sx, sy, sz, 0.6,0.6,0.6))

# === cubes ===
cubes = [
    # x, y, z, sx, sy, sz
    (1.5, 1, 0.25, 0.5, 0.5, 0.5),
    (1.5, 2, 0.25, 0.5, 0.5, 0.5),
    (-1, 0, 0.25, 0.5, 0.5, 0.5),
    (4, -1, 0.25, 0.5, 0.5, 0.5),
    (-2.3, -2, 0.25, 0.5, 0.5, 0.5),
    (2, 0, 0.25, 0.5, 0.5, 0.5),
    (-2, 4, 0.25, 0.5, 0.5, 0.5),
    (2, 4, 0.25, 0.5, 0.5, 0.5)
]

for idx, (x, y, z, sx, sy, sz) in enumerate(cubes, start=10):
    marker_array.markers.append(create_marker(idx, Marker.CUBE, x, y, z, sx, sy, sz, 1.0,0.0,0.0))

# === cylinders ===
cylinders = [
    # x, y, z, sx, sy, sz
    (-1.5, -1, 0.25, 0.5, 0.5, 0.5),
    (1.5, 2, 0.25, 0.5, 0.5, 0.5),
    (3, 1, 0.25, 0.5, 0.5, 0.5),
    (1, -2, 0.25, 0.5, 0.5, 0.5)
]

for idx, (x, y, z, sx, sy, sz) in enumerate(cylinders, start=20):
    marker_array.markers.append(create_marker(idx, Marker.CYLINDER, x, y, z, sx, sy, sz, 0.0,0.0,1.0))

# نشر العوائق بشكل مستمر
rate = rospy.Rate(1)
while not rospy.is_shutdown():
    pub.publish(marker_array)
    rate.sleep()
