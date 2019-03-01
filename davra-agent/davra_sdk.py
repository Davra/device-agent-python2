# Davra SDK for Device Applications
# Import this SDK to assist writing Device Applications
# so they can communicate with the Davra Agent, running on the device
#
import os
import time
import requests
import json 
from pprint import pprint
import sys
from datetime import datetime
# Use MQTT to communicate with the davra device agent
import paho.mqtt.client as mqtt


# CONFIG
mqttBrokerAgentHost = '127.0.0.1' # Where is the MQTT broker running on the agent
installationDir = "/usr/bin/davra"
agentConfigFile = installationDir + "/config.json"
# END CONFIG


# Load configuration if it exists
conf = {}
def loadConfiguration():
    global conf
    try:
        if(os.path.isfile(agentConfigFile) is True):
            with open(agentConfigFile) as data_file:
                conf = json.load(data_file)
    except Exception as e:
        print('ERROR: Cannot read config file ' + agentConfigFile + ":" + str(e))
loadConfiguration()


###########################   Utilities


def getMilliSecondsSinceEpoch():
    return int((datetime.now() - datetime(1970,1,1)).total_seconds() * 1000)


# Is a string valid json
def isJson(myjson):
    try:
        json_object = json.loads(myjson)
    except ValueError, e:
        return False
    return True


# Log a message
def log(log_msg):
    log_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = str(log_msg)
    try:
        print(log_time + ": " + log_msg)  # Echo to stdout
    except:
        print "Error: Logging to file failed"


###########################   Connect to the MQTT Broker running on device

# The callback for when the client receives a CONNACK response from the broker on the device.
def mqttOnConnectDevice(client, userdata, flags, resultCode):
    if(resultCode != 0):
        log("Mqtt Device Broker: Connected with result code " + str(resultCode))
    else:
        log('MQTT Device Broker: Could not connect. userdata:' + str(userdata) + str(flags))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("/agent")
    return 


# The callback for when a PUBLISH message is received from the broker on device.
def mqttOnMessageDevice(client, userdata, msg):
    payload = str(msg.payload)
    log('Mqtt Device Broker: Received Mqtt message: ' + payload)
    if(isJson(payload)):
        processMessageFromAgentToApp(json.loads(payload))
    return
    
# Setup the MQTT client talking to the broker on the device    
clientOfDevice = None
if(len(mqttBrokerAgentHost) > 3):
    clientOfDevice = mqtt.Client()
    clientOfDevice.on_connect = mqttOnConnectDevice
    clientOfDevice.on_message = mqttOnMessageDevice
    # MQTT on device may be optionally restricted to only username of device uuid
    if("mqttRestrictions" in conf and "username" in conf["mqttRestrictions"]):
        clientOfDevice.username_pw_set(conf["UUID"], conf["apiToken"])
        log('MQTT: Will connect using password to broker running on device' + conf["UUID"])
    log('Starting to connect to MQTT broker running on device ' + mqttBrokerAgentHost)
    clientOfDevice.connect(mqttBrokerAgentHost)
    clientOfDevice.loop_start() # Starts another thread to monitor incoming messages
    time.sleep(2)
else:
    log('No MQTT broker configured on device')


###########################   Send Messages from Device Application to Device Agent

# msg should be a json object
def sendMessageFromAppToAgent(msg):
    log('sendMessageFromAppToAgent: sending msg: ' + str(msg))
    clientOfDevice.publish('/agent', json.dumps(msg))


def connectToAgent(applicationName):
    log('connectToAgent: announce application to agent: ' + str(applicationName))
    sendMessageFromAppToAgent({ "connectToAgent": applicationName })


def registerCapability(capabilityName, capabilityDetails):
    log('registerCapability: announce application capability to agent: ' + str(capabilityName))
    sendMessageFromAppToAgent({ "registerCapability": capabilityName, "capabilityDetails": capabilityDetails})


###########################   Process Messages from Device Agent to Device Application

# These messages may arrive by mqtt from agent or api calls or flat file comms
# msg should be a json object
def processMessageFromAgentToApp(msg):
    log('processMessageFromAgentToApp: incoming msg: ' + str(msg))
    #if(msg.has_key("agent-action-sampleApp-reportDiskStatus")):
    #if(msg.has_key("runFunctionOnAgent")):
    #    functionName = msg["runFunctionOnAgent"]
    #    functionParameterValues = msg["functionParameterValues"] if msg.has_key("functionParameterValues") else {}
    #    runFunction(functionName, functionParameterValues)

