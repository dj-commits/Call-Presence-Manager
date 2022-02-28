import credentials
from ringcentral import *
import time
import datetime

def respTest(platform):
    # Testing function, checking the response on the Presence API endpoint.
    resp = platform.get('/restapi/v1.0/account/~/presence',
    {
    'detailedTelephonyState' : True
    })
    return resp.response()

def rcLogin():
    # Logs in to RingCentral
    sdk = SDK(credentials.rc_CLIENTID, credentials.rc_SECRETKEY, credentials.rc_PRODSERVER)

    platform = sdk.platform()

    try:
        platform.login(credentials.rc_PHONENUMBER, credentials.rc_EXTENSION, credentials.rc_PW)
    except Exception as e:
        with open(r'officestatus.log', 'a+') as file:
            file.write(f'An exception "{e}" occured when attempting to log in to RingCentral.\n')

    return platform


def get_status(platform):
    # GETS a list of extensions and their call presence
    resp = platform.get('/restapi/v1.0/account/~/presence',
    {
    'detailedTelephonyState' : True
    })
    if resp.response().status_code == 200:
        statuses = []
        for r in resp.json().records:
                try:
                    if int(r.extension.extensionNumber) > 300 and int(r.extension.extensionNumber) < 400:
                        statuses.append([r.extension.id, r.extension.extensionNumber, r.dndStatus, r.presenceStatus])
                except AttributeError:
                    pass           
        return statuses
    return 1
        


def update_status(platform, accountId, extensionId, body):
    # PUTS a new call presence status on an extention
    resp = platform.put(f"/restapi/v1.0/account/{accountId}/extension/{extensionId}/presence", body)
    return (resp.response())


# "Take All Calls" body that is used in the update_status function
tac_body = {
      "userStatus": "Available",
      "dndStatus": 'TakeAllCalls',
      "allowSeeMyPresence": True,
      "ringOnMonitoredCall": False,
      "pickUpCallsOnHold": True,
   }

# "Do Not Accept" body that is used in the update_status function
dna_body = {
      "userStatus": "Busy",
      "dndStatus": 'DoNotAcceptDepartmentCalls',
      "allowSeeMyPresence": True,
      "ringOnMonitoredCall": False,
      "pickUpCallsOnHold": True,
   }