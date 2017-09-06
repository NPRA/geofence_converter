# geofence broker

## description

Mainly built for internal SVV usage. The purpose is to periodically get a collection
of road objects of a certain type that contains a `POLYGON`. In this case we are using
that polygon as a _"geofence"_ which we cache / store internally.


All _"geofences"_ that are added, changed or deleted shall be forwarded to a custom AMQP server
for further processing.


Simple, yeah?


## Technology?

Python ofcourse ;)
