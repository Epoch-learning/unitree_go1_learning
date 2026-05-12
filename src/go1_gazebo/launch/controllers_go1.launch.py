from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    # 启动关节状态广播器 (解决 RViz 报错)
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    # 启动腿部力矩控制器
    leg_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["leg_controller", "-c", "/controller_manager"],
        output="screen",
    )

    return LaunchDescription([
        joint_state_broadcaster_spawner,
        leg_controller_spawner
    ])