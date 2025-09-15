#!/bin/bash
searchString="Pinged out from styx"
file="output.log"
while true
do
if grep -Fxq "$searchString" $file
   then
           echo "pkill -f bitbotd && ./bitbotd 2>&1 | tee output.log" 
   else 
           echo "String not found in $file"
fi
sleep 10m
done
