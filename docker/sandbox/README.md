#Sandbox
To run the sandbox locally do the following:
1. Go to docker/sandbox directory.
2. Build the docker image of the sandbox:
```
docker build .
```
You will see logs with id of the built image.
3. Make the docker image run on  default 8080 port:
```
docker run image_id
```
or on custom port:
```
docker run -p 7000:8080 image_id
```
4. Now you can make your requests, i.e.:
```
http://localhost:7000/routing-reliability
```

#Wiremock:
You can read about Wiremock stubbing on this site: http://wiremock.org/docs/stubbing/
