# geofence broker

## description

Mainly built for internal SVV usage. The purpose is to periodically get a collection
of road objects of a certain type that contains a `POLYGON`. In this case we are using
that polygon as a _"geofence"_ which we cache / store internally.


All _"geofences"_ that are added, changed or deleted shall be forwarded to a custom AMQP server
for further processing.


Simple, yeah?


## Example

**Help:**
```bash
$ python client.py --help
```

**configuration file:**
```yaml
$ cat config.yml
 # config file
broker_url: amqps://url.to.my.amqp.server.com:5671
sender: send_queue
receiver: recv_queue
ssl_keyfile: certs/my_priv.key
ssl_certfile: certs/my_crt.cert
username: user1
password: VerySecret
verbose: true
# Timeout in seconds. How often to check for new geofences from NVDB
timeout: 300
```

**Run with config file:**
```bash
$ python -conf ./config.yml
```

## Technology?

Python ofcourse ;)


## Build and start docker container

1. First create your config file: `config.yml`
2. Then build the docker container
```bash
$ sudo docker-compose build
```
3. Start the container (in background - if not, skip the '-d')
```bash
$ sudo docker-compose up -d
```
4. Inspect the logs by running
```bash
$ sudo docker-compose logs
```

