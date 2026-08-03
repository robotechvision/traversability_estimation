# <?xml version="1.0" encoding="UTF-8" ?>
# <launch>
#     <arg name="device" default="cuda" doc="Device to run tensor operations on: cpu or cuda"/>
#     <arg name="input" default="points" doc="Input point cloud for segmentation"/>
#     <arg name="max_age" default="0.5"/>
#     <arg name="weights" default="student_kitti_traversablity_f0_0_time_ema.pt"/>
#     <arg name="rviz" default="false"/>

#     <param name="use_sim_time" value="true"/>

#     <group if="0">
#         <include file="$(find depth_correction)/launch/robot_data.launch">
#             <arg name="dataset" value="semantic_kitti/00"/>
#             <arg name="cloud" value="points"/>
#             <arg name="rviz" value="false"/>
#         </include>
#     </group>

#     <group if="1">
#         <arg name="bag" default="$(dirname)/../data/bags/traversability/husky/husky_2022-09-23-12-38-31.bag"/>
#         <arg name="params" default="$(eval bag.split()[0] + '.params')"/>
#         <rosparam command="load" file="$(arg params)"/>
#         <node name="rosbag_play" pkg="rosbag" type="play"
#               args="--clock --delay 3.0 --rate 1.0 --start 0 $(arg bag)"/>
#     </group>

#     <!-- Point cloud segmentation -->
#     <node name="cloud_segmentation" pkg="traversability_estimation" type="cloud_segmentation_tconcord3d" output="screen">
#         <rosparam subst_value="true">
#             device: $(arg device)
#             max_age: $(arg max_age)
#             weights: $(arg weights)
#             cloud_in: $(arg input)
#             cloud_out: cloud_segmentation_tconcord3d/points
#         </rosparam>>
#     </node>

#     <!-- RVIZ -->
#     <node if="$(arg rviz)" name="rviz" pkg="rviz" type="rviz"
#           args="-d $(find traversability_estimation)/config/rviz/semantic_trav.rviz"/>

# </launch>

from launch import LaunchDescription
from launch.actions import GroupAction
from launch.actions import IncludeLaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch.conditions import IfCondition, UnlessCondition, LaunchConfigurationEquals
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node
from launch_ros.actions import PushRosNamespace
from launch_ros.actions import SetParameter
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(name='device', default_value='cuda', description='Device to run tensor operations on: cpu or cuda'),
        DeclareLaunchArgument(name='input', default_value='velodyne_points', description='Input point cloud for segmentation'),
        DeclareLaunchArgument(name='output', default_value='cloud_segmentation_tconcord3d/points', description='Output traversability point cloud topic.'),
        DeclareLaunchArgument(name='max_age', default_value='0.5'),
        DeclareLaunchArgument(name='weights', default_value='student_kitti_traversablity_f0_0_time_ema.pt'),
        # Set to false when running against live data instead of a bag replaying /clock.
        DeclareLaunchArgument(name='use_sim_time', default_value='false',
                              description='Use /clock instead of the wall clock.'),
        DeclareLaunchArgument(name='rviz', default_value='false'),

        # Point cloud segmentation
        Node(
            name='cloud_segmentation', package='traversability_estimation', executable='cloud_segmentation_tconcord3d',
            output='screen',
            parameters=[{
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'device': LaunchConfiguration('device'),
                'max_age': LaunchConfiguration('max_age'),
                'weights': LaunchConfiguration('weights'),
                'cloud_in': LaunchConfiguration('input'),
                'cloud_out': LaunchConfiguration('output'),
            }],
        ),

        # RVIZ. Note: config/rviz/semantic_trav.rviz is still in the ROS 1 rviz format
        # (rviz/... display classes) and has to be ported before rviz2 can load it.
        Node(
            name='rviz', package='rviz2', executable='rviz2',
            condition=IfCondition(LaunchConfiguration('rviz')),
            arguments=['-d', PathJoinSubstitution([FindPackageShare('traversability_estimation'),
                                                   'config', 'rviz', 'semantic_trav.rviz'])],
            parameters=[{
                'use_sim_time': LaunchConfiguration('use_sim_time'),
            }],
        ),
    ])
