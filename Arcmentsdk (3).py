import sys
import time
import requests
import numpy as np

# Add path to Baumer SDK
sys.path.append("C:/Users/Arc One/Downloads/Baumer_OxSDK_V2...")
import oxapi


class WeldScanner:
    def __init__(self):
        # Initialize scanner connection
        self.ox = oxapi.ox("192.168.0.250")
        self.ox.Connect()
        self.ox.Login("admin", "")

        # Get scanner info
        self.maxLen, self.xunit, self.zunit = self.ox.GetProfileInfo()
        print("Scanner Info: Max Length={}, X Unit={}, Z Unit={}".format(self.maxLen, self.xunit, self.zunit))

        # System parameters
        self.duet_ip = "192.168.0.4"
        self.x_offset = 10
        self.y_offset = 11
        self.z_offset = 12
        self.weld_speed = 387
        self.z_buffer = 30
        self.z_range = (300, 500)  # Define working range (example: 300 mm to 500 mm)

        # Initialize tracking variables
        self.max_height = float('-inf')
        self.height_history = []

    def send_gcode(self, command):
        url = "http://{}/rr_gcode?gcode={}".format(self.duet_ip, command)
        try:
            response = requests.get(url)
            return response.json()
        except Exception as e:
            print("G-code error: {}".format(e))
            return None

    def send_gcodes(self, commands):
        for command in commands:
            response = self.send_gcode(command)
            print("Command: {}, Response: {}".format(command, response))

    def get_profile(self, retries=3):
        """Fetch profile data with retry logic."""
        for attempt in range(retries):
            try:
                qualityId, timeStamp, precision, xStart, length, x, z = self.ox.GetProfile()
                if qualityId != 0:
                    print("Warning: Profile quality issue ({})".format(qualityId))
                    continue

                # Convert to mm
                x_mm = [(xStart + x[i]) / precision for i in range(length)]
                z_mm = [z[i] / precision for i in range(length)]

                # Filter measurements within the work range
                valid_indices = [
                    i for i in range(len(z_mm)) if self.z_range[0] <= z_mm[i] <= self.z_range[1]
                ]
                x_mm = [x_mm[i] for i in valid_indices]
                z_mm = [z_mm[i] for i in valid_indices]

                # Remove outliers
                if z_mm:
                    z_mean = np.mean(z_mm)
                    z_std = np.std(z_mm)
                    z_mm = [z for z in z_mm if abs(z - z_mean) < 2 * z_std]

                return x_mm, z_mm
            except Exception as e:
                print("Profile error (attempt {} of {}): {}".format(attempt + 1, retries, e))
                time.sleep(1)  # Wait before retrying

        print("Failed to retrieve profile data after {} attempts.".format(retries))
        return None, None

    def scan(self, z, x0, y0, x1, y1, h, duration=5.0):
        init_move = [
            "G1 F1000 Z{}".format(z + self.z_offset + self.z_buffer),
            "G1 X{} Y{} Z{}".format(x0 + self.x_offset, y0 + self.y_offset, z + self.z_offset),
        ]
        scanning_move = [
            "G4 S1",
            "G1 X{} Y{}".format(x1 + self.x_offset, y1 + self.y_offset)
        ]

        print("Moving to start position...")
        self.send_gcodes(init_move)
        print("Starting scan...")
        self.send_gcodes(scanning_move)

        start_time = time.time()
        profile_count = 0

        while time.time() - start_time < duration:
            x_mm, z_mm = self.get_profile()

            if x_mm and z_mm:
                current_max = max(z_mm)
                self.height_history.append(current_max)

                if current_max > self.max_height:
                    self.max_height = current_max
                    max_index = z_mm.index(current_max)
                    max_x_pos = x_mm[max_index]
                    self.max_position = (max_x_pos, profile_count)

                profile_count += 1

            time.sleep(0.1)

        print("\nScan Results:")
        print("Maximum height: {:.3f} mm".format(self.max_height))
        print("Average height: {:.3f} mm".format(np.mean(self.height_history)))
        print("Profiles captured: {}".format(profile_count))
        if hasattr(self, 'max_position'):
            print("Max height position (X, Profile): {}".format(self.max_position))

        return z


def main():
    scanner = WeldScanner()

    try:
        filename = input("Please enter a gcode file to run: ")
        with open(filename, "r") as file:
            gcode_commands = file.readlines()

        z0 = x0 = y0 = x1 = y1 = 0

        for i, command in enumerate(gcode_commands):
            if "Z" in command:
                comment_index = sys.maxsize
                if ";" in command:
                    comment_index = command.index(";")
                if comment_index > command.index("Z"):
                    z = float(command.split("Z")[1].split(" ")[0])

            if command.startswith(";TYPE:WALL-OUTER"):
                x0, y0 = float(gcode_commands[i - 1].split("X")[1].split(" ")[0]), float(
                    gcode_commands[i - 1].split("Y")[1].split(" ")[0])
                z0 = float(gcode_commands[i + 1].split("Z")[1].split(" ")[0])

            if command.startswith("M42 P1 S0"):
                x1, y1 = float(gcode_commands[i - 3].split("X")[1].split(" ")[0]), float(
                    gcode_commands[i - 3].split("Y")[1].split(" ")[0])

        print("\nStarting scanning and welding sequence...")
        z0 = scanner.scan(z0, x0, y0, x1, y1, 0)

    except Exception as e:
        print("Error in main sequence: {}".format(e))
    finally:
        scanner.ox.Disconnect()


if __name__ == "__main__":
    main()
