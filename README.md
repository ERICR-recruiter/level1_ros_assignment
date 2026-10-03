# Level 1: ROS2 Navigation Assignment - Soham Sarpotdar
## Table of Contents
* [Repository Structure](#repository-structure)
* [Setup and Simulation](#setup-and-simulation)
    * [Setting up the repository](#1-setting-up-the-repository)
    * [Troubleshooting](#troubleshooting)
    * [Map server launch](#2-map-server-launch)
    * [AMCL Localization](#3-amcl-localization)
    * [Navigation](#4-navigation)

## Repository Structure

```
ros_nav2_assignment/
├── testbed_description/
│   ├── launch/            # Launch the full base simulation
│   ├── meshes/            # mesh files for models
│   ├── rviz/              # RVIZ configuration files
│   └── urdf/              # URDF files for Testbed-T1.0.0
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

### 1. Setting up the repository
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
>
> 5. Lidar scan range too low \
>    In `testbed.gazebo`, the range_max set for lidar sensor is 1.5 which is quite low compared to the world.
>    ```xml
>    <range>
>        <min>0.10</min>
>        <max>1.5</max>
>        <resolution>0.01</resolution>
>    </range>
>    ```
>
>    Change the max value to `12.0`
>
> 6. Adding Joint states publisher to urdf \
>    As wheel joints are of type `continuous`, they are not included by robot state publisher directly in tf tree. \
>    Add the following to `testbed.gazebo` to enable wheel joints TF
>    ```xml
>    <gazebo>
>        <plugin name="joint_state_publisher" filename="libgazebo_ros_joint_state_publisher.so">
>            <update_rate>100</update_rate>
>            <joint_name>left_wheel_joint</joint_name>
>            <joint_name>right_wheel_joint</joint_name>
>        </plugin>
>    </gazebo>
>    ``` 

### 2. Map server launch
* Launch `map_server` node with the `testbed_world.yaml` as a parameter
* The map server node is a lifecycle node and requires `lifecycle_manager` node to activate or manage its state
* Launch RViz alongside map server through the same launch file
* To visualize the map in RViz, a Fixed Frame is required to project the map image on it. A static transform publisher is used to create a transform between the frames `map` and a dummy frame `map_visualization_frame`
* **ERROR: No [map] received** when Map is added to rviz display.
    * In RViz, select the Map display, set Topic to /map, and set QoS → Durability Policy to Transient Local. Keep Fixed Frame set to map. 
    * Save the RViz config as `testbed_navigation/config/map_view.rviz`.
    * Update the launch file to start RViz with that config.

```bash
ros2 launch testbed_navigation map_loader.launch.py
```
<img width="1200" height="845" alt="map_rviz_viz" src="https://github.com/user-attachments/assets/e359becb-e418-42c1-8fb3-ab6dddaa333b" />


### 3. AMCL Localization
* Create `testbed_navigation/config/amcl_params.yaml` and add the required ros parameters.
* For understanding each parameter, refer official nav2 docs for [amcl](https://docs.nav2.org/jazzy/configuration_and_development/configuration_guide/others/configuring_amcl/)
* Set the initial pose to the one set in `spawn_testbed.launch.py`
* Add the LaunchDescription of `robot_description.launch.py`, `spawn_playground.launch.py` and `spawn_testbed.launch.py`
* AMCL needs a map to localize, so also add map server and lifecycle_manager nodes
* Using `DifferentialMotionModel` for robot motion type as our robot is DiffDrive

```bash
ros2 launch testbed_navigation localization.launch.py
```


### 4. Navigation
* Create `testbed_navigation/config/nav2_params.yaml` and add parameters for global and local costmaps, waypoint follower, behaviour tree navigator, behaviours, smoother, controllers, planners and collision monitor.
* Using default plugins for all the servers
    * Using `SimpleProgressChecker`, `SimpleGoalChecker` and `DWBLocalPlanner` plugins for Controller server
    * Using `NavfnPlanner` with A* for planner server
    * Using all 5 default plugins for behaviour server
* For further customizing  the configuration, refer the official docs for [configuratioin guide](https://docs.nav2.org/jazzy/configuration_and_development/configuration_guide/)
* Add all the nodes in the `navigation.launch.py`. Also add map server and amcl nodes for localization.

```bash
ros2 launch testbed_navigation navigation.launch.py
```
