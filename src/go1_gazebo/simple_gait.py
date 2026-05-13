#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
import math
import time

class SimpleGaitNode(Node):
    def __init__(self):
        super().__init__('simple_gait_node')
        # 1. 声明参数并赋予默认值
        self.declare_parameter('gait_freq', 2.0)
        self.declare_parameter('gait_amplitude', 0.3)
        self.declare_parameter('thigh_offset', 0.8)
        
        self.publisher_ = self.create_publisher(Float64MultiArray, '/leg_controller/commands', 10)
        self.timer = self.create_timer(0.01, self.timer_callback)
        self.start_time = time.time()

    def timer_callback(self):

        # 2. 每次循环实时获取最新的参数值
        freq = self.get_parameter('gait_freq').value
        amplitude = self.get_parameter('gait_amplitude').value
        thigh_offset = self.get_parameter('thigh_offset').value

        t = time.time() - self.start_time
        msg = Float64MultiArray()
        
        # 定义基础站立姿态的关节偏移量 (让狗半蹲站立)
        hip_offset = 0.0      # 髋侧摆角
        thigh_offset = 0.8    # 大腿前摆角 (约45度)
        calf_offset = -1.5    # 小腿后折角 (约-85度)
        
        # 定义运动幅度 (振幅) 和 频率
        amplitude = 0.3
        freq = 2.0 # 频率 2Hz
        
        # 计算前腿和后腿的相位差 (让对角腿同步，这就是 Trot 步态的雏形)
        phase_1 = math.sin(2 * math.pi * freq * t)          # 右前 (FR) 和 左后 (RL)
        phase_2 = math.sin(2 * math.pi * freq * t + math.pi) # 左前 (FL) 和 右后 (RR) (相差半个周期)

        # 按照 jtc.yaml 里定义的顺序打包 12 个关节数据
        # 顺序: FR_hip, FR_thigh, FR_calf, FL_hip, FL_thigh, FL_calf, 
        #       RR_hip, RR_thigh, RR_calf, RL_hip, RL_thigh, RL_calf
        
        msg.data = [
            # FR 右前腿
            hip_offset, 
            thigh_offset + amplitude * phase_1, 
            calf_offset, 
            
            # FL 左前腿
            hip_offset, 
            thigh_offset + amplitude * phase_2, 
            calf_offset, 
            
            # RR 右后腿
            hip_offset, 
            thigh_offset + amplitude * phase_2, 
            calf_offset, 
            
            # RL 左后腿
            hip_offset, 
            thigh_offset + amplitude * phase_1, 
            calf_offset
        ]
        
        self.publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = SimpleGaitNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()