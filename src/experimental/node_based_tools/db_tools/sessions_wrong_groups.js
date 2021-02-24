/*
 * Look into MongoDB and create groups property containing group_id
 * for users that are lacking.
 * This will enable RAPD2 to be used by these users
 */
const { MongoClient } = require("mongodb");
const config = require("./config");

const remoteUri = config.auth_conn;
const remoteClient = new MongoClient(remoteUri, {useUnifiedTopology: true});

const rapdUri = config.new_control_conn;
const rapdClient = new MongoClient(rapdUri, {useUnifiedTopology: true});

async function run() {
  try {
    await remoteClient.connect();
    const remoteDatabase = remoteClient.db('remote');
    const groupsCollection = remoteDatabase.collection('groups');
  
    await rapdClient.connect();
    const rapdDatabase = rapdClient.db('rapd');
    const sessionsCollection = rapdDatabase.collection('sessions');

    // Query for all sessions
    const query = {};
    const options = {}
    const sessionsCursor = sessionsCollection.find(query, options);    
    
    let counter = 0;
    while (await sessionsCursor.hasNext()) {
      counter += 1;
      const session = await sessionsCursor.next();
      console.log(session);

      let group = await groupsCollection.findOne({_id:session.group});
      console.log(group);

      if (group === null) {
        console.log("!!!!!!!!!!");
        sessionsCursor.close();
      }

    //   await usersCollection.findOneAndUpdate({_id:user._id}, {$set:{groups:[user.group_id]}});
    }
  } finally {
    // Ensures that the client will close when you finish/error
    await remoteClient.close();
    await rapdClient.close()
  }
  }
  run().catch(console.dir);