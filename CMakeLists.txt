cmake_minimum_required(VERSION 3.8)
project(traversability_estimation)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

# Python modules (src/<module>) installed onto the Python path.
ament_python_install_package(traversability_estimation PACKAGE_DIR src/traversability_estimation)
ament_python_install_package(tconcord3d PACKAGE_DIR src/tconcord3d)
ament_python_install_package(datasets PACKAGE_DIR src/datasets)
ament_python_install_package(hrnet PACKAGE_DIR src/hrnet)

# Non-Python resources of the modules (model configs, ...) are read from the share directory.
install(DIRECTORY src
  DESTINATION share/${PROJECT_NAME}
)
install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)
install(DIRECTORY config
  DESTINATION share/${PROJECT_NAME}
)

install(DIRECTORY scripts/nodes/
  DESTINATION lib/${PROJECT_NAME}
  USE_SOURCE_PERMISSIONS
  PATTERN "__init__.py" EXCLUDE
)

ament_package()
