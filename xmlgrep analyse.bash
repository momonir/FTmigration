#!/bin/bash
###################################################################
#Author: 	  Mohamed Mounir ee51486                              #
#Description: Script to extract Application Monitors parameters   #
#			  from staged xmls                                    #
#Guide: Parameter(1) is App / Parameter(2) is Env                 #
#Last Updated:17/07/2019                                          #
################################################################### 

#Variables
ServerTemp="/tmp"
App=$1
ENV=$2
Edate=$(date +"%m-%d-%y")
#Getting a list of Monitors in Scope of execution
ls /data/mqfte/config/fteCM/staged/$ENV | grep $App"\." > $ServerTemp/MonList.txt

#Extract data from Monitors
while read line
 do
	Name=$(xml_grep 'name' $line --text_only)
	SourceAgent=$(xml_grep 'sourceAgent' $line|grep agent=|sed 's/.*agent="\(.*\)".*/\1/')
	SourceDirectory=$(xml_grep 'directory' $line --text_only)
	Pattern=$(xml_grep 'pattern' $line --text_only)
	Overwrite=$(xml_grep 'destination' $line|grep exist=|sed 's/.*exist="\(.*\)" .*/\1/')
	Leave=$(xml_grep 'source' $line|grep disposition=|sed 's/.*disposition="\(.*\)" r.*/\1/')
	DestinationAgent=$(xml_grep 'destinationAgent' $line|grep agent=|sed 's/.*agent="\(.*\)".*/\1/')
	DestinationPath=$(xml_grep 'destination' $line --text_only)
	OriginatorHost=$(xml_grep 'hostName' $line --text_only|head -n 1)
	OriginatorUserId=$(xml_grep 'userID' $line --text_only|head -n 1)
	
	echo $Name "|" $SourceAgent "|" $SourcePath "|" $Pattern "|" $Overwrite "|" $Leave "|" $DestinationAgent "|" $DestinationPath "|" $OriginatorHost "|" $OriginatorUserId  >> $ServerTemp/$App'extract'$ENV$Edate'.CSV'
	
done < $ServerTemp/MonList.txt
rm $ServerTemp/MonList.txt
