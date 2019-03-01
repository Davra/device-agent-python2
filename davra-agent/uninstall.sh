#!/bin/bash

echo "Starting UN-install procedure for Davra Agent"
cd `dirname $0`

installationDir="/usr/bin/davra"

if [[ $(id -u) -ne 0 ]]; then
    echo "Please run as root" 
    exit 1 
fi


systemctl stop davra_agent.service
systemctl disable davra_agent.service

rm /lib/systemd/system/davra_agent.service 

systemctl daemon-reload


mv "${installationDir}/davra_agent.py" "${installationDir}/davra_agent_UNINSTALLED.py"

logFile="/var/log/davra_agent.log"
mv "${logFile}" "${logFile}_UNINSTALLED"

echo "Finished UN-install procedure for Davra Agent"
