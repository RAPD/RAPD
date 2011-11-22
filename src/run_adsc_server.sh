#!/bin/bash

#Quick script to run rapd_adscserver forever

nohup python rapd_adscserver.py > /dev/null 2>& 1 &
