import requests
import socketio
import json
import urllib3
import ssl
from websocket import create_connection
import sys
import termios
import tty
import select

# from pynput import keyboard

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
print("You really wanna do this...?")
default_user = "test"
default_email = "test@example.com"
default_password = "wert2345"

username = input("Enter your username: (default: test)")
email = input("Enter your email: (default: test@example.com)")
password = input("Enter your password: (default: wert2345)")

if not username:
    username = default_user
if not email:
    email = default_email
if not password:
    password = default_password

login_url = "https://localhost/api/v1/users/accounts/login/"
login_payload = {"username": username, "email": email, "password": password}
access_token_name = "ft_transcendence-app-auth"

print("\n arggg... authenticating")
session = requests.Session()
auth_response = session.post(login_url, json=login_payload, verify=False)
if auth_response.status_code == 200:
    cookies = session.cookies.get_dict()
else:
    print("Login failed! Touch some grass")
    exit()

if access_token_name not in cookies:
    print("Login failed! Touch some grass")
    exit()

cookie_header = "; ".join([f"{key}={value}" for key, value in cookies.items()])

game_matching_url = "wss://localhost/api/ws/matchmaking/"

game_url = "wss://localhost/api/ws/game/"

sslopt = {
    "cert_reqs": ssl.CERT_NONE,
    "check_hostname": False,
}

headers = [
    f"Cookie: {cookie_header}",
    # "Origin: https://example.com",  # Adjust origin URL as necessary
]

request_match = {"type": "request_match", "gamemode": "1v1"}
request_match_json = json.dumps(request_match)

print(f"Cookie: {cookie_header}")
print("trying to queue for a game...")
try:
    ws = create_connection(game_matching_url, header=headers, sslopt=sslopt)
    print("Connected to the server for matchmaking")
    ws.send(request_match_json)
    print("Matching...")
    while True:
        response = ws.recv()
        print(f"Received: {response}")
        response_dict = json.loads(response)
        if response_dict["type"] == "match_found":
            print("Match found!")
            break
except Exception as e:
    print("Error: ", e)
    exit()

gameId = response_dict["game_id"]

print("\nConnecting to WebSocket...")

from engineio.client import Client as EngineIOClient

sio = socketio.Client(ssl_verify=False)

is_second_player = False

connected = False

@sio.event(namespace="/api/game")
def connect():
    global connected
    connected = True
    print("Connection established")


@sio.event(namespace="/api/game")
def disconnect():
    global connected
    connected = False
    print("Disconnected from server")


@sio.event(namespace="/api/game")
def message(data):
    if data.type == "secondPlayer":
        global is_second_player
        is_second_player = True


ws_header = {
    "Cookie": cookie_header,
}

sio.connect(
    f"wss://localhost/api/game?gameId={gameId}&gameType=PVP",
    headers=ws_header,
    namespaces="/api/game",
    socketio_path="/api/game/socket.io",
    transports="websocket",
)

def send_keypress(key, pressed):
    if connected:  # Only emit if connected
        # print(f"Sending key press: {key} - {pressed}")
        sio.emit("keyPress", {"key": key, "pressed": pressed, "who": is_second_player}, namespace='/api/game')
    # else:
        # print(f"Connection lost! Cannot send keypress: {key} - {pressed}")
        
def get_single_char():
    fd = sys.stdin.fileno()
    rlist, _, _ = select.select([fd], [], [], 0.05)
    if rlist:
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
    return None

from time import sleep
import time

class Timer:
    def __init__(self, duration):
        self.duration = duration
        self.time_left = duration
        self.last_time = time.time()
        self.expired = False

    def update(self):
        current_time = time.time()
        # Update the remaining time based on the elapsed time
        elapsed_time = current_time - self.last_time
        self.time_left -= elapsed_time
        self.last_time = current_time

        # If time_left reaches zero, the timer has expired
        if self.time_left <= 0:
            self.expired = True
            self.time_left = 0

    def reset(self):
        self.time_left = self.duration
        self.expired = False
        self.last_time = time.time()

    def is_expired(self):
        return self.expired
    

import curses

def main(stdscr):
    
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.timeout(100)
    
    timer = Timer(0.1)
    paddle_moving_left = False
    paddle_moving_right = False
    
    while True:
        key = stdscr.getch()
        
        timer.update()
        
        if key == ord('a') or key == curses.KEY_LEFT:
            paddle_moving_left = True
            paddle_moving_right = False
            timer.reset()  # Reset the timer when a key is pressed
        elif key == ord('d') or key == curses.KEY_RIGHT:
            paddle_moving_right = True
            paddle_moving_left = False
            timer.reset()  # Reset the timer when a key is pressed
        elif key == ord('q') :
            print("Exiting...")
            break  # Quit the game loop
        if paddle_moving_left:
            send_keypress('A', True)
        else:
            send_keypress('A', False)
        if paddle_moving_right:
            send_keypress('D', True)
        else:
            send_keypress('D', False)
        if timer.is_expired():
            paddle_moving_left = False
            paddle_moving_right = False
            send_keypress('A', False)
            send_keypress('D', False)
        stdscr.refresh()
        sleep(0.05)


# def key_pressed(key, key_state):
#     if key == False and key_state == True:
#         return True


# def key_released(key, key_state):
#     if key == True and key_state == False:
#         return True


# def on_press(key):
#     print(f"{key} pressed")
#     if key == keyboard.Key.left:
#         key = "A"
#     elif key == keyboard.Key.right:
#         key = "D"
#     sio.emit("keyPress", {"key": key, "pressed": True, "who": is_second_player})


# def on_release(key):
#     print(f"{key} pressed")
#     if key == keyboard.Key.left:
#         key = "A"
#     elif key == keyboard.Key.right:
#         key = "D"
#     sio.emit("keyPress", {"key": key, "pressed": False, "who": is_second_player})


# with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
#     listener.join()
# import keyboard  # using module keyboard

# while True:  # making a loop
#     try:  # used try so that if user pressed other than the given key error will not be shown
#         if keyboard.is_pressed("q"):  # if key 'q' is pressed
#             print("You Pressed A Key!")
#             break  # finishing the loop
#     except:
#         break  # if user pressed a key other than the given key the loop will break

if __name__ == "__main__":
    curses.wrapper(main)
    
    
    
    sio.wait()
