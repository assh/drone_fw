from dronekit import connect, VehicleMode, LocationGlobalRelative, APIException, Command
import time
import socket
import exceptions
import math
import argparse
import psycopg2
from pymavlink import mavutil
import os

manual = ['M000006']
auto = []
next_date = None
next_time = None


def connectDrone():

    parser = argparse.ArgumentParser(description='commands')
    parser.add_argument('--connect')
    args = parser.parse_args()

    connection_string = args.connect
    #if not connection_string:
    #    import dronekit_sitl
    #    sitl = dronekit_sitl.start_default()
    #    connection_string = sitl.connection_string()

    vehicle = connect(connection_string, baud=57600, wait_ready=True)
    return vehicle


def takeoff(targetH):
    while vehicle.is_armable != True:
        print("Waiting for Vehicle to become Armable")
        time.sleep(1)
    print("Vehicle is now Armable")

    vehicle.mode = VehicleMode("GUIDED")

    while vehicle.mode != 'GUIDED':
        print("Waiting for drone to enter GUIDED flight mode")
        time.sleep(1)

    print("Vehicle is now in GUIDED mode")

    vehicle.armed = True

    while vehicle.armed == False:
        print("Waiting for vehicle to become armed")
        time.sleep(1)
    print("Vehicle is armed")

    vehicle.simple_takeoff(targetH)

    while True:
        print("Current Altitude: %d" %
              vehicle.location.global_relative_frame.alt)
        if vehicle.location.global_relative_frame.alt >= 0.95*targetH:
            break
        time.sleep(1)
    print("Target Altitude reached")
    return None


def connectDB():
    con = psycopg2.connect(database=os.environ.get('DB_NAME'), user=os.environ.get('DB_USER'), password=os.environ.get('DB_PASSWORD'),
                           host=os.environ.get('DB_HOST'), port=os.environ.get('DB_PORT'))

    curr = con.cursor()
    return curr


def executeMission(coords,mode,):
    vehicle = connectDrone()
    wphome = vehicle.location.global_relative_frame


# vehicle = connectDrone()
#cursor = connectDB()
#exe = """SELECT mission_id,date, "time", launch_mode FROM public.accounts_mission WHERE vda = 'UAE-DR-0001' AND mission_status = 'On Schedule' ORDER BY date asc, "time" asc """
# cursor.execute(exe)
#tmplist = cursor.fetchall()
# for i in tmplist:
#    if (i[3] == 'AUTO'):
#        auto.append(i[0])
#    else:
#        manual.append(i[0])
#print(auto, manual)
# vehicle.wait_ready('autopilot_version')
# print(vehicle.is_armable)
# while vehicle.is_armable != True :
# print("waiting for Arming")
# time.sleep(1)
# print("Vehicle now armable")
# vehicle.mode = VehicleMode("GUIDED")
# while vehicle.mode != 'GUIDED':
# print("Waiting")
# time.sleep(1)
# print(vehicle.mode)
# vehicle.close()
while True:
    if (len(manual) == 0 and len(auto) == 0):
        print("Wating")
        time.sleep(3)

    elif (len(manual) != 0):

        mission = manual.pop(0)
        coordinates = []
        cursor = connectDB()
        exe = """SELECT * FROM public.accounts_mission WHERE mission_id = '""" + \
            str(mission) + "'"
        print(exe)
        cursor.execute(exe)
        tmplist = cursor.fetchall()[0]
        # print(len(tmplist))
        mode = tmplist[1]
        for i in range(18, 26, 1):
            coordinates.append(tmplist[i])
            pass
        print(coordinates[0])

    elif (len(auto) != 0):
        pass
