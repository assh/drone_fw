from dronekit import connect, VehicleMode, LocationGlobalRelative, APIException, Command
import time
import socket
import exceptions
import math
from math import radians, cos, sin, asin, sqrt
import argparse
import psycopg2
from pymavlink import mavutil
import os
from datetime import datetime, date

manual = []#['M001207']
auto = []
next_date = None
next_time = None
next_mission = 0

def time2second(t):
    tmp = str(t).split(':')
    second = int(tmp[0])*3600+int(tmp[1])*60+int(tmp[2])
    return second


def getDistance(lat1,lon1,lat2,lon2):
    R = 6372.8 
    dLat = radians(lat2 - lat1)
    dLon = radians(lon2 - lon1)
    lat1 = radians(lat1)
    lat2 = radians(lat2)

    a = sin(dLat/2)**2 + cos(lat1)*cos(lat2)*sin(dLon/2)**2
    c = 2*asin(sqrt(a))

    return R * c

def getLawn(lawn):
    nlst=[]
    wlst = []
    count = 4
    k = 1

    def getCoords(lst):
        print lst[0][0],',',lst[0][1]
        print lst[1][0],',',lst[1][1]
        print lst[len(lst)-2][0],',',lst[len(lst)-2][1]
        print lst[len(lst)-1][0],',',lst[len(lst)-1][1]
        print "New Coordinates"
        for i in range(2,len(lst)-2):
            print lst[i][0],',',lst[i][1]

    def sortCoord(home,lawn):
        temp=1000000
        for i in range(4):
            dist=getDistance(home[0],home[1],lawn[i][0],lawn[i][1])
            if (dist<=temp):
                temp = dist
                temlist=lawn[i]
        lawn.remove(temlist)
        nlst.append(temlist)

        for i in range(3):
            temp = 1000000
            dist=getDistance(nlst[0][0],nlst[0][1],lawn[i][0],lawn[i][1])
            if (dist<=temp):
                temp = dist
                temlist=lawn[i]
        lawn.remove(temlist)
        nlst.append(temlist)


    nlst.append(lawn[0])
    nlst.append(lawn[1])
    
    for i in range(count-1):
        perc = (i+1.00)/count
        dlatt1 = perc*(lawn[3][0]-lawn[0][0])
        dlont1 = perc*(lawn[3][1]-lawn[0][1])
        dlatt2 = perc*(lawn[2][0]-lawn[1][0])
        dlont2 = perc*(lawn[2][1]-lawn[1][1])
        a = lawn[0][0]+dlatt1
        b = lawn[0][1]+dlont1
        x = lawn[1][0]+dlatt2
        y = lawn[1][1]+dlont2
        if (k == 1):
            nlst.append([x,y])
            nlst.append([a,b])
        else:
            nlst.append([a,b])
            nlst.append([x,y])
        k = k*-1

    if (count%2 == 0):
        nlst.append(lawn[3])
        nlst.append(lawn[2])
    else:
        nlst.append(lawn[2])
        nlst.append(lawn[3])
    getCoords(nlst)
    return nlst

    


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
    elif (mode == '3'):
        nnlist = []
        while (len(coords)>0):
            tmp = []
            tmp.append(coords.pop(0))
            tmp.append(coords.pop(0))
            nnlist.append(tmp)
        mylist = getLawn(nnlist)

        cmdlist = []
        tmpcoord = mylist.pop(0)
        cmdlist.append(Command(0,0,0,mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,0,0,0,0,0,0,wphome.lat,wphome.lon,wphome.alt))
        cmdlist.append(Command(0,0,0,mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,0,0,0,0,0,0,tmpcoord[0],tmpcoord[1],wphome.alt))
        cmdlist.append(Command(0,0,0,mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,mavutil.mavlink.MAV_CMD_DO_SET_CAM_TRIGG_DIST,0,0,15,0,0,0,0,0,0))

        for j in mylist:
            c1 = j[0]
            c2 = j[1]
            cmdlist.append(Command(0,0,0,mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,0,0,0,0,0,0,c1,c2,wphome.alt))

        cmdlist.append(Command(0,0,0,mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,mavutil.mavlink.MAV_CMD_DO_SET_CAM_TRIGG_DIST,0,0,0,0,0,0,0,0,0))   
        cmdlist.append(Command(0,0,0,mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH,0,0,0,0,0,0,0,0,0))

        cmds = vehicle.commands
        cmds.download()
        cmds.wait_ready()
        cmds.clear()

        for j in cmdlist:
            cmds.add(j)

        cmds.upload()
    elif (mode == '1'):

        cmd0 = Command(0,0,0,mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,mavutil.mavlink.MAV_CMD_DO_SET_CAM_TRIGG_DIST,0,0,15,0,0,0,0,0,0)
        cmd01 = Command(0,0,0,mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,mavutil.mavlink.MAV_CMD_DO_SET_CAM_TRIGG_DIST,0,0,0,0,0,0,0,0,0)
        cmd1 = Command(0,0,0,mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,0,0,0,0,0,0,wphome.lat,wphome.lon,wphome.alt)
        cmd2 = Command(0,0,0,mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,mavutil.mavlink.MAV_CMD_NAV_LOITER_TURNS,0,0,1,0,0,0,coords[0],coords[1],wphome.alt)
        cmd3 = Command(0,0,0,mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,mavutil.mavlink.MAV_CMD_NAV_LOITER_TURNS,0,0,1,0,0,0,coords[2],coords[3],wphome.alt)
        cmd4 = Command(0,0,0,mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,mavutil.mavlink.MAV_CMD_NAV_LOITER_TURNS,0,0,1,0,0,0,coords[4],coords[5],wphome.alt)
        cmd5 = Command(0,0,0,mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,mavutil.mavlink.MAV_CMD_NAV_LOITER_TURNS,0,0,1,0,0,0,coords[6],coords[7],wphome.alt)
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
    

    exe = """SELECT mode_type, mission_id, date, "time" FROM public.accounts_mission WHERE launch_mode = 'AUTO' and vda = 'UAE-DR-0001' and mission_status = 'On Schedule' ORDER BY date,"time" """
    cursor.execute(exe)
    try:
        auto = []
        tmplist = cursor.fetchall()
        auto.extend(tmplist)
        if (next_mission in auto):
            auto.remove(next_mission)
        
    except:
        print("No AUTO Launches")


    try:
        if (next_mission == 0):
            next_mission = auto.pop(0)
            print(next_mission)
            next_date = next_mission[2]
            next_time = next_mission[3]
            ntmi = time2second(next_time)-600
        
    except:
        print("Some Error")


    currtime = datetime.now().strftime("%H:%M:%S")
    ctms = time2second(currtime)
    

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
            coord.append(float(coordinates[j]))
        print(coord)
        executeMission(coord,mode)
        exe = """UPDATE public.accounts_mission SET launch_now = false, mission_status='Complete' WHERE mission_id = '""" + str(mission) + "'"
        print(exe)
        cursor.execute(exe)
        exe = """DELETE FROM public.accounts_launch WHERE mission = '""" + str(mission) + "'"
        print(exe)
        cursor.execute(exe)
        con.commit()



    elif (next_mission != 0 and date.today() == next_date and ntmi < ctms):
        #vehicle = connectDrone()
        #print(vehicle.battery)
        
        mission = next_mission[1]
        print(mission)
        coordinates = []
        coord = []
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
            coord.append(float(coordinates[j]))
        print(coord)
        #executeMission(coord,mode)
        exe = """UPDATE public.accounts_mission SET mission_status='Complete' WHERE mission_id = '""" + str(mission) + "'"
        print(exe)
        cursor.execute(exe)
        con.commit()
        next_mission = 0
        

    
