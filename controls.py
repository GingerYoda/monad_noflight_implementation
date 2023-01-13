"""
Oskari Perikangas
oskari.perikangas@tuni.fi

Contains different functions and utility functions to control planes.
"""
import math
MAX_TURN = 20


def count_distance(coord_1, coord_2):
    """
    Counts euclidean distance between two coordinates.
    :param coord_1: starting point.
    :param coord_2: end point.
    :return: distance between points.
    """
    return math.sqrt(pow(coord_2['x'] - coord_1['x'], 2) + pow(coord_2['y'] - coord_1['y'], 2))


def count_discourse(aircraft_course, landing_direction):
    """
    Simply calculates how much aircrafts course is off the target.
    :param aircraft_course: course of the aircraft.
    :param landing_direction: landing direction on the destination airport.
    :return: difference between two courses.
    """
    return landing_direction-aircraft_course


def count_angle(aircraft_pos, destination_pos):
    """
    Count angle between two points.
    :param aircraft_pos: Position of the aircraft.
    :param destination_pos: Position of the destination of the aircraft.
    :return: angle between the two given points.
    """

    y = destination_pos['y'] - aircraft_pos['y']
    x = destination_pos['x'] - aircraft_pos['x']

    if y == 0:
        if x >= 0:
            return 0
        else:
            return 180

    if x == 0:
        if y >= 0:
            return 90
        else:
            return 270

    angle = math.degrees(math.atan(y/x))
    if angle < 0:
        angle += 360
    return int(angle)


def count_turning_point(airport, aircraft_speed, discourse):
    """
    Counts point where plane must be aligned with the airports direction.
    :param airport: destination airport of the plane.
    :param aircraft_speed: speed of the aircraft.
    :param discourse: difference between planes course and the airport.
    :return: int x, int y: coordinates of the turning point.
    """
    # TODO: clean up and add/test support for arbitrary directions.
    direction = airport['direction']

    turning_space = abs(discourse) // 20 * aircraft_speed
    # Going right
    if direction <= 90 or direction >= 270:
        x = airport['position']['x'] - turning_space
    # Going left
    else:
        x = airport['position']['x'] + turning_space

    # Exception handling for tangent.
    if direction == 90:
        y = airport['position']['y'] - turning_space
        x = airport['position']['x']
    elif direction == 270:
        y = airport['position']['y'] + turning_space
        x = airport['position']['x']

    else:
        y = math.tan(math.radians(direction)) * x
    if int(y) == 0:
        y = airport['position']['y']
    return x, y


def steer_aircraft(aircraft, airport):
    """
    Steers aircraft towards the airport.
    :param aircraft: controlled aircraft.
    :param airport: destination of the aircraft.
    :return: discourse: how much plane must be turned. Returns None if no turning needs to be done.
    """
    aircraft_pos = aircraft['position']
    aircraft_dir = aircraft['direction']
    discourse = count_discourse(aircraft_dir, airport['direction'])
    position_angle = count_angle(aircraft_pos, airport['position'])

    # Check if the plane is already on the right course.
    if discourse == 0 and position_angle == airport['direction']:
        return

    # Count point where plane must be aligned to the airports direction.
    x_tp, y_tp = count_turning_point(airport, aircraft['speed'], discourse)
    turning_point = {'x': x_tp, 'y': y_tp}
    distance_from_tp = count_distance(aircraft_pos, turning_point)

    if distance_from_tp > aircraft['speed']*2:
        course_to_turning_point = count_angle(aircraft_pos, turning_point)
        discourse = count_discourse(aircraft_dir, course_to_turning_point)
    # Adjust to the turning range of the plane.
    if abs(discourse) > MAX_TURN:
        if discourse < 0:
            discourse = -MAX_TURN
        else:
            discourse = MAX_TURN
    return discourse


def evade(aircraft_one, aircraft_two, min_distance_between):
    """
    First plane makes evading maneuver. Evading should start earlier for better score.
    :param aircraft_one: Aircraft which will be evading.
    :param aircraft_two: Aircfrat which is evaded.
    :param min_distance_between: Minimum distance between planes before crashing.
    :return: evading course for aircraft_one
    """
    x_evade = aircraft_two['position']['x'] - math.cos(math.radians(aircraft_two['direction'])) * min_distance_between
    y_evade = aircraft_two['position']['y'] - math.sin(math.radians(aircraft_two['direction'])) * min_distance_between
    evading_angle = count_angle(aircraft_one['position'], {'x': x_evade, 'y': y_evade})
    new_course = count_discourse(aircraft_one['direction'], evading_angle)
    return new_course


def collision_detection(aircraft_one, aircraft_two):
    """
    Detects if given aircrafts are about crash.
    :param aircraft_one: first aircraft
    :param aircraft_two: second aircraft
    :return: None if there will be no crashing, else returns evading course for aircraft_one.
    """
    direction_one = aircraft_one['direction']
    direction_two = aircraft_two['direction']
    angle_between = abs(direction_two - direction_one)
    # Check if collision is even possible.
    if angle_between == 0 or angle_between == 180:
        return
    else:
        distance_between_planes = count_distance(aircraft_two['position'], aircraft_one['position'])
        min_distance_between = aircraft_one['collisionRadius'] + aircraft_two['collisionRadius'] + aircraft_one['speed'] + aircraft_two['speed']
        if distance_between_planes > min_distance_between:
            return
        evasion = evade(aircraft_one, aircraft_two, min_distance_between)
        if abs(evasion) > MAX_TURN:
            if evasion < 0:
                evasion = -MAX_TURN
            else:
                evasion = MAX_TURN
        return evasion
