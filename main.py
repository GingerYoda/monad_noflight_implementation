"""
Oskari Perikangas
oskari.perikangas@tuni.fi

Source code is from https://github.com/monadoy/rekry2022-sample. I have implemented myself generate commands function.
"""

from dotenv import dotenv_values
import requests
import webbrowser
import websocket
import json
import time
import controls

FRONTEND_BASE = "noflight.monad.fi"
BACKEND_BASE = "noflight.monad.fi/backend"

game_id = None


def normalize_heading(heading):
    """Normalize any angle to 0-359"""
    return round(heading + 360) % 360


def on_message(ws: websocket.WebSocketApp, message):
    [action, payload] = json.loads(message)

    if action != "game-instance":
        print([action, payload])
        return

     # New game tick arrived!
    game_state = json.loads(payload["gameState"])
    commands = generate_commands(game_state)

    time.sleep(0.1)
    ws.send(json.dumps(["run-command", {"gameId": game_id, "payload": commands}]))


def on_error(ws: websocket.WebSocketApp, error):
    print(error)


def on_open(ws: websocket.WebSocketApp):
    print("OPENED")
    ws.send(json.dumps(["sub-game", {"id": game_id}]))


def on_close(ws, close_status_code, close_msg):
    print("CLOSED")


# Change this to your own implementation
def generate_commands(game_state):
    commands = []
    evading_planes = []
    for aircraft in game_state["aircrafts"]:
        # Collision detection and evading if there are more than one aircrafts.
        if len(game_state["aircrafts"]) > 1:
            for aircraft_two in game_state["aircrafts"]:
                if aircraft['name'] == aircraft_two['name'] or aircraft_two['id'] in evading_planes:
                    continue
                colliding = controls.collision_detection(aircraft, aircraft_two)
                if colliding is not None:
                    new_dir = normalize_heading(aircraft['direction'] + colliding)
                    if new_dir == aircraft['direction']:
                        break
                    commands.append(f"HEAD {aircraft['id']} {new_dir}")
                    plane_id = aircraft['id']
                    evading_planes.append(plane_id)
                    break

        # Basic controls if no evading is needed.
        if aircraft['id'] not in evading_planes:
            destination = aircraft['destination']
            for airport in game_state["airports"]:
                if airport['name'] == destination:
                    command = controls.steer_aircraft(aircraft, airport)
                    if command is None:
                        break
                    new_dir = normalize_heading(aircraft['direction'] + command)
                    if new_dir == aircraft['direction']:
                        break
                    commands.append(f"HEAD {aircraft['id']} {new_dir}")
                    break
    return commands


def main():
    config = dotenv_values()
    res = requests.post(
        f"https://{BACKEND_BASE}/api/levels/{config['LEVEL_ID']}",
        headers={
            "Authorization": config["TOKEN"]
        })

    if not res.ok:
        print(f"Couldn't create game: {res.status_code} - {res.text}")
        return

    game_instance = res.json()

    global game_id
    game_id = game_instance["entityId"]

    url = f"https://{FRONTEND_BASE}/?id={game_id}"
    print(f"Game at {url}")
    webbrowser.open(url, new=2)
    time.sleep(2)

    ws = websocket.WebSocketApp(
        f"wss://{BACKEND_BASE}/{config['TOKEN']}/", on_message=on_message, on_open=on_open, on_close=on_close, on_error=on_error)
    ws.run_forever()


if __name__ == "__main__":
    main()