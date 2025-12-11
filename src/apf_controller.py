#!/usr/bin/env python3
import rospy
import math
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import tf
from lec11.srv import *

# --- Parameters ---
GOAL_X = None
GOAL_Y = None
SAFE_DISTANCE = 0.8       # Safe distance to start repulsion
MIN_REPULSE_DIST = 0.6   # Minimum distance for repulsion to have effect
K_GOAL = 0.6             # Attractive force strength
K_OBS = 2.7              # Repulsive force strength
GOAL_THRESHOLD = 0.25     # Goal reached if distance < threshold
ANGLE_THRESHOLD = 0.05    # Threshold to stop rotating

# Robot state
robot_x = 0.0
robot_y = 0.0
robot_yaw = 0.0
scan_data = None
goal_reached = True

# Stuck detection
prev_x, prev_y = 0.0, 0.0
stuck_counter = 0
STUCK_LIMIT = 15

# --- Callbacks ---
def scan_callback(msg):
    global scan_data
    scan_data = msg

def odom_callback(msg):
    global robot_x, robot_y, robot_yaw
    robot_x = msg.pose.pose.position.x
    robot_y = msg.pose.pose.position.y
    q = msg.pose.pose.orientation
    (_, _, yaw) = tf.transformations.euler_from_quaternion([q.x, q.y, q.z, q.w])
    robot_yaw = yaw

def set_goal(req):
    global GOAL_X, GOAL_Y, goal_reached
    GOAL_X = req.x
    GOAL_Y = req.y
    goal_reached = False
    rospy.loginfo(f"New goal received: ({GOAL_X:.2f}, {GOAL_Y:.2f})")
    res = goalResponse()
    res.success = 1
    res.message = "Goal received successfully"
    return res

# --- Compute motion vector ---
def compute_motion_vector():
    global scan_data, robot_x, robot_y, robot_yaw
    if scan_data is None or GOAL_X is None or GOAL_Y is None:
        return 0.0, 0.0

    # Attractive force
    dx = GOAL_X - robot_x
    dy = GOAL_Y - robot_y
    dist_to_goal = math.hypot(dx, dy)
    goal_angle = math.atan2(dy, dx)
    force_x = K_GOAL * dist_to_goal * math.cos(goal_angle)
    force_y = K_GOAL * dist_to_goal * math.sin(goal_angle)

    # Repulsive force only for close obstacles
    for i, r in enumerate(scan_data.ranges):
        if scan_data.range_min < r < SAFE_DISTANCE:
            if r > MIN_REPULSE_DIST:
                continue  # ignore distant obstacles
            angle = robot_yaw + scan_data.angle_min + i * scan_data.angle_increment
            repulse = K_OBS * (1.0 / r - 1.0 / SAFE_DISTANCE) / (r*r)
            repulse = min(repulse, 2.0)
            force_x -= repulse * math.cos(angle)
            force_y -= repulse * math.sin(angle)

    move_angle = math.atan2(force_y, force_x)
    magnitude = min(math.hypot(force_x, force_y), 1.0)
    return move_angle, magnitude

# --- Main control loop ---
def main():
    global goal_reached, prev_x, prev_y, stuck_counter
    rospy.init_node("apf_controller")

    rospy.Subscriber("/scan", LaserScan, scan_callback)
    rospy.Subscriber("/odom", Odometry, odom_callback)
    rospy.Service('/set_goal', goal, set_goal)
    cmd_pub = rospy.Publisher("/cmd_vel", Twist, queue_size=10)

    rate = rospy.Rate(20)  # Faster control loop

    while not rospy.is_shutdown():
        cmd = Twist()

        if GOAL_X is None or GOAL_Y is None or goal_reached:
            cmd_pub.publish(cmd)
            rate.sleep()
            continue

        # Distance to goal
        dist_to_goal = math.hypot(GOAL_X - robot_x, GOAL_Y - robot_y)

        # Check if goal is effectively reached or blocked
        min_scan = min([r for r in scan_data.ranges if not math.isinf(r)] + [float('inf')])
        if dist_to_goal < GOAL_THRESHOLD or (dist_to_goal < SAFE_DISTANCE/2 and min_scan < 0.2):
            rospy.loginfo("Goal reached or too close to obstacle, stopping at safe distance.")
            cmd_pub.publish(Twist())
            goal_reached = True
            stuck_counter = 0
            continue

        # Compute motion
        move_angle, force_mag = compute_motion_vector()
        angle_diff = math.atan2(math.sin(move_angle - robot_yaw), math.cos(move_angle - robot_yaw))

        # Linear speed proportional to force
        cmd.linear.x = 0.5 * force_mag

        # Angular speed (smooth)
        cmd.angular.z = 1.5 * math.tanh(angle_diff)

        # Stuck detection
        if math.hypot(robot_x - prev_x, robot_y - prev_y) < 0.05:
            stuck_counter += 1
        else:
            stuck_counter = 0
        prev_x, prev_y = robot_x, robot_y

        if stuck_counter > STUCK_LIMIT:
            rospy.logwarn("Robot stuck, rotating to recover...")
            cmd.linear.x = 0.0
            cmd.angular.z = 1.0  # Rotate in place
            stuck_counter = 0

        cmd_pub.publish(cmd)
        rate.sleep()

if __name__ == "__main__":
    try:
        main()
    except rospy.ROSInterruptException:
        pass
