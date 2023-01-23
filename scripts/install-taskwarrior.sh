#!/usr/bin/env bash
apt-key adv --recv-keys --keyserver keyserver.ubuntu.com 6B05F25D762E3157
apt-get update
sudo apt-get install taskwarrior || sudo apt-get install task
