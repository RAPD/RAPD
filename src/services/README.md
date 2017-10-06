## Running Services in Docker
Docker is the preferred way to run services for RAPD. This is just because it makes it a lot simpler for installation and cross-platform use.

#### MongDB with persistence
Make a directory to store data in (I have used `/Users/frankmurphy/workspace/data/mongo` on my Mac)  

```shell
run -d -p 27017:27017 --name mongo -v /Users/frankmurphy/workspace/data/mongo:/data/db mongo --storageEngine wiredTiger
```

#### Redis with persistence
```shell
docker run --name redis -d redis -p 6379:6379 redis-server --appendonly yes
```

#### REST and Websocket server
These run on port 3000 by default
Build
```shell
cd rapd/src/restful
docker build -t rapd_rest .
```

Run
```shell
docker run --name rapd_rest --link redis:redis --link mongo:mongo -p 3000:3000 rapd_rest
```
