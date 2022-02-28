import pyodbc
import backend
import time
from datetime import datetime
import credentials

# Call Presence Manager created by Donald Jones, 12/2019
# This program checks the Azure hosted OffcieStatus server for changes in status. If a change is detected (4 second polling rate), then an API PUT call is made through the backend.py module to RingCentral to change a user's status. 
# This is only done if applicable (i.e., a user status going from Out to Out-sick will not trigger an API call, but a status going from Out to In/Office will)

status_dict = {'1' : 'In/Office', '2' : 'Out', '3' : 'On-Site', '4' : 'Lunch', '5' : 'With a Customer', 
                '6' : 'Out of Town', '7' : 'Out Sick', '9' : 'Vacation', '8' : 'In/Home', '10' : 'In/Busy'}
inQueueStatuses = [1, 8]

def getOStatus():
    # This tries to return a list of statuses from the OfficeStatus server; a general catch statement is used to exit this function if there are issues connecting to the server.
    try:
        conn = pyodbc.connect(f'{credentials.sql_conn_string}')
        cursor = conn.cursor()
        oStatuses = []
        cursor.execute('''SELECT FirstName, LastName, StatusID, dbo.PhoneNum.Number, dbo.UserDept.DeptID FROM [dbo].[User]
                        INNER JOIN dbo.PhoneNum on [dbo].[User].[UserID]= dbo.PhoneNum.UserID
                        INNER JOIN dbo.UserDept on [dbo].[User].[UserID] = dbo.UserDept.UserID
                        WHERE dbo.UserDept.DeptID = '2' AND dbo.PhoneNum.PhoneTypeID = '1' AND [dbo].[User].IsEnabled <> 0;''')
        for row in cursor:
            oStatuses.append(row)
        cursor.close()
        return oStatuses
    except Exception as e:
        # General catch for any exceptions when connecting to OfficeStatus server
        with open(r'officestatus.log', 'a+') as file:
            file.write(f'Pyodbc encountered an {e} at {datetime.now()}.\n')
            return 0

def checkOStatusChange(oldOStatuses, newOStatuses):
    # This function checks for a difference between two seperate getOStatus calls.
    if oldOStatuses != newOStatuses:
        with open(r'officestatus.log', 'a+') as file:
            file.write(f'OfficeStatus change detected at {datetime.now()}.\nCalling updateRCPresence.\n')
        if updateRCPresence(newOStatuses) == 1:
            with open(r'officestatus.log', 'a+') as file:
                file.write(f'Update successful.\n')
                return 1
        elif updateRCPresence(newOStatuses) == 0:
            with open(r'officestatus.log', 'a+') as file:
                file.write(f'updateRCPresence returned 0, indicating an issue with RingCentral. Returning to main loop.\n')
                return 0
        
    
def updateRCPresence(oStatuses):
    # This function issues the API call to RingCentral to change a users call presence, if a change is detected in "checkOStatusChange".
    try:
        platform = backend.rcLogin()
        rcStatus = backend.get_status(platform)
        #sysnom = 0
        if type(rcStatus) == list:   
            for x in oStatuses:
                for y in rcStatus:
                    if x[3] == y[1]:
                        if x[2] not in inQueueStatuses and y[2] == 'TakeAllCalls':
                            backend.update_status(platform, '~',f'{y[0]}', backend.dna_body)
                            with open(r'officestatus.log', 'a+') as file:
                                file.write(f"Presence changed to unavailable for {x[0]} {x[1]} at {datetime.now()}\n")
                        elif x[2] in inQueueStatuses and y[2] == 'DoNotAcceptDepartmentCalls':
                            backend.update_status(platform, '~', f'{y[0]}', backend.tac_body)
                            with open(r'officestatus.log', 'a+') as file:
                                file.write(f"Presence changed to available for {x[0]} {x[1]} at {datetime.now()}\n")
                        #else:
                            #with open(r'officestatus.log', 'a+') as file:
                                #file.write(f"OfficeStatus update detected for {x[0]} {x[1]}, but Call Queue Status is already up to date in RingCentral\n")
                            #sysnom += 1

        return 1
    except Exception as e:
        with open(r'officestatus.log', 'a+') as file:
            file.write(f"An exception '{e}' occured when attempting to connect to RingCentral at {datetime.now()}. Pausing for 1 minute.\n")
            time.sleep(60)
        return 0

def frkbmb():
    # This function issues an API call that sets everyone to available if communciation is lost  with the OfficeStatus SQL server.
    try:
        platform = backend.rcLogin()
        rcStatus = backend.get_status(platform)
        for y in rcStatus:
            time.sleep(1)
            if y[2] != 'TakeAllCalls':
                backend.update_status(platform, '~', f'{y[0]}', backend.tac_body)
                with open(r'officestatus.log', 'a+') as file:
                    file.write(f"Presence changed to available for {y[1]} at {datetime.now()}\n")
    except Exception as e:
        with open(r'officestatus.log', 'a+') as file:
            file.write(f"An exception '{e}' occured when attempting to connect to RingCentral at {datetime.now()}. Pausing for 1 minute.\n")
            time.sleep(60) 
                   
def updateLoop():
    # Main loop of the script/program. Checks OfficeStatus every 4 seconds for changes, then issues API calls if necessary. 
    # If there are two errors connecting to OfficeStatus, then it issues an immediate "available" API call using frkbmb(). 
    # It manually runs API calls every 60 seconds as a contigency.
    err_count = 0
    catchUP_count = 0
    while True:
        oldOStatuses = getOStatus()
        time.sleep(4)
        newOStatuses = getOStatus()
        if oldOStatuses != 0 or newOStatuses != 0:
            if checkOStatusChange(oldOStatuses, newOStatuses) == 1:
                continue
        else:
            err_count += 1
            if err_count == 2:
                with open(r'officestatus.log', 'a+') as file:
                    file.write(f'Error detected in main loop (Unable to connect to OfficeStatus server). Setting all call queue members to available (if no issues with RingCentralAPI).\n')
                frkbmb()
                err_count = 0
        catchUP_count += 1
        if catchUP_count % 60 == 0:
            updateRCPresence(newOStatuses)
            catchUP_count = 0

if __name__ == '__main__':
    updateLoop()