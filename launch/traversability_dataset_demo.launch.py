# <?xml version="1.0" encoding="UTF-8" ?>
#
# <launch>
#     <arg name="device" default="cuda" doc="Device to run tensor operations on: cpu or cuda"/>
#     <arg name="data_sequence" default="00000" doc="Sequence name from Rellis-3D dataset"/>
#     <arg name="rviz" default="true"/>
#     <arg name="traversability" default="semantic" doc="One of ['geometric', 'semantic', 'fused']"/>
#
#     <include file="$(dirname)/robot_data.launch">
#         <arg name="data_sequence" value="$(arg data_sequence)"/>
#         <arg name="pose_step" value="10"/>
#     </include>
#
#     <!-- Traversability estimation -->
#     <include file="$(dirname)/$(arg traversability)_traversability.launch">
#         <arg name="input" value="robot_data/lidar_cloud"/>
#         <arg name="height" value="64"/>
#         <arg name="width" value="2048"/>
#         <arg name="fov_elevation" value="45"/>
#         <arg if="$(eval arg('traversability') == 'semantic')" name="debug" value="true"/>
#         <arg if="$(eval arg('traversability') == 'semantic')" name="weights"
#              value="deeplabv3_resnet101_lr_0.0001_bs_16_epoch_40_Rellis3DClouds_depth_labels_None_iou_0.138.pth"/>
#     </include>
#
#     <!-- RVIZ -->
#     <node if="$(arg rviz)" name="rviz" pkg="rviz" type="rviz"
#           args="-d $(find traversability_estimation)/config/rviz/cloud_segm.rviz"/>
#
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
    DeclareLaunchArgument(name='device', default_value='cuda', description='Device to run tensor operations on: cpu or cuda'),
    DeclareLaunchArgument(name='data_sequence', default_value='00000', description='Sequence name from Rellis-3D dataset'),
    DeclareLaunchArgument(name='rviz', default_value='true'),
    DeclareLaunchArgument(name='traversability', default_value='semantic', description='One of [\'geometric\', \'semantic\', \'fused\']'),

    # SetParameter(name='use_sim_time', value=True),
    # 'use_sim_time' will be set on all nodes following the line above

    IncludeLaunchDescription(
      PythonLaunchDescriptionSource(
        [FindPackageShare('traversability_estimation'), '/launch/robot_data.launch.py'],
      ),
      launch_arguments={
        'data_sequence': LaunchConfiguration('data_sequence'),
        'pose_step': '1',
      }.items(),
    ),

    IncludeLaunchDescription(
      PythonLaunchDescriptionSource(
        [FindPackageShare('traversability_estimation'), '/launch/', LaunchConfiguration('traversability'),'_traversability.launch.py']
      ),
      launch_arguments={
        'input': 'robot_data/lidar_cloud',
        'height': '64',
        'width': '2048',
        'fov_elevation': '45',
        'debug': 'true',
        # 'weights': 'deeplabv3_resnet101_lr_0.0001_bs_16_epoch_40_Rellis3DClouds_depth_labels_None_iou_0.138.pth',
        # 'weights': 'deeplabv3_resnet101_lr_0.0001_bs_80_epoch_66_SemanticKITTI_Rellis3DClouds_depth_64x256_labels_traversability_iou_0.903.pth'
        # 'weights': 'deeplabv3_resnet101_lr_0.0001_bs_8_epoch_90_TraversabilityClouds_depth_labels_traversability_iou_0.972.pth'
        'weights': 'deeplabv3_resnet101_lr_0.0001_bs_80_epoch_54_TraversabilityClouds_depth_64x256_labels_traversability_iou_0.919.pth'
        # 'weights': 'deeplabv3_resnet101_lr_0.0001_bs_64_epoch_40_Rellis3DClouds_TraversabilityClouds_depth_64x256_labels_traversability_iou_0.788.pth'
        # 'weights': 'deeplabv3_resnet101_lr_0.0001_bs_8_epoch_62_FlexibilityClouds_depth_labels_flexibility_iou_0.884.pth'
      }.items(),
    ),

    Node(
      condition=IfCondition(LaunchConfiguration('rviz')),
      name='rviz',
      package='rviz2',
      executable='rviz2',
      arguments=['-d', [FindPackageShare('traversability_estimation'), '/config/rviz/cloud_segm.rviz']]
    )
  ])