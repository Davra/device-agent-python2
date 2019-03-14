# Establish connection with the Davra server
# Save the location of the Davra server to config.json for use by other programs
# Optionally: Create this device on the Davra server
#
import time, requests, os.path
from requests.auth import HTTPBasicAuth
import json 
from pprint import pprint
import sys
from datetime import datetime
import davra_lib as comDavra


configFilename = comDavra.agentConfigFile

currentDirectory = comDavra.runCommandWithTimeout('pwd', 10)[1]
print("Running setup of Davra Agent " + comDavra.davraAgentVersion)
print("Received arguments: ")
print(sys.argv)
print("Current directory: " + currentDirectory)


# Load configuration if it already exists
comDavra.loadConfiguration()


# Set the security on the mqqt broker on this device so connections
# can only be made by using the device UUID and API token
def setDeviceMqttBrokerSecurity():
    if("mqttRestrictions" in comDavra.conf and "localhost" in comDavra.conf["mqttRestrictions"]):
        comDavra.runCommandWithTimeout('sudo echo "listener 1883 localhost" > /etc/mosquitto/conf.d/localhost.conf', 5)
        comDavra.runCommandWithTimeout('sudo systemctl stop mosquitto', 10)
        comDavra.runCommandWithTimeout('sudo systemctl start mosquitto', 10)
    if("mqttRestrictions" in comDavra.conf and "username" in comDavra.conf["mqttRestrictions"]):
        # Set security on the MQTT broker so clients connect as username:device uuid, password: API key
        comDavra.log("Setting security on device mqtt broker")
        comDavra.runCommandWithTimeout('sudo echo "allow_anonymous false" > /etc/mosquitto/conf.d/davra.conf', 5)
        comDavra.runCommandWithTimeout('sudo echo "password_file /etc/mosquitto/conf.d/davra.txt" >> /etc/mosquitto/conf.d/davra.conf', 5)
        comDavra.runCommandWithTimeout('sudo touch /etc/mosquitto/conf.d/davra.txt', 5)
        comDavra.runCommandWithTimeout('sudo mosquitto_passwd -b /etc/mosquitto/conf.d/davra.txt ' + comDavra.conf['UUID'] \
        + ' ' + comDavra.conf['apiToken'], 5) 
        comDavra.runCommandWithTimeout('sudo systemctl stop mosquitto', 10)
        comDavra.runCommandWithTimeout('sudo systemctl start mosquitto', 10)
    return 

if("--secure-mqtt" in sys.argv):
    setDeviceMqttBrokerSecurity()
    exit(0)



if('server' not in comDavra.conf):
    # No server known yet. Was it passed as a command line param?
    for index, arg in enumerate(sys.argv):
        if arg in ['--server'] and len(sys.argv) > index + 1:
            comDavra.conf['server'] = sys.argv[index + 1]
            with open(configFilename, 'w') as outfile:
                json.dump(comDavra.conf, outfile, indent=4)
            break
    # No configuration info exists so get it from user and save
    comDavra.conf['server'] = raw_input("Server location? ")
    with open(configFilename, 'w') as outfile:
        json.dump(comDavra.conf, outfile, indent=4)

    
print("Establishing connection to Davra server... ")
# Confirm can reach the server
r = requests.get(comDavra.conf['server'])
if(r.status_code == 200):
    #print(r.content)
    print("Ok, can reach " + comDavra.conf['server'])
else:
    print("Cannot reach server. " + comDavra.conf['server'] + ' Response: ' + str(r.status_code))

# Create this device on server
#if('deviceName' not in comDavra.conf):        
#    comDavra.conf['deviceName'] = raw_input("Name for this device? ")
#    serverUsername = raw_input('Username:')
#    serverPassword = raw_input('Password:')
#    contents = '{ "name": "' + comDavra.conf['deviceName'] + '", '\
#        + '"serialNumber": "' + comDavra.conf['deviceName'] + '" }'
#    headers = {'Accept' : 'application/json', 'Content-Type' : 'application/json'}
#    #print('Sending data to server: ' + contents)
#    r = requests.post(comDavra.conf['server'] + '/api/v1/devices', data=contents, \
#        headers=headers, auth=HTTPBasicAuth(serverUsername, serverPassword))
#    if(r.status_code == 200):
#        print(r.content)
#        comDavra.conf['UUID'] = json.loads(r.content)[0]['UUID']
#        print("Device created on server. New UUID: " + comDavra.conf['UUID'])
#        # Save device info to config file
#        with open(configFilename, 'w') as outfile:
#            json.dump(comDavra.conf, outfile, indent=4)
#    else:
#        print(r.content)
#        print("Cannot reach server. " + str(r.status_code))
#        sys.exit()


# Requires the API token of a device
if('apiToken' not in comDavra.conf):
    # No api token known yet. Was it passed as a command line param?
    for index, arg in enumerate(sys.argv):
        if arg in ['--token'] and len(sys.argv) > index + 1:
            comDavra.conf['apiToken'] = sys.argv[index + 1]
            with open(configFilename, 'w') as outfile:
                json.dump(comDavra.conf, outfile, indent=4)
            break
    # No configuration UUID exists so get it from user and save
    comDavra.conf['apiToken'] = raw_input("API Token? ")
    with open(configFilename, 'w') as outfile:
        json.dump(comDavra.conf, outfile, indent=4)


# Confirm the details supplied can make authenticated API call to server
# Find the UUID of this device
headers = {'Accept': 'application/json', 'Authorization': 'Bearer ' + comDavra.conf['apiToken']}
print('Confirming connection to server')
r = comDavra.httpGet(comDavra.conf['server'] + '/user')
if(r.status_code == 200):
    print(r.content)
    comDavra.conf['UUID'] = json.loads(r.content)['UUID']
    print("Device confirmed on server")
    # Save device info to config file
    with open(configFilename, 'w') as outfile:
        json.dump(comDavra.conf, outfile, indent=4)
else:
    print(r.content)
    print("Cannot reach server. " + str(r.status_code))
    sys.exit()


# heartbeatInterval is how many seconds between calling home
if('heartbeatInterval' not in comDavra.conf):
    comDavra.upsertConfigurationItem('heartbeatInterval', 600)


# scriptMaxTime is how many seconds between a script can run for before timing out
if('scriptMaxTime' not in comDavra.conf):
    comDavra.upsertConfigurationItem('scriptMaxTime', 600)


# agentRepository is where the artifacts for the agent are published
# should also have /build_version.txt to indicate the latest release version
if('agentRepository' not in comDavra.conf):
    comDavra.upsertConfigurationItem('agentRepository', 'downloads.davra.com/agents/davra-agent-python2-master')

# What is the host of the MQTT Broker on Davra Server
if('mqttBrokerServerHost' not in comDavra.conf):
    # No configuration exists for mqtt
    # Make assumptions for the cloud based scenarios
    if ('davra.com' in comDavra.conf['server']):
        comDavra.upsertConfigurationItem('mqttBrokerServerHost', 'mqtt.davra.com')
    elif ('eemlive.com' in comDavra.conf['server']):
        comDavra.upsertConfigurationItem('mqttBrokerServerHost', 'mqtt.eemlive.com')
    else:
        # Assume the same IP as the Davra server but ignore http or port definition
        mqttBroker = comDavra.conf['server'].replace("http://", "").replace("https://", "").split(":")[0]
        print('Setting mqttBroker ' + str(mqttBroker))
        comDavra.upsertConfigurationItem('mqttBrokerServerHost', mqttBroker)


# Reload configuration inside library
comDavra.loadConfiguration()


# Create necessary metrics on server    
comDavra.createMetricOnServer('cpu', '%', 'CPU usage')
comDavra.createMetricOnServer('uptime', 's', 'Time since reboot')
comDavra.createMetricOnServer('ram', '%', 'RAM usage')


def getWanIpAddress():
    # Returns the current WAN IP address, as calls to internet server perceive it
    r = comDavra.httpGet('http://whatismyip.akamai.com/')
    if (r.status_code == 200):
        return r.content
    return ''

# Estimate GPS
def getLatLong():
    # Use IP address to guess location from geoIp
    wanIpAddress = getWanIpAddress()
    # Make call to GeoIP server to find out location from WAN IP
    comDavra.log('Getting Lat/Long estimate ')
    r = comDavra.httpGet('http://ip-api.com/json')
    if(r.status_code == 200):
        jsonContent = json.loads(r.content)
        latitude = jsonContent['lat']
        longitude = jsonContent['lon']
        return (latitude, longitude)
    else:
        comDavra.log("Cannot reach GeoIp server. " + str(r.status_code))
        return (0,0)

(piLatitude, piLongitude) = getLatLong()
comDavra.log('Latitude/Longitude estimated as ' + str(piLatitude) + ", " + str(piLongitude))


# Confirm MQTT Broker on agent
if(comDavra.checkIsAgentMqttBrokerInstalled() == False):
    comDavra.log('MQTT Broker not installed')
    comDavra.upsertConfigurationItem("mqttBrokerAgentHost", '')
else:
    comDavra.log('MQTT Broker installed and running')
    comDavra.upsertConfigurationItem("mqttBrokerAgentHost", '127.0.0.1')
    # To enable advanced security on mqtt requiring usernames for connections
    #comDavra.upsertConfigurationItem("mqttRestrictions", 'localhost,username')
    # To enable basic security which is only localhost connections to mqtt
    comDavra.upsertConfigurationItem("mqttRestrictions", 'localhost')
    setDeviceMqttBrokerSecurity()
    
    

# Send an event to the server to inform it of the installation
dataToSend = { 
    "UUID": comDavra.conf['UUID'],
    "name": "davra.agent.installed",
    "value": {
        "deviceConfig": comDavra.conf
    },
    "msg_type": "event",
    "latitude": piLatitude,
    "longitude": piLongitude
}
# Inform user of the overall data being sent for a single metric
comDavra.log('Sending data to server: ' + comDavra.conf['server'])
comDavra.log(json.dumps(dataToSend, indent=4))
comDavra.sendDataToServer(dataToSend)



# Install as a service so it continually runs
if('service' not in comDavra.conf):
    # By default, install as a service
    print('Using root permissions to install as service')
    comDavra.runCommandWithTimeout('cp ./davra_agent.service /lib/systemd/system/davra_agent.service', 10)
    comDavra.runCommandWithTimeout('chmod 644 /lib/systemd/system/davra_agent.service', 10)
    comDavra.runCommandWithTimeout('systemctl daemon-reload', 10)
    comDavra.runCommandWithTimeout('systemctl enable davra_agent.service', 10)
    comDavra.runCommandWithTimeout('systemctl start davra_agent.service', 10)
    comDavra.runCommandWithTimeout('systemctl restart davra_agent.service', 10)
    with open(configFilename, 'w') as outfile:
        json.dump(comDavra.conf, outfile, indent=4)
else:
    if(comDavra.conf['service'] == 'y' or comDavra.conf['service'] =='Y'):
        if("--no-service-restart" not in sys.argv):
            print('Using root permissions to restart service')
            comDavra.runCommandWithTimeout('systemctl stop davra_agent.service', 10)
            comDavra.runCommandWithTimeout('systemctl daemon-reload', 10)
            comDavra.runCommandWithTimeout('systemctl start davra_agent.service', 10)
            comDavra.runCommandWithTimeout('systemctl restart davra_agent.service', 10)
        else:
            print("Will not restart the service now. Please do so manually")


print("Finished setup.")

