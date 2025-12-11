#!/usr/bin/env python3
import rospy
from nav_msgs.msg import Path, Odometry
from geometry_msgs.msg import PoseStamped

class RobotPathPublisher:
    def __init__(self):
        rospy.init_node('robot_path_node', anonymous=True)

        # Subscriber: Odom data (pose of the robot)
        self.odom_sub = rospy.Subscriber('/odom', Odometry, self.odom_callback)

        # Publisher: Path to visualize
        self.path_pub = rospy.Publisher('/robot_path', Path, queue_size=10)

        # Initialize Path message
        self.path = Path()
        self.path.header.frame_id = "world"  # Must match your TF frame

        rospy.loginfo("Robot Path Publisher started, listening to /odom")

    def odom_callback(self, msg: Odometry):
        # Create a PoseStamped from Odom pose
        pose_stamped = PoseStamped()
        pose_stamped.header.stamp = rospy.Time.now()
        pose_stamped.header.frame_id = "world"  # Consistent frame

        pose_stamped.pose = msg.pose.pose

        # Append to the path
        self.path.header.stamp = rospy.Time.now()
        self.path.poses.append(pose_stamped)

        # Limit path length to avoid performance issues
        if len(self.path.poses) > 1000:
            self.path.poses.pop(0)

        # Publish path
        self.path_pub.publish(self.path)

    def run(self):
        rospy.spin()

if __name__ == '__main__':
    try:
        RobotPathPublisher().run()
    except rospy.ROSInterruptException:
        pass
