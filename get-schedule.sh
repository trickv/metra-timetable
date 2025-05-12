#!/usr/bin/env bash

set -u
set -e 

rm -rf metra-gtfs-new
mkdir -p metra-gtfs-new
cd metra-gtfs-new
wget https://schedules.metrarail.com/gtfs/schedule.zip
unzip schedule.zip
cd ..
rm -rf metra-gtfs
mv metra-gtfs-new metra-gtfs
