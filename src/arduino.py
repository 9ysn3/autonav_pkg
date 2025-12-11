#!/usr/bin/env python3
import rospy
import random
import math
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32

class MockArduino:
    def __init__(self):
        rospy.init_node("mock_arduino")

       
        self.sensor_pub = rospy.Publisher("/mock_sensor", Float32, queue_size=10)

        rospy.Subscriber("/cmd_vel", Twist, self.cmd_callback)

        self.rate = rospy.Rate(10)  # 10 Hz
        self.t = 0.0

    def cmd_callback(self, msg):
        rospy.loginfo(f"[MockArduino] recieved cmd_vel: linear={msg.linear.x:.2f}, angular={msg.angular.z:.2f}")

    def run(self):
        while not rospy.is_shutdown():
            sensor_value = 5.0 + math.sin(self.t) + random.uniform(-0.1, 0.1)
            self.sensor_pub.publish(sensor_value)

            rospy.loginfo(f"[MockArduino] publish sensor data : {sensor_value:.2f}")

            self.t += 0.1
            self.rate.sleep()

if __name__ == "__main__":
    try:
        node = MockArduino()
        node.run()
    except rospy.ROSInterruptException:
        pass
