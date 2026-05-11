import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, AppendEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node

def generate_launch_description():
    # 获取包路径
    pkg_go1_gazebo = get_package_share_directory('go1_gazebo')
    pkg_go1_description = get_package_share_directory('go1_description')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    # 1. 配置新版环境变量：让 Gazebo Harmonic 能找到 meshes 模型
    # Harmonic 使用 GZ_SIM_RESOURCE_PATH 代替老版的 GAZEBO_MODEL_PATH
    set_env_vars_resources = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH',
        os.path.join(pkg_go1_description, '..') # 指向工作区的 install 目录
    )

    # 2. 启动 Gazebo Harmonic
    world_file_name = LaunchConfiguration('world_file_name', default='empty.sdf') # 注意：Harmonic 的世界文件后缀通常是 sdf
    world_path = PathJoinSubstitution([pkg_go1_gazebo, 'worlds', world_file_name])

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': ['-r -v4 ', world_path]}.items() # -r 自动运行, -v4 输出详细日志
    )

    # 3. 启动机器狗可视化与状态发布 (复用我们之前改好的包)
    visualize_robot = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(pkg_go1_description, 'launch', 'go1_visualize.launch.py')
        ]),
        launch_arguments={
            'use_joint_state_publisher': 'False', # 交给仿真器发状态
            'use_sim_time': 'True'
        }.items(),
    )

    # 4. 在 Gazebo 中生成机器狗 (替代老版的 spawn_entity.py)
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'GO1',
            '-topic', 'robot_description', # 从刚刚启动的 visualize 节点获取 URDF
            '-x', '0.0', '-y', '0.0', '-z', '0.6',
        ],
        output='screen'
    )

    # 5. 关键：ROS 2 和 Gazebo Harmonic 之间的桥接 (Bridge)
    # 没有这个，ROS 2 节点将无法获取仿真的时钟，导致 tf 报错
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
        ],
        output='screen'
    )

    # 6. 加载底层控制器 (复用你发来的第三个文件)
    launch_ros2_control = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(pkg_go1_gazebo, 'launch', 'controllers_go1.launch.py')
        ])
    )

    return LaunchDescription([
        set_env_vars_resources,
        gz_sim,
        visualize_robot,
        spawn_robot,
        bridge,
        
        # 暂时先不加载控制器，等模型能成功掉进世界里再打开下面这行
        # launch_ros2_control 
    ])