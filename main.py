from dronekit import connect, VehicleMode, LocationGlobalRelative, APIException, Command
import time
import socket
import exceptions
import math
import argparse
import psycopg2
from pymavlink import mavutil
import os

manual = []#['M001207']
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
    


def connectDB():
    con = psycopg2.connect(database=os.environ.get('DB_NAME'), user=os.environ.get('DB_USER'), password=os.environ.get('DB_PASSWORD'),
                           host=os.environ.get('DB_HOST'), port=os.environ.get('DB_PORT'))

    #con = psycopg2.connect(database='postgres', user='postgres', password='123456',
                       #host='127.0.0.1', port='5432')
    curr = con.cursor()
    return curr


def executeMission(coords,mode):
    #vehicle = connectDrone()
    wphome = vehicle.location.global_relative_frame
    if (mode == '2'):

        cmd0 = Command(0,0,0,mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,mavutil.mavlink.MAV_CMD_DO_SET_CAM_TRIGG_DIST,0,0,15,0,0,0,0,0,0)
        cmd01 = Command(0,0,0,mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,mavutil.mavlink.MAV_CMD_DO_SET_CAM_TRIGG_DIST,0,0,0,0,0,0,0,0,0)
        cmd1 = Command(0,0,0,mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,0,0,0,0,0,0,wphome.lat,wphome.lon,wphome.alt)
        cmd2 = Command(0,0,0,mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,0,0,0,0,0,0,coords[0],coords[1],wphome.alt)
        cmd3 = Command(0,0,0,mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,0,0,0,0,0,0,coords[2],coords[3],wphome.alt)
        cmd4 = Command(0,0,0,mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,0,0,0,0,0,0,coords[4],coords[5],wphome.alt)
        cmd5 = Command(0,0,0,mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,0,0,0,0,0,0,coords[6],coords[7],wphome.alt)
        cmd6 = Command(0,0,0,mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH,0,0,0,0,0,0,0,0,0)
        cmds = vehicle.commands
        cmds.download()
        cmds.wait_ready()

        cmds.clear()
        cmds.add(cmd1)
        cmds.add(cmd2)
        cmds.add(cmd0)
        cmds.add(cmd3)
        cmds.add(cmd4)
        cmds.add(cmd5)
        cmds.add(cmd2)
        cmds.add(cmd01)
        cmds.add(cmd6)

        cmds.upload()

    takeoff(15)
    vehicle.mode = VehicleMode("AUTO")
    while vehicle.mode!='AUTO':
        time.sleep(0.2)
    while vehicle.location.global_relative_frame.alt >2:
        print("Mission executing")
        time.sleep(2)
    

con = psycopg2.connect(database=os.environ.get('DB_NAME'), user=os.environ.get('DB_USER'), password=os.environ.get('DB_PASSWORD'),
                           host=os.environ.get('DB_HOST'), port=os.environ.get('DB_PORT'))
cursor = con.cursor()


while True:
    exe = """SELECT mission FROM public.accounts_launch WHERE drone = 'UAE-DR-0001'"""
    cursor.execute(exe)
    try:
        
        tmplist = cursor.fetchall()[0][0]
        print(tmplist)
        manual.append(tmplist)
    except:
        print("No MANUAL Launches")
        

    if (len(manual) == 0 and len(auto) == 0):
        print("Waiting")
        time.sleep(10)

    elif (len(manual) != 0):
        vehicle = connectDrone()
        print(vehicle.battery)
        mission = manual.pop(0)
        print(mission)
        #coordinates=[25.351153,55.388386,25.351231,55.388788,25.350955,55.388976,25.350873,55.388606]
        coordinates = []
        coord = []
        #cursor = connectDB()
        exe = """SELECT * FROM public.accounts_mission WHERE mission_id = '""" + \
            str(mission) + "'"
        print(exe)
        cursor.execute(exe)
        tmplist = cursor.fetchall()[0]
        #print(len(tmplist))
        mode = tmplist[1]
        print(mode)
        for i in range(18, 26, 1):
            
            coordinates.append(tmplist[i])
        for j in range(8):
            coord.append(coordinates[j])
        print(coord)
        executeMission(coord,mode)
        exe = """UPDATE public.accounts_mission SET launch_now = false, mission_status='Complete' WHERE mission_id = '""" + str(mission) + "'"
        print(exe)
        cursor.execute(exe)
        exe = """DELETE FROM public.accounts_launch WHERE mission = '""" + str(mission) + "'"
        print(exe)
        cursor.execute(exe)
        con.commit()
    elif (len(auto) != 0):
        pass

    
