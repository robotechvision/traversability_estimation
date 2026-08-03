# <?xml version="1.0" encoding="UTF-8" ?>
# <launch>
#     <arg name="device" default="cuda" doc="Device to run tensor operations on: cpu or cuda"/>
#     <arg name="input" default="points_filtered_jetson" doc="Input point cloud for segmentation"/>
#     <arg name="output" default="traversability" doc="Output traversability point cloud topic."/>
#     <arg name="max_age" default="0.5"/>
#     <arg name="debug" default="false"/>
#     <arg name="weights" default="deeplabv3_resnet101_lr_0.0001_bs_64_epoch_32_TraversabilityClouds_depth_64x256_labels_traversability_iou_0.928.pth"/>
#     <arg name="height" default="64"/>
#     <arg name="width" default="256"/>
#     <arg name="fov_elevation" default="90"/>  <!-- 90 deg -->
#     <arg name="preprocessing" default="true"/>
#     <arg name="nodelet_manager" default="semantic_traversability_manager"/>
#     <arg name="nodelet_action" default="$(eval 'load' if nodelet_manager.strip() else 'standalone')"/>
#
#         <node name="projection_first" pkg="nodelet" type="nodelet"
#               args="$(arg nodelet_action) cloud_proc/projection $(arg nodelet_manager)"
#               respawn="true" respawn_delay="1.0" output="log">
#             <rosparam subst_value="true">
#                 height: $(arg height)
#                 width: $(arg width)
#                 keep: 0  <!-- keep first -->
#                 azimuth_only: false
#                 frame: odom
#             </rosparam>
#             <param name="fov_elevation" value="$(eval arg('fov_elevation') / 180. * 3.1415)"/>
#
#             <remap from="input" to="$(arg input)"/>
#             <remap from="output" to="points_first"/>
#         </node>
#
# <!--    Point cloud segmentation -->
#     <node name="cloud_segmentation" pkg="traversability_estimation" type="cloud_segmentation">
#         <env name="PYTHONPATH" value="$(dirname)/../thirdparty/vision:$(optenv PYTHONPATH)"/>
#         <rosparam subst_value="true">
#             device: $(arg device)
#             max_age: $(arg max_age)
#             lidar_channels: $(arg height)
#             lidar_beams: $(arg width)
#             range_projection: false
#             debug: $(arg debug)
#             soft_label_ind: 1
#             weights: $(arg weights)
#             cloud_in: points_first
#             cloud_out: semantic_traversability
#         </rosparam>
#         <param name="lidar_fov_up" value="$(eval arg('fov_elevation') / 2.)"/>
#         <param name="lidar_fov_down" value="$(eval -arg('fov_elevation') / 2.)"/>
#     </node>
# </launch>

from launch import LaunchDescription
from launch.actions import GroupAction
from launch.actions import IncludeLaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
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
        DeclareLaunchArgument(name='output', default_value='traversability', description='Output traversability point cloud topic.'),
        DeclareLaunchArgument(name='max_age', default_value='0.5'),
        DeclareLaunchArgument(name='debug', default_value='false'),
        DeclareLaunchArgument(name='weights', default_value='deeplabv3_resnet101_lr_0.0001_bs_64_epoch_32_TraversabilityClouds_depth_64x256_labels_traversability_iou_0.928.pth'),
        DeclareLaunchArgument(name='height', default_value='64'),
        DeclareLaunchArgument(name='width', default_value='256'),
        DeclareLaunchArgument(name='fov_elevation', default_value='90'),  # 90 deg
        DeclareLaunchArgument(name='preprocessing', default_value='true'),
        DeclareLaunchArgument(name='nodelet_manager', default_value='semantic_traversability_manager'),
        DeclareLaunchArgument(name='nodelet_action', default_value='$(eval \'load\' if nodelet_manager.strip() else \'standalone\')'),

        # Projection
        Node(
            name='projection_first', package='cloud_proc', executable='projection',
            parameters=[{
                'height': LaunchConfiguration('height'),
                'width': LaunchConfiguration('width'),
                'keep': 0,  # keep first
                'azimuth_only': False,
                'frame': 'odom',
                'timeout' : 2.0,
            }],
            remappings=[('input', LaunchConfiguration('input')), ('output', 'velodyne_points_pre')],
            condition=IfCondition(LaunchConfiguration('preprocessing')),
        ),


        # Point cloud segmentation
        Node(
            name='cloud_segmentation', package='traversability_estimation', executable='cloud_segmentation',
            parameters=[{
                'device': LaunchConfiguration('device'),
                'max_age': LaunchConfiguration('max_age'),
                'lidar_channels': LaunchConfiguration('height'),
                'lidar_beams': LaunchConfiguration('width'),
                'range_projection': False,
                'debug': LaunchConfiguration('debug'),
                'soft_label_ind': 1,
                'weights': LaunchConfiguration('weights'),
                'cloud_in': 'velodyne_points_pre',
                'cloud_out': 'semantic_traversability',
                'lidar_fov_up': PythonExpression([LaunchConfiguration('fov_elevation'), ' / 2.']),
                'lidar_fov_down': PythonExpression(['-', LaunchConfiguration('fov_elevation'), ' / 2.']),
            }],
        ),
    ])
