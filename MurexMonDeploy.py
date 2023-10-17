#!/usr/bin/env python
###################################################################
# Author:          Mohamed Mounir ee51486                          #
# Description: Monitors Management Script                          #
# Guide: Provide a list of Monitors as parmeter 1 or provide it to #
#        the prompt message                                        #
# Last Updated:01/06/2020                                          #
###################################################################
import os
import sys
import xml.etree.ElementTree as ET
import datetime


class Monitor:
    def __init__(self, conf):
        self.name = conf.replace(".conf", "").rstrip("\n")
        self.conf = conf
        self.agent = None

    def deploy(self, retries=0):
        print("Deploying monitor (" + self.name + ")...")
        stream = os.popen("fteDeployCM.sh %s" % self.name)
        output = stream.read()
        if "not found! Maybe not staged?" in output:
            print("Error: Can't find this Monitor in Staging: " + self.name)
            print("Failed: Skipping Monitor " + self.name)
            return False, "Not Found"
        else:
            if "BFGCL0251I" in output:
                print("Info: Monitor " + self.name + " was Deployed Successfully.")
                return True, "Success"
            elif "BFGCL0253W" in output:
                agent = self.getAgent()
                if not agent.ping():
                    print("Failed: Skipping Monitor " + self.name)
                    return False, "Failed Ping"
                else:
                    if retries > 0:
                        print("Info: Agent " + agent.name + " responded to Ping, will retry for " + str(
                            retries) + " time(S)")
                    while retries > 0:
                        stream = os.popen("fteDeployCM.sh %s" % self.name)
                        output = stream.read()
                        if "BFGCL0251I" in output:
                            print("Info: Monitor " + self.name + " was Deployed Successfully.")
                            return True, "Success"
                        else:
                            retries -= 1
                    print("Agent responded to Ping but not Deploy commands")
                    print("Failed: Skipping Monitor " + self.name)
                    return False, "Failed Command, Ping Success"
            else:
                errList = [line for line in output.split('\n') if "BFG" in line]
                print("Error: Deployment has encountered the below errors...")
                print(errList)
                print("Failed: Skipping Monitor " + self.name)
                return False, "New Error"

   
    def checkStatus(self):
        # CheckStatus will return a list, as the monitor might be deployed on several agents
        print("Info: Checking Monitor (%s) Status..." % self.name)
        stream = os.popen("fteListMonitors -v -mn %s" % self.name)
        output = stream.read()
        if "BFGCL0242W" in output:
            print("Error: This Monitor is not deployed on any Agent.")
            return ['Not deployed']
        elif "Monitor Information" in output:
            print("Info: Below are a list of Monitor statuses.")
            output = [line.split(':')[1].strip() for line in output.split('\n') if "Status" in line]
            print(output)
            return output

    def checkStatusAG(self, agent):
        # CheckStatusAG will check the monitor status on a specific Agent so it will only return one string value
        print("Info: Checking Monitor (%s) Status on Agent(%s)..." % (self.name, agent))
        stream = os.popen("fteListMonitors -v -mn %s -ma %s" % (self.name, agent))
        output = stream.read()
        if "BFGCL0242W" in output:
            print("Error: This Monitor is not deployed on Agent(%s)." % agent)
            return "Not deployed"
        elif "Monitor Information" in output:
            print("Info: Monitor Status on Agent %s :" % agent)
            output = [line.split(':')[1].strip() for line in output.split('\n') if "Status" in line][0]
            print(output)
            return output

    def retry(self, r, ag):
        # This Function will take the agent keep redeploying and checking if the monitor is started for r times.
        x = 1
        while x <= r:
            print("retry: %s" % x)
            self.deploy()
            if self.checkStatusAG(ag) == "Started":
                print("Success: After %s deployment retries Monitor is now Started" % x)
                return True
            else:
                x += 1
        print("Error: After %s deployment retries Monitor is still Stopped (Failed)" % x)
        print("Failed: Skipping Monitor %s" % self.name)
        return False

    def getAgent(self):
        # Finding Staging Repo
        if os.path.exists("/data/mqfte/config/fteCM/staged/IT"):
            stPath = "/data/mqfte/config/fteCM/staged/IT"
        elif os.path.exists("/data/mqfte/config/fteCM/staged/QSU"):
            stPath = "/data/mqfte/config/fteCM/staged/QSU"
        elif os.path.exists("/data/mqfte/config/fteCM/staged/PROD"):
            stPath = "/data/mqfte/config/fteCM/staged/PROD"
        else:
            return "Cannot find Staging repo to get Agent"
        # Parsing the XML and getting the agent
        tree = ET.parse(stPath + '/' + self.name + '.xml')
        agent = tree.find('agent')
        if agent is not None:
            self.agent = agent.text
            return Agent(agent.text)
        else:
            return None

    def __str__(self):
        return self.named


class Agent:
    def __init__(self, name):
        self.name = name
        if name[0:1] == "XN" and name[3:4] == "BR":
            self.QM = name.split('.')[0].split('_')[0]
        else:
            self.QM = name.split('.')[1]

    def getStatus(self):
        stream = os.popen("fteShowAgentDetails %s" % self.name)
        output = stream.read().split('\n')
        self.QM = output[output.index('Queue Manager Information:') + 1].split(':')[1].strip()
        return output[output.index('Agent Availability Information:') + 1].split(':')[1].strip()

    def ping(self):
        print("Info: Agent " + self.name + " seems not to respond to Deploy command, Pinging Agent...")
        stream = os.popen("ftePingAgent -m %s %s" % (self.QM, self.name))
        output = stream.read()
        if "BFGCL0213I" in output:
            print("Info: Agent " + self.name + " has responded to ping")
            return True
        elif "BFGCL0214I" in output:
            print("Error: Agent " + self.name + " not responding to ping.")
            return False


# Deploy Monitors in Bulk from a list a file.
def listDeploy(ls, retry=3):
    # Create a list DS containing Monitors objects
    MonList = []
    listFile = open(ls, "r")
    for line in listFile:
        MonList.append(Monitor(line))
    listFile.close()
    # Start Operation, Main Loop
    sFile = open('/tmp/ListDeploy_%s.csv' % datetime.datetime.now().strftime("%d%m%Y_%H%M%S"), 'w')
    sFile.write("Monitor" + " : " + "DeployStatus" + "\n")
    for mon in MonList:
        print("\n")
        deployStatus = mon.deploy(retry)
        if deployStatus[0]:
            agent = mon.getAgent().name
            if mon.checkStatusAG(agent) == "Started":
                print("Success: Monitor is now Started")
                sFile.write(mon.name + " : " + "Started" + "\n")
            else:
                if not mon.retry(retry, agent):
                    sFile.write(mon.name + " : " + "Monitor Deployed but Stopped" + "\n")
        else:
            sFile.write(mon.name + " : " + deployStatus[1] + "\n")
    sFile.close()


# First call of the script, Main function
def main():
    # Manage User Inputs
    if len(sys.argv) < 2:
        listPath = raw_input("Please enter the path to the list file containing the monitors: ")
    else:
        listPath = str(sys.argv[1])
    if not os.path.isfile(listPath):
        print("This file does not exist")
        exit()
    # Call Functions
    return listDeploy(listPath)


if __name__ == "__main__":
    main()

