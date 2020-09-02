#!/bin/bash
do docker run
for i in {1..10}
    do docker run —name docker-nginx$i -P -d nginx
    sleep 3
done