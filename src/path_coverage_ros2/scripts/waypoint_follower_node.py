#!/usr/bin/env python3
import os
import glob
import yaml
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped
class WaypointFollower(Node):
	def __init__(self):
		super().__init__('waypoint_follower')
		self.declare_parameter("yaml_pattern", "~/pose_output.yaml")
		self.declare_parameter("global_frame", "map")
		self.yaml_pattern = self.get_parameter("yaml_pattern").get_parameter_value().string_value
		self.global_frame = self.get_parameter("global_frame").get_parameter_value().string_value
		self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
	def find_area_files(self):
		expanded = os.path.expanduser(self.yaml_pattern)
		files = sorted(glob.glob(expanded))
		self.get_logger().info(f"Matched {len(files)} area file(s) for pattern {expanded}")
		return files
	def load_waypoints(self, path):
		with open(path, "r") as f:
			data = yaml.safe_load(f)
		keys = [k for k in data.keys() if k != "updatetime"]
		keys_sorted = sorted(keys, key=lambda k: int(k))
		waypoints = []
		for k in keys_sorted:
			entry = data[k]
			waypoints.append(entry)
		self.get_logger().info(f"Loaded {len(waypoints)} waypoints from {path}")
		return waypoints
	def pose_from_entry(self, entry):
		pose = PoseStamped()
		pose.header.frame_id = self.global_frame
		pose.header.stamp = self.get_clock().now().to_msg()
		pose.pose.position.x = entry["position"]["x"]
		pose.pose.position.y = entry["position"]["y"]
		pose.pose.position.z = entry["position"]["z"]
		pose.pose.orientation.x = entry["orientation"]["x"]
		pose.pose.orientation.y = entry["orientation"]["y"]
		pose.pose.orientation.z = entry["orientation"]["z"]
		pose.pose.orientation.w = entry["orientation"]["w"]
		return pose
	def send_goal(self, pose, index, total, area_prefix):
		self.get_logger().info(f"{area_prefix} Sending waypoint {index}/{total}: x={pose.pose.position.x:.2f}, y={pose.pose.position.y:.2f}")
		goal_msg = NavigateToPose.Goal()
		goal_msg.pose = pose
		send_goal_future = self.nav_client.send_goal_async(goal_msg)
		rclpy.spin_until_future_complete(self, send_goal_future)
		goal_handle = send_goal_future.result()
		if not goal_handle.accepted:
			self.get_logger().warn(f"{area_prefix} Waypoint {index}/{total} was rejected by Nav2, skipping.")
			return False
		result_future = goal_handle.get_result_async()
		rclpy.spin_until_future_complete(self, result_future)
		result = result_future.result()
		status = result.status
		# status 4 == STATUS_SUCCEEDED per action_msgs/msg/GoalStatus
		if status == 4:
			self.get_logger().info(f"{area_prefix} Waypoint {index}/{total} reached successfully.")
			return True
		else:
			self.get_logger().warn(f"{area_prefix} Waypoint {index}/{total} finished with status {status} (not success).")
			return False
	def run_area(self, path, area_index, area_total):
		area_prefix = f"[area {area_index}/{area_total}: {os.path.basename(path)}]"
		waypoints = self.load_waypoints(path)
		if not waypoints:
			self.get_logger().warn(f"{area_prefix} No waypoints found. Skipping.")
			return 0, 0
		total = len(waypoints)
		succeeded = 0
		for i, entry in enumerate(waypoints, start=1):
			pose = self.pose_from_entry(entry)
			ok = self.send_goal(pose, i, total, area_prefix)
			if ok:
				succeeded += 1
		self.get_logger().info(f"{area_prefix} Completed: {succeeded}/{total} succeeded.")
		return succeeded, total
	def run(self):
		files = self.find_area_files()
		if not files:
			self.get_logger().warn("No area files matched the pattern. Nothing to do.")
			return
		self.get_logger().info("Waiting for navigate_to_pose action server...")
		self.nav_client.wait_for_server()
		self.get_logger().info("Action server available, starting waypoint following.")
		grand_succeeded = 0
		grand_total = 0
		for area_index, path in enumerate(files, start=1):
			s, t = self.run_area(path, area_index, len(files))
			grand_succeeded += s
			grand_total += t
		self.get_logger().info(f"All areas completed: {grand_succeeded}/{grand_total} waypoints succeeded across {len(files)} area(s).")
def main(args=None):
	rclpy.init(args=args)
	node = WaypointFollower()
	try:
		node.run()
	except Exception as e:
		import traceback
		traceback.print_exc()
	finally:
		node.destroy_node()
		rclpy.shutdown()
if __name__ == '__main__':
	main()
