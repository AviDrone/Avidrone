#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    SECONDARY SEARCH
"""
from __future__ import print_function

# Set up option parsing to get connection string
import argparse
import datetime
import logging as log
import math
import time

import drone
import dronekit_sitl
import util
from dronekit import LocationGlobal, VehicleMode, connect
from transceiver import Transceiver

Avidrone = drone.vehicle
search = util.Search()

def run(transceiver):
    log.info("-- SECONDARY SEARCH --")
    signal_found = False
    uav_pos = [0,0,0]
    beacon_pos = [0,0,0]
    if util.IS_TEST:
        mock_transceiver = search.read_transceiver(uav_pos,beacon_pos)  # mock transceiver
    else:
        transceiver = Transceiver()
    search.start()
    gps_window = util.WINDOW_SIZE
    while Avidrone.mode.name == "GUIDED":
        log.info(transceiver.direction, ", ", transceiver.distance)

        if transceiver.direction < 2:  # Turn left
            log.info("-- Turning left")
            util.Search.condition_yaw(-util.DEGREES, True)

        elif transceiver.direction > 2:  # Turn right
            log.info("-- Turning right")
            util.Search.condition_yaw(util.DEGREES, True)

        elif transceiver.direction == 2:  # Continue forward
            log.info("-- Continuing forward")
            gps_window.add_point(search.get_global_pos(), transceiver.distance)
            if (
                gps_window.get_minimum_index() == ((gps_window.window_size - 1) / 2)
                and len(gps_window.gps_points) == gps_window.window_size
            ):

                # If the minimum is the center point of the gps_window we need to go
                # back to that location, Min index = middle

                util.Search.simple_goto_wait(
                    gps_window.gps_points[int((gps_window.window_size - 1) / 2)]
                )

                if gps_window.distance[2] <= util.LAND_THRESHOLD:
                    log.info("-- Landing")
                    Avidrone.mode = VehicleMode("LAND")
                    signal_found = True
 
                if signal_found:
                    current_time = datetime.datetime.now()
                    print("--- SIGNAL FOUND --- ", f"-- time: {current_time}")

                else:
                    log.info("Not close, continuing")
                    gps_window.purge_gps_window()

            elif (
                gps_window.get_minimum_index() == (gps_window.window_size - 1)
                and len(gps_window.gps_points) == gps_window.window_size
            ):

                # If the minimum data point is the last one in the array,
                log.info("too far in the wrong direction")

                util.Search.condition_yaw(180, True)
                util.Search.simple_goto_wait(
                    gps_window.gps_points[gps_window.window_size - 1]
                )
                gps_window.purge_gps_window()

            elif gps_window.get_minimum_index() == 0:
                # If the minimum data point is in the first index,
                log.info("continue forward")
                util.Search.go_to_location(
                    util.MAGNITUDE, Avidrone.attitude.yaw, Avidrone
                )

            else:
                log.info(f"Did not find signal at altitude: {util.ALTITUDE}")
                log.info("Climbing...")
                util.Search.go_to_location(
                    util.MAGNITUDE, Avidrone.attitude.yaw, Avidrone
                )
        time.sleep(2)


if __name__ == "__main__":
    uav_pos = [2, 2, 2]  # TODO replace this with actual positions
    beacon_pos = [1, 1, 1]  # TODO replace this with actual positions
    search = util.Search()
    transceiver = search.read_transceiver(uav_pos, beacon_pos)
    run(transceiver)
