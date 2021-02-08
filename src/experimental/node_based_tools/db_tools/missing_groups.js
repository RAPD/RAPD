/*
 * Look into MongoDB and create groups property containing group_id
 * for users that are lacking.
 * This will enable RAPD2 to be used by these users
 */
const { MongoClient } = require("mongodb");
const config = require("./config");

const uri = config.auth_conn;
const client = new MongoClient(uri, {useUnifiedTopology: true});

async function run() {
  try {
    await client.connect();
    const database = client.db('remote');
    const usersCollection = database.collection('users');
  
    // Query for users without groups
    const query = {groups:{$exists:false}};
    const options = {}
    const usersCursor = usersCollection.find(query, options);    
    
    let counter = 0;
    while (await usersCursor.hasNext()) {
      counter += 1;
      const user = await usersCursor.next();
      console.log(user);
      await usersCollection.findOneAndUpdate({_id:user._id}, {$set:{groups:[user.group_id]}});
    }
  } finally {
    // Ensures that the client will close when you finish/error
    await client.close();
  }
  }
  run().catch(console.dir);