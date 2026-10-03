# Level 1: ROS2 Navigation Assignment - Soham Sarpotdar
## Table of Contents

## Repository Structure

```
ros_nav2_assignment/
├── testbed_description/
│   ├── launch/            # Launch the full base simulation
│   ├── meshes/
│   ├── rviz/            # RVIZ configuration files
│   └── urdf/            # URDF files for Testbed-T1.0.0
├── testbed_gazebo/
│   ├── worlds/            # Simulation world files
│   ├── launch/            # Launch files for Gazebo
│   └── models/            # Misc. Gazebo model files
├── testbed_bringup/
│   ├── launch/            # Launch file for bringing up the robot
│   └── maps/              # Predefined map of the test environment
├── testbed_navigation/
│   ├── launch/            # Launch files for map server, amcl and navigation
│   ├── config/            # param files and rviz configs
└── README.md              # Navigation setup and troubleshooting
```

## Setup and Simulation

### 1. Setting Up the Repository
1. Create your workspace:
    ```bash
    mkdir -p ~/assignment_ws/src
    ```
2. Clone this repository:
   ```bash
   cd ~/assignment_ws/src
   git clone <repository-url>
   ```
3. Build the workspace:
   ```bash
   cd ~/assignment_ws/
   colcon build
   ```
4. Install dependencies:
   ```bash
   sudo apt update
   sudo apt install \
       ros-${ROS_DISTRO}-gazebo-plugins \
       ros-${ROS_DISTRO}-gazebo-ros-pkgs \
       ros-${ROS_DISTRO}-navigation2 \
       ros-${ROS_DISTRO}-nav2-bringup
   ```
> ### Troubleshooting
> 1. Cmake error during colcon build
>    ```bash
>    CMake Error at CMakeLists.txt:24:
>        Parse error. Expected "(", got newline with text "
>
>        ".
>    ```
>
>    Missing parantheses in CMakeLists.txt \
>    Open `testbed_description/CMakeLists.txt` and change line 23 to `ament_package()` \
>    Rebuild the workspace with `colcon build`
>
> 2. Missing `maps` in testbed_bringup share directory \
>    Open `testbed_bringup/CMakeLists.txt` and add `maps` to the list of `DIRECTORY` to be installed
>
> 3. Incorrect path to the map file in yaml 
>    ```bash
>    image: wrong_path_testbed_world.pgm
>    mode: trinary
>    resolution: 0.05
>    origin: [-10.2, -9.94, 0]
>    negate: 0
>    occupied_thresh: 0.65
>    free_thresh: 0.25
>    ```
>
>    Change the name of the image to correct one - `testbed_world.pgm`
>
> 4. DiffDrive and lidar sensor plugins not found \
>    In `testbed_gazebo/launch/spawn_playground.launch.py`, the gazebo environment variable `GAZEBO_PLUGIN_PATH` is set. In my case, the variable was not empty so the resulting path became `install/test_description/lib` \
>    To let gazebo locate the ros plugins for DiffDrive and lidar, change these lines
>    ```bash
>    if 'GAZEBO_PLUGIN_PATH' in os.environ:
>        os.environ['GAZEBO_PLUGIN_PATH'] = os.environ['GAZEBO_PLUGIN_PATH'] + ':' + install_dir + '/lib'
>    else:
>        os.environ['GAZEBO_PLUGIN_PATH'] = install_dir + '/lib'
>    ```
>
>    to
>    ```bash
>    ros_plugin_path = "/opt/ros/humble/lib"
>    plugins_to_add = f"{ros_plugin_path}:{install_dir}/lib"
>    if 'GAZEBO_PLUGIN_PATH' in os.environ:
>        os.environ['GAZEBO_PLUGIN_PATH'] = os.environ['GAZEBO_PLUGIN_PATH'] + ':' + plugins_to_add
>    else:
>        os.environ['GAZEBO_PLUGIN_PATH'] = plugins_to_add
>    ```

### 2. Map Loading
1. Use the map provided in `testbed_bringup/maps/testbed_world.yaml`.
2. Write actions in the launch file `testbed_navigation/launch/map_loader.launch.py` to load the map using the `map_server` plugin.
3. Test and confirm that the map is loaded correctly in Rviz.

### 3. AMCL Localization
1. Implement localization with the AMCL plugin:
   - Write a parameter file for AMCL in `testbed_navigation/config/amcl_params.yaml`.
   - Create actions in the launch file `testbed_navigation/launch/localization.launch.py` to run AMCL.
   - Verify that the robot can localize itself in the simulated environment using Rviz.

### 4. Navigation
1. Set up navigation using `nav2` plugins:
   - Configure parameter files for the global and local planners, behaviour tree plugins and any other nav2 plugin you want to use, like 'collision_monitor' or 'velocity_smoother', in `testbed_navigation/config/nav2_params.yaml`.
   - Write actions in the launch file `testbed_navigation/launch/navigation.launch.py` to bring up the navigation workflow.
2. Test the navigation setup by sending goals to the robot and observing its behavior.
