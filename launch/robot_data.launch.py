# <?xml version="1.0" encoding="UTF-8" ?>
# <launch>
#     <arg name="rviz" default="false" doc="Launch RViz for data visualization or not"/>
#     <arg name="data_sequence" default="00000" doc="Sequence name from Rellis-3D dataset"/>
#     <arg name="pose_step" default="5"/>
#
#     <node name="robot_data" pkg="traversability_estimation" type="robot_data" output="screen">
#         <rosparam subst_value="true">
#             data_sequence: $(arg data_sequence)
#             pose_step: $(arg pose_step)
#             lidar_frame: 'ouster_lidar'
#             camera_frame: 'pylon_camera'
#         </rosparam>
#     </node>
#
#     <!-- RVIZ -->
#     <node if="$(arg rviz)" name="rviz" pkg="rviz" type="rviz"
#           args="-d $(find traversability_estimation)/config/rviz/robot_data.rviz"/>
# </launch>

from launch import LaunchDescription
from launch.actions import GroupAction
from launch.actions import IncludeLaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition, UnlessCondition, LaunchConfigurationEquals
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node
from launch_ros.actions import PushRosNamespace
from launch_ros.actions import SetParameter
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
  return LaunchDescription([
    DeclareLaunchArgument(name='rviz', default_value='false', description='Launch RViz for data visualization or not'),
    DeclareLaunchArgument(name='data_sequence', default_value='00000', description='Sequence name from Rellis-3D dataset'),
    DeclareLaunchArgument(name='pose_step', default_value='1'),
    DeclareLaunchArgument(name='period', default_value='0.05'),
    
    Node(
      package='traversability_estimation', executable='robot_data', output='screen', name='robot_data',
      parameters=[{
        'data_sequence': ['"', LaunchConfiguration('data_sequence'), '"'],
        'pose_step': LaunchConfiguration('pose_step'),
        'lidar_frame': 'ouster_lidar',
        'camera_frame': 'pylon_camera',
        'period': LaunchConfiguration('period'),
      }],
      namespace='robot_data',
    ),

    # RVIZ
    Node(
      condition=IfCondition(LaunchConfiguration('rviz')), name='rviz', package='rviz2', executable='rviz2',
      arguments=['-d', get_package_share_directory('traversability_estimation') + '/config/rviz/robot_data.rviz'],
    ),
  ])