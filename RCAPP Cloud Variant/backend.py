import credentials
from ringcentral import *
import time
import datetime

def respTest(platform):
    resp = platform.get('/restapi/v1.0/account/~/presence',
    {
    'detailedTelephonyState' : True
    })
    return resp.response()

def rcLogin():
    sdk = SDK(credentials.rc_CLIENTID, credentials.rc_SECRETKEY, credentials.rc_PRODSERVER)

    platform = sdk.platform()

    try:
        platform.login(credentials.rc_PHONENUMBER, credentials.rc_EXTENSION, credentials.rc_PW)
    except Exception as e:
        with open(r'officestatus.log', 'a+') as file:
            file.write(f'An exception "{e}" occured when attempting to log in to RingCentral.\n')

    return platform


def get_status(platform):
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
    resp = platform.put(f"/restapi/v1.0/account/{accountId}/extension/{extensionId}/presence", body)
    return (resp.response())


# Take All Calls Body
tac_body = {
      "userStatus": "Available",
      "dndStatus": 'TakeAllCalls',
      "allowSeeMyPresence": True,
      "ringOnMonitoredCall": False,
      "pickUpCallsOnHold": True,
   }

# Do Not Accept Deparment Calls Body
dna_body = {
      "userStatus": "Busy",
      "dndStatus": 'DoNotAcceptDepartmentCalls',
      "allowSeeMyPresence": True,
      "ringOnMonitoredCall": False,
      "pickUpCallsOnHold": True,
   }
'''my_statuses = get_status(rcLogin())
for x in my_statuses:
    if x[1] == '314':
        r = update_status(rcLogin(), '~',f'{x[0]}', dna_body)
        print(r)'''