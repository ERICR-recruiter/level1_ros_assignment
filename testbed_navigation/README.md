# `testbed_navigation` — Implementation Notes

---

## Where I Started

The assignment gave me the `testbed_bringup`, `testbed_description`, and `testbed_gazebo` packages as a starting point — along with a pre-built map of the arena. My job was to create a new `testbed_navigation` package from scratch that could load that map, localize the robot, and navigate it to goals.

The first thing I did was actually try to launch what was there.

```bash
ros2 launch testbed_bringup testbed_full_bringup.launch.py
```

---

## Fixing the Starter Code

Before writing the navigation node, I had to get the simulation environment actually running. Here's what was broken and what I did about it.

### The robot model threw errors in Gazebo

Two issues inside `testbed.gazebo`:
- A leftover `libgazebo_ros_control.so` plugin from ROS 1 that Gazebo was choking on under ROS 2 Humble. Removed it.
- A malformed XML closing tag with a stray `>` — `</initial_orientation_as_reference>>` — which was causing the URDF to parse incorrectly.

While I was in there, I also noticed the caster wheel friction was set unrealistically high, causing the robot to resist turning. Dropped `mu1` and `mu2` to `0.001`.

### CMakeLists issues

Two packages were missing install targets:
- `testbed_description` had `ament_package` without parentheses — a subtle but fatal CMake error.
- `testbed_bringup` wasn't installing the `maps/` folder, meaning `testbed_world.yaml` and `testbed_world.pgm` were never copied to `share/`. The map loader had no map to load.
- `testbed_gazebo` had the same issue with `models/` — the playground model files were never installed.

### The map YAML had the wrong image filename

`testbed_world.yaml` referenced:
```yaml
image: wrong_path_testbed_world.pgm
```
The actual file sitting right next to it was `testbed_world.pgm`. Simple rename error, but it meant `map_server` would error out immediately trying to load a file that didn't exist.

---

## Building the Navigation Package

Once the simulation was actually launching and I could see the robot in the world, I created the `testbed_navigation` package:

```bash
ros2 pkg create testbed_navigation --build-type ament_cmake
```

separate launch files for map loading, localization, and navigation rather than one big bringup script. The assignment explicitly asked for this, but it also just makes debugging easier: if AMCL is misbehaving, I can restart it without killing the map server.

The final structure ended up as:

```
testbed_navigation/
├── config/
│   ├── amcl_params.yaml          # AMCL tuned for the Testbed robot
│   └── nav2_params.yaml          # Nav2: planners, controllers, behaviors, costmaps
├── launch/
│   ├── map_loader.launch.py      # Just the map server + its lifecycle manager
│   ├── localization.launch.py    # AMCL (optionally includes map server)
│   ├── navigation.launch.py      # Planners, controller, BT navigator, behaviors
│   └── testbed_navigation.launch.py  # All-in-one with RViz
└── rviz/
    └── nav2_default_view.rviz    # Pre-configured view: map, costmaps, particles, goal tool
```

---

## Step 1 — Getting the Map to Load

The first launch file I wrote was `map_loader.launch.py`. It starts a `nav2_map_server` node pointed at `testbed_world.yaml` and a `lifecycle_manager` to transition it to `ACTIVE`.

```bash
ros2 launch testbed_navigation map_loader.launch.py
```

To verify it worked:
```bash
ros2 topic echo /map --once
```

Once the map topic was publishing, it showed up correctly in RViz as a grey-and-black occupancy grid.

---

## Step 2 — Localization with AMCL

### The initial pose problem

AMCL assumes the robot starts at `(0.0, 0.0)` by default. But the Gazebo spawn configuration places the robot at `(x=0.0, y=5.0)`. So out of the box, AMCL initialises its particle cloud in the wrong corner of the map entirely.

The fix— set `set_initial_pose: true` in `amcl_params.yaml` with the correct spawn coordinates:
```yaml
set_initial_pose: true
initial_pose:
  x: 0.0
  y: 5.0
  z: 0.0
  yaw: 0.0
```

### The lidar range problem

Even with the correct initial pose, AMCL's particles were not converging. The robot would sit still and the particle cloud would barely tighten. After some digging, I found the lidar's max range in the URDF was set to `1.5` metres.

In a ~20m × 20m arena, most of the walls are more than 1.5m away. AMCL's likelihood field model was scoring particles against laser returns that literally couldn't see far enough to distinguish location. I bumped the max range to `12.0` metres and updated the horizontal samples to 360 for full coverage. After that, particles converged in seconds.

### Running localization

With the map server already running:
```bash
ros2 launch testbed_navigation localization.launch.py include_map:=false
```

Or to bring up map + AMCL together:
```bash
ros2 launch testbed_navigation localization.launch.py
```

You can tell it's working when `/amcl_pose` starts publishing and the yellow particle cloud in RViz clusters around the robot.

---

## Step 3 — Navigation

With localization working, I moved on to the actual navigation stack. I chose:

| Role | Plugin |
|---|---|
| Global planner | `nav2_navfn_planner/NavfnPlanner` |
| Local controller | `dwb_core::DWBLocalPlanner` |
| Recovery behaviors | `Spin`, `BackUp`, `DriveOnHeading`, `Wait` |
| Behavior tree | `nav2_bt_navigator` (default BT) |
| Global costmap | Static Layer + Obstacle Layer + Inflation Layer |
| Local costmap | Obstacle Layer + Inflation Layer (rolling window) |

Nothing exotic — the assignment asks for basic navigational functionality and these are the standard Nav2 defaults. I configured them in `nav2_params.yaml` and started the navigation launch file:

```bash
ros2 launch testbed_navigation navigation.launch.py
```

### The lifecycle decoupling problem

One headache I ran into: when running each launch file independently, the lifecycle managers would fail to transition their nodes if any node in their managed list wasn't running. By default, a single `lifecycle_manager` would try to manage map server, AMCL, and nav nodes all at once — and if I only launched navigation, it would error looking for AMCL.

The fix was to give each subsystem its own dedicated lifecycle manager:
- `lifecycle_manager_map_server` — manages only `map_server`
- `lifecycle_manager_localization` — manages only `amcl`
- `lifecycle_manager_navigation` — manages the nav2 nodes

That way each component is fully self-contained and can be launched independently without caring what else is or isn't running.

---

## Step 4 — All-at-Once Bringup

Once everything was working individually, I tied it all together in `testbed_navigation.launch.py` — a single launch file that brings up the complete stack with RViz pre-configured:

```bash
ros2 launch testbed_navigation testbed_navigation.launch.py
```

This launches:
- `map_server` (testbed arena map)
- `amcl` (initial pose preset to the Gazebo spawn position)
- The full Nav2 controller/planner/behavior/BT stack
- RViz with the map, costmaps, particle cloud, plan visualisation, and 2D Goal Pose tool already configured

---


## Quick Reference: Recommended DDS Setup

Before running anything Nav2-related, it's worth setting Cyclone DDS. It avoids discovery and action timeout issues that can make Nav2 look broken when it isn't:

```bash
sudo apt install -y ros-humble-rmw-cyclonedds-cpp
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

Added it to `.bashrc` to persist between terminals.

---

## Summary 

Three independent, composable launch files — map loading, localization, navigation — each managing their own lifecycle, each testable in isolation. A single all-in-one launch file for when you just want everything running. Parameter files tuned for the specific robot geometry and arena size. And a bunch of starter code bugs fixed along the way before any of this was possible.

The modular approach took a bit more upfront work but made debugging dramatically easier. When AMCL was misbehaving, I could restart just that node. When the costmaps looked wrong, I could check the controller in isolation. That flexibility is exactly why the assignment asked for this structure rather than a single `nav2_bringup` call.

