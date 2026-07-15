# ROS2 Autonomous Coverage Robot

**Stack:** ROS2 Jazzy, Gazebo Harmonic, TurtleBot3 Waffle, `slam_toolbox`, Nav2, `path_coverage_ros2`
**Repo:** `github.com/adli-syauqi/ros_backend`
**Workspace:** `~/ros_backend_ws`

## Overview

This project drives a TurtleBot3 Waffle through a full autonomous coverage pipeline in Gazebo:

1. **Mapping** — teleop the robot around the arena while `slam_toolbox` builds a 2D occupancy map, then save it.
2. **Coverage planning** — with Nav2 bringup running on the saved map, click polygons in RViz to generate boustrophedon (back-and-forth) coverage paths for one or more areas, saved as waypoint YAML files.
3. **Execution** — a waypoint-follower node loads the generated YAML file(s) and drives the robot through each area's waypoints in sequence via Nav2's `NavigateToPose` action.

## Prerequisites

- ROS2 Jazzy, Gazebo Harmonic, and this workspace built (`colcon build`, then `source install/setup.bash`).

## Step 1 — Mapping

Build a map of the arena using SLAM before anything else; Nav2 bringup and coverage planning both depend on having a saved map.

```bash
# Terminal 1 — Gazebo world
ros2 launch coverage_robot arena_world.launch.py

# Terminal 2 — SLAM
ros2 launch slam_toolbox online_async_launch.py

# Terminal 3 — visualize (no dedicated RViz launch file for mapping yet;
# add the Map and LaserScan displays manually)
rviz2

# Terminal 4 — drive the robot around until the map looks complete in RViz
ros2 run turtlebot3_teleop teleop_keyboard

# Once the map looks good, save it (creates ~/map.yaml and ~/map.pgm)
ros2 run nav2_map_server map_saver_cli -f ~/map
```

## Step 2 — Coverage planning and execution

With a saved map in hand, bring up Nav2 and generate coverage paths for one or more areas.

```bash
# Terminal 1 — Gazebo world
ros2 launch coverage_robot arena_world.launch.py

# Terminal 2 — Nav2 bringup (uses a local custom params file, see Configuration notes below)
ros2 launch nav2_bringup bringup_launch.py \
  map:=/home/adly/map.yaml \
  params_file:=/home/adly/ros_backend_ws/nav2_params/waffle_custom.yaml \
  use_sim_time:=true

# Terminal 3 — RViz
ros2 launch nav2_bringup rviz_launch.py
# Use "2D Pose Estimate" to seed AMCL as soon as RViz opens

# Terminal 4 — optional, drive around briefly to help AMCL converge
ros2 run turtlebot3_teleop teleop_keyboard

# Terminal 5a — plan the first area
ros2 launch path_coverage path_coverage.launch.py output_filename:=~/area1.yaml
# click a polygon in RViz, wait for "writing the data to the YAML file...", then Ctrl+C

# Terminal 5b — plan additional areas the same way, one launch per area
ros2 launch path_coverage path_coverage.launch.py output_filename:=~/area2.yaml
# click a different polygon, wait for the write confirmation, then Ctrl+C

# confirm the files were written before executing
ls -la ~/area1.yaml ~/area2.yaml

# Terminal 6 — drive through all planned areas in sequence
ros2 launch path_coverage waypoint_follower.launch.py yaml_pattern:="~/area*.yaml"
```

`yaml_pattern` accepts any glob; files are matched and executed in sorted filename order, with `[area N/M: filename]`-prefixed logging per area so progress is easy to follow in the terminal.

## Configuration notes

- `nav2_params/waffle_custom.yaml` is a local copy of the installed `waffle.yaml` (the installed one is read-only), with `max_vel_x` and `max_speed_xy` raised from `0.3` to `0.5` for faster coverage runs.
- `min_wp_dist` in `path_coverage.launch.py` is tuned to `0.5` (from a default of `4.5`), matching `robot_width: 0.6` for a 10x10m arena; produces 30–56+ waypoints per area depending on shape.
