#!/usr/bin/env python3
import rospy
import math
import tf
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist, Point, Quaternion

class OdomNode:
    def __init__(self):
        # Initial pose
        self.x = rospy.get_param('~init_x', 5.0)
        self.y = rospy.get_param('~init_y', 5.0)
        self.yaw = rospy.get_param('~init_yaw', -1.5707)

        # Velocities
        self.v = 0.0
        self.w = 0.0

        # Timing
        self.last_time = rospy.Time.now()

        # Publishers and Subscribers
        self.br = tf.TransformBroadcaster()
        self.odom_pub = rospy.Publisher('/odom', Odometry, queue_size=10)
        rospy.Subscriber('/cmd_vel', Twist, self.cmd_vel_cb)

        self.rate = rospy.Rate(30)  # 30 Hz

        rospy.loginfo("Odometry node started at position (%.2f, %.2f, %.2f)" % (self.x, self.y, self.yaw))

    def cmd_vel_cb(self, msg):
        """Callback to update linear and angular velocities from /cmd_vel"""
        self.v = msg.linear.x
        self.w = msg.angular.z

    def update(self):
        while not rospy.is_shutdown():
            now = rospy.Time.now()
            dt = (now - self.last_time).to_sec()
            if dt <= 0.0:
                dt = 1e-6  # Avoid division by zero
            self.last_time = now

            # --- Integrate position ---
            self.x += self.v * math.cos(self.yaw) * dt
            self.y += self.v * math.sin(self.yaw) * dt
            self.yaw += self.w * dt

            # Keep yaw between -pi and pi
            self.yaw = math.atan2(math.sin(self.yaw), math.cos(self.yaw))

            # --- Publish TF ---
            quat = tf.transformations.quaternion_from_euler(0, 0, self.yaw)
            self.br.sendTransform(
                (self.x, self.y, 0.0),
                quat,
                now,
                "body",
                "world"
            )

            # --- Publish Odometry ---
            odom = Odometry()
            odom.header.stamp = now
            odom.header.frame_id = "world"
            odom.child_frame_id = "body"

            # Pose
            odom.pose.pose.position = Point(self.x, self.y, 0.0)
            odom.pose.pose.orientation = Quaternion(*quat)

            # Twist (just echo the commanded velocities)
            odom.twist.twist.linear.x = self.v
            odom.twist.twist.angular.z = self.w

            self.odom_pub.publish(odom)

            self.rate.sleep()

if __name__ == "__main__":
    rospy.init_node('odom_node')
    node = OdomNode()
    try:
        node.update()
    except rospy.ROSInterruptException:
        pass
