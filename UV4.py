import tkinter as tk
import json
import paho.mqtt.client as mqtt
from tkinter import simpledialog
from tkinter import messagebox
from tkinter import Menu
import re
import time
import threading
import random
import os
import msvcrt


# MQTT broker details
BROKER = "192.168.109.155"
PORT = 1883
TOPIC = "logs/ual"
USERNAME = "testuser"
PASSWORD = "testpass"

UAL_FILE_PATH = r'C:\Users\janva\Downloads\ual.json'
CHECK_DONE_PATH = r"C:\Shared\checkDone.json"
SNAP_UAL_FILE_PATH = r"C:\Shared\snapUal.json"

# MQTT Client setup
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(USERNAME, PASSWORD)
mqtt_client.connect(BROKER, PORT)
mqtt_client.loop_start()


class User:
    def __init__(self, name, behavior="default", timeList=None, position=(0, 0)):
        if timeList is None:
            timeList = []
        self.name = name
        self.behavior = behavior
        self.timeList = timeList
        self.position = position

class Model:
    def __init__(self):
        self.data = "Hello, MVC!"
        self.users = []

    def addUser(self, user):
        self.users.append(user)

    def getUserByName(self, username):  # ✅ New method
        for user in self.users:
            if user.name == username:
                return user
        return None  # Return None if user is not found


class View(tk.Tk):
    def __init__(self, windowSize=900, squareSize=600):
        super().__init__()
        self.controller = None
        self.windowSize = windowSize
        self.squareSize = squareSize
        self.geometry(f"{self.windowSize}x{self.windowSize}")
        self.currentMode = None
        self.json_lock = threading.Lock()

        # Create a navbar frame at the top
        self.navbar = tk.Frame(self, bg="lightgray", height=50)
        self.navbar.pack(side="top", fill="x")

        # Add button inside the navbar
        self.check_config_button = tk.Button(self.navbar, text="Check Configurations", command=self.checkConfigurations)
        self.check_config_button.pack(pady=10, padx=10, side="left")

        # Add Start Simulation button inside the navbar
        self.start_sim_button = tk.Button(self.navbar, text="Start Simulation", command=lambda: self.controller.startUserMovement())
        self.start_sim_button.pack(pady=10, padx=10, side="left")

        # Add Stop Simulation button inside the navbar
        self.stop_sim_button = tk.Button(self.navbar, text="Stop Simulation", command=lambda: self.controller.stopUserMovement())
        self.stop_sim_button.pack(pady=10, padx=10, side="left")

        # Canvas for main content
        self.canvas = tk.Canvas(self, width=self.windowSize, height=self.windowSize, bg="white")
        self.canvas.pack(fill="both", expand=True)

        # Add "Nudge Director1" button inside the navbar
        self.nudge_button = tk.Button(
            self.navbar,
            text="Nudge Director1",
            command=lambda: self.controller.nudgeUser("Manager2")  # ✅ Pass function through controller
        )
        self.nudge_button.pack(pady=10, padx=10, side="left")

        # Add a dropdown menu to the navbar
        self.menu_bar = Menu(self)

        # Create dropdown
        self.dropdown_menu = Menu(self.menu_bar, tearoff=0)
        self.dropdown_menu.add_command(label="Random Movement", command=lambda: self.set_mode("Random Movement"))
        self.dropdown_menu.add_command(label="Stagnant (Manual Movement)", command=lambda: self.set_mode("Stagnant (Manual Movement)"))
        # self.dropdown_menu.add_command(label="Option 3", command=lambda: self.set_mode("Option 3"))

        # Add dropdown to menu bar
        self.menu_bar.add_cascade(label="User Behavior (All)", menu=self.dropdown_menu)

        # Attach menu to the window
        self.config(menu=self.menu_bar)

        self.drawQuadrants()
        self.userCircles = {}
        self.userTexts = {}
        self.currentlyDragging = None
        self.offsetX = 0
        self.offsetY = 0

    def set_mode(self, mode):
        """ Updates currentMode when an option is selected """
        self.currentMode = mode
        print(f"Current Mode changed to: {self.currentMode}")  # Debugging output

    def getRandomPositionForRoom(self, room_name):
        """Returns a random (x, y) position within the given room, ensuring the circle stays inside."""
        room_boundaries = {
            "Room C": (150, 450, 150, 450),
            "Room A": (150, 450, 450, 750),
            "Room D": (450, 750, 150, 450),
            "Room B": (450, 750, 450, 750),
        }

        if room_name not in room_boundaries:
            return None  # Room not found

        min_x, max_x, min_y, max_y = room_boundaries[room_name]

        circle_size = 50  # Ensure the circle stays inside the boundary
        adjusted_max_x = max_x - circle_size
        adjusted_max_y = max_y - circle_size

        # Generate a valid position within the adjusted bounds
        random_x = random.randint(min_x, adjusted_max_x)
        random_y = random.randint(min_y, adjusted_max_y)

        return (random_x, random_y)

    def getShortName(self, fullName):
        return "".join([word[0] for word in fullName.split()]) + fullName[-1] if fullName else fullName

    def checkConfigurations(self):
        """Displays the movement schedule (timeList) of all users."""
        if not self.controller or not self.controller.model.users:
            messagebox.showinfo("User Configurations", "No users found.")
            return

        config_text = ""
        for user in self.controller.model.users:
            schedule = "\n".join(f"  {room}: {minutes}m" for room, minutes in user.timeList)  # Fixed
            config_text += f"{user.name}:\n{schedule if schedule else '  No schedule set'}\n\n"

        # Create a custom window with larger text
        config_window = tk.Toplevel(self)
        config_window.title("User Configurations")
        config_window.geometry("425x550")

        label = tk.Label(config_window, text=config_text, font=("Arial", 14), justify="left", wraplength=480)
        label.pack(padx=20, pady=20)

        close_button = tk.Button(config_window, text="Close", command=config_window.destroy)
        close_button.pack(pady=10)

    def setController(self, controller):
        self.controller = controller

    def drawQuadrants(self):
        self.squareSize = min(self.squareSize, self.windowSize)
        offset = (self.windowSize - self.squareSize) // 2

        self.canvas.create_rectangle(
            offset, offset,
            offset + self.squareSize, offset + self.squareSize,
            outline="black", width=2
        )

        midX = offset + self.squareSize / 2
        midY = offset + self.squareSize / 2

        self.canvas.create_line(midX, offset, midX, offset + self.squareSize, fill="black", width=2)
        self.canvas.create_line(offset, midY, offset + self.squareSize, midY, fill="black", width=2)

        self.canvas.create_text(offset + self.squareSize * 0.25, offset + self.squareSize * 0.25, text="Room C",
                                font=("Arial", 16))
        self.canvas.create_text(offset + self.squareSize * 0.75, offset + self.squareSize * 0.25, text="Room D",
                                font=("Arial", 16))
        self.canvas.create_text(offset + self.squareSize * 0.25, offset + self.squareSize * 0.75, text="Room A",
                                font=("Arial", 16))
        self.canvas.create_text(offset + self.squareSize * 0.75, offset + self.squareSize * 0.75, text="Room B",
                                font=("Arial", 16))

    def drawUserCircle(self, user):
        x, y = user.position
        circle = self.canvas.create_oval(x - 25, y - 25, x + 25, y + 25, fill="blue", outline="")
        shortName = self.getShortName(user.name)
        nameText = self.canvas.create_text(x, y, text=shortName, fill="white", font=("Arial", 12))

        self.userCircles[user.name] = circle
        self.userTexts[user.name] = nameText

        self.canvas.tag_bind(circle, "<Button-1>", lambda event, user=user: self.startDrag(event, user))
        self.canvas.tag_bind(circle, "<B1-Motion>", lambda event, user=user: self.drag(event, user))
        self.canvas.tag_bind(circle, "<ButtonRelease-1>", lambda event, user=user: self.stopDrag(event, user))
        self.canvas.tag_bind(circle, "<Button-3>",
                             lambda event, user=user: self.setMovementSchedule(event, user))  # Right-click binding


    def setMovementSchedule(self, event, user):
        user.timeList.clear()  # Reset existing schedule

        while True:
            room = simpledialog.askstring("Set Movement", "Enter Room Letter (A-D) (0 to stop):", parent=self)
            if room == "0":
                break  # Exit input loop
            if not room or not re.match(r"^[ABCD]$", room):
                messagebox.showerror("Invalid Input", "Room must be a capital letter A-D.")
                continue

            minutes = simpledialog.askinteger("Set Minutes", f"Enter minutes for Room {room} (1 and up):", parent=self)
            if minutes is None:
                continue  # User canceled input
            if minutes < 1:
                messagebox.showerror("Invalid Input", "Minutes must be 1 or more.")
                continue

            user.timeList.append((room, minutes))
            messagebox.showinfo("Success", f"Schedule added: {room.upper()} for {minutes} minutes.")

    def checkRoom(self, user):
        x, y = user.position
        offset = (self.windowSize - self.squareSize) // 2
        midX = offset + self.squareSize / 2
        midY = offset + self.squareSize / 2

        if not (offset <= x <= offset + self.squareSize and offset <= y <= offset + self.squareSize):
            return "Outside the rooms"

        if x < midX and y < midY:
            return "Room C"
        elif x < midX and y > midY:
            return "Room A"
        elif x > midX and y < midY:
            return "Room D"
        elif x > midX and y > midY:
            return "Room B"

    def updateUalJson(self, user, room):
        with self.json_lock:  # Ensure only one thread modifies the file at a time
            try:
                with open(UAL_FILE_PATH, "r") as file:
                    roomAssignments = json.load(file)
            except FileNotFoundError:
                roomAssignments = {"Room A": [], "Room B": [], "Room C": [], "Room D": []}

            # Remove user from all rooms first
            for key in roomAssignments:
                if user.name in roomAssignments[key]:
                    roomAssignments[key].remove(user.name)

            # Add user to new room if applicable
            if room != "Outside the rooms" and user.name not in roomAssignments[room]:
                roomAssignments[room].append(user.name)

            # Save updated data
            with open(UAL_FILE_PATH, "w") as file:
                json.dump(roomAssignments, file, indent=4)

            print(f"{user.name} has been moved to {room}")

            # Send updated JSON to MQTT publisher
            # self.sendToPublisher(roomAssignments)

    def sendToPublisher(self, roomAssignments):
        try:
            json_message = json.dumps(roomAssignments)
            mqtt_client.publish(TOPIC, json_message, qos=1)
            print("📤 Sent updated ual.json log to publisher.")
        except Exception as e:
            print(f"❌ Failed to send MQTT message: {e}")

    def startDrag(self, event, user):
        self.currentlyDragging = user
        self.offsetX = self.canvas.coords(self.userCircles[user.name])[0] - event.x
        self.offsetY = self.canvas.coords(self.userCircles[user.name])[1] - event.y

    def drag(self, event, user):
        if self.currentlyDragging == user:
            x1 = event.x + self.offsetX
            y1 = event.y + self.offsetY
            x2 = x1 + 50
            y2 = y1 + 50
            self.canvas.coords(self.userCircles[user.name], x1, y1, x2, y2)
            self.canvas.coords(self.userTexts[user.name], x1 + 25, y1 + 25)
            user.position = (x1 + 25, y1 + 25)

    def stopDrag(self, event, user):
        if self.currentlyDragging == user:
            self.currentlyDragging = None
            coords = self.canvas.coords(self.userCircles[user.name])
            room = self.checkRoom(user)
            x = (coords[0] + coords[2]) // 2
            y = (coords[1] + coords[3]) // 2
            print(f"{user.name} dropped at: x={x}, y={y}, {room}")
            self.updateUalJson(user, room)


class Controller:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.view.setController(self)
        self.room_counts={}
        self.stop_threads = {}
        self.loadUsersFromJson()
        self.startCheckDoneLoop()
        self.lock = threading.Lock()  # Create a lock

    def nudgeUser(self, username):
        user = self.model.getUserByName(username)  # ✅ Get user object
        if not user:
            print(f"User {username} not found!")
            return

        room = self.view.checkRoom(user)  # Find out the current room
        new_x, new_y = self.view.getRandomPositionForRoom(room)  # Get a valid position

        if new_x and new_y:
            # Move user to the new position
            self.view.canvas.coords(self.view.userCircles[username], new_x, new_y, new_x + 50, new_y + 50)
            self.view.canvas.coords(self.view.userTexts[username], new_x + 25, new_y + 25)

            # Update user's position
            user.position = (new_x + 25, new_y + 25)

            # Ensure the room is updated
            self.view.updateUalJson(user, room)
            print(f"{username} nudged to new position: x={new_x}, y={new_y}, {room}")

    def startUserMovement(self):
        """Starts threads that move all predefined users between rooms at intervals."""
        users = ["AS1", "AS2", "Manager1", "Manager2", "Director1", "Director2"]

        for username in users:
            if username in self.stop_threads:
                print(f"User {username} is already moving.")
                continue

            user = self.model.getUserByName(username)  # Assuming this retrieves the user object
            if not user:
                print(f"User {username} not found!")
                continue

            stop_event = threading.Event()
            self.stop_threads[username] = stop_event
            thread = threading.Thread(target=self.simulateUserMovement, args=(user, stop_event))
            thread.daemon = True
            thread.start()
            print(f"Started movement for {username}")

    def stopUserMovement(self, username=None):
        """Stops movement for a specific user or all users if no username is provided."""
        if username:
            if username in self.stop_threads:
                self.stop_threads[username].set()
                del self.stop_threads[username]
                print(f"Stopped movement for {username}")
        else:
            for user in list(self.stop_threads.keys()):  # Copy keys to avoid modification issues
                self.stop_threads[user].set()
                del self.stop_threads[user]
                print(f"Stopped movement for {user}")

    def loadUsersFromJson(self):
        try:
            with open(UAL_FILE_PATH, "r") as file:
                roomAssignments = json.load(file)

            for room, users in roomAssignments.items():
                for username in users:
                    user = User(
                        name=username,
                        behavior="default",
                        position=self.getInitialPositionForRoom(room)
                    )
                    self.model.addUser(user)
                    self.view.drawUserCircle(user)

        except (FileNotFoundError, json.JSONDecodeError):
            print("Error loading ual.json, proceeding with no users.")

    def checkDoneStatus(self):
        """Continuously checks checkDone.json for 'done' status and updates it to 'waiting'."""
        while True:
            retries = 5  # Maximum retries to check if status is 'done'

            for attempt in range(retries):
                try:
                    with open(CHECK_DONE_PATH, "r") as file:
                        data = json.load(file)

                    print(f"Current status in loop: {data}")  # DEBUG: Print current status

                    if data.get("status") == "done":
                        print("Detected 'done' status! Proceeding...")
                        break  # Exit loop if status is 'done'
                except (FileNotFoundError, json.JSONDecodeError):
                    pass  # Ignore errors and retry

                print(f"Retrying to check 'done' status... ({attempt + 1}/{retries})")
                time.sleep(1.5)  # Short wait before retrying

            # If after retries, it's still not "done", just skip the rest
            if data.get("status") != "done":
                print("Max retries reached, but status is still not 'done'. Skipping this cycle.")
                time.sleep(1)  # Avoid excessive CPU usage
                continue

            # Once 'done' is confirmed, proceed
            with self.lock:  # Lock access to prevent conflicts
                try:
                    with open(UAL_FILE_PATH, "r") as ualFile:
                        roomAssignments = json.load(ualFile)

                    # Save the snapshot to snapUal.json
                    with open(SNAP_UAL_FILE_PATH, "w") as snapFile:
                        json.dump(roomAssignments, snapFile, indent=4)

                    # Send updated JSON to MQTT publisher
                    print("Sending updated UAL to publisher...")
                    self.view.sendToPublisher(roomAssignments)

                except (FileNotFoundError, json.JSONDecodeError):
                    print("Error: ual.json not found or invalid.")

                # **Now we update checkDone.json to "waiting"**
                try:
                    print("Updating status to 'waiting'...")
                    with open(CHECK_DONE_PATH, "w") as file:
                        json.dump({"status": "waiting"}, file, indent=4)
                    os.replace(CHECK_DONE_PATH, CHECK_DONE_PATH)  # Ensure atomic write
                except PermissionError as e:
                    print(f"Error writing 'waiting': {e}")

            time.sleep(1)  # Check again after 1 second

    def startCheckDoneLoop(self):
        """Runs checkDoneStatus in a separate thread so it doesn't block."""
        thread = threading.Thread(target=self.checkDoneStatus, daemon=True)
        thread.start()

    def simulateUserMovement(self, user, stop_event):
        """Moves user to random rooms at intervals until stopped."""
        rooms = ["Room A", "Room B", "Room C", "Room D"]

        while not stop_event.is_set():
            new_room = random.choice(rooms)
            new_position = self.view.getRandomPositionForRoom(new_room)

            if new_position:
                # Move user to new position
                user.position = new_position
                self.view.canvas.coords(
                    self.view.userCircles[user.name],
                    new_position[0] - 25, new_position[1] - 25,
                    new_position[0] + 25, new_position[1] + 25
                )
                self.view.canvas.coords(
                    self.view.userTexts[user.name],
                    new_position[0], new_position[1]
                )

                # Update room assignment in ual.json
                self.view.updateUalJson(user, new_room)
                print(f"{user.name} moved to {new_room}: x={new_position[0]}, y={new_position[1]}")

            time.sleep(random.randint(2, 5))  # Wait before moving again


    def getInitialPositionForRoom(self, room):
        base_positions = {
            "Room A": (300, 600),
            "Room C": (250, 250),
            "Room D": (600, 250),
            "Room B": (600, 550)
        }

        base_x, base_y = base_positions.get(room, (0, 0))
        count = self.room_counts.get(room, 0)  # ✅ Get current user count for this room

        # Offset users to spread them out
        offset_x = (count % 3) * 30
        offset_y = (count // 3) * 30

        new_position = (base_x + offset_x, base_y + offset_y)

        # ✅ Update room count
        self.room_counts[room] = count + 1

        return new_position


if __name__ == "__main__":
    model = Model()
    view = View(windowSize=900, squareSize=600)
    controller = Controller(model, view)
    view.mainloop()