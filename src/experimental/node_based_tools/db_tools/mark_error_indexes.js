/*
 * Look into MongoDB and create groups property containing group_id
 * for users that are lacking.
 * This will enable RAPD2 to be used by these users
 */
const { MongoClient } = require("mongodb");
const config = require("./config");

// const remoteUri = config.auth_conn;
// const remoteClient = new MongoClient(remoteUri, {useUnifiedTopology: true});

const rapdUri = config.new_control_conn;
const rapdClient = new MongoClient(rapdUri, {useUnifiedTopology: true});

async function run() {
  try {
  
    await rapdClient.connect();
    const rapdDatabase = rapdClient.db('rapd');
    const resultsCollection = rapdDatabase.collection('results');
    const indexesCollection = rapdDatabase.collection('mx_index_results');

    // Query for all sessions
    const query = {"results.labelit_results.status":"FAILED"};
    const projection = {"process":1}
    const indexesCursor = indexesCollection.find(query, projection);    
    
    let counter = 0;
    while (await indexesCursor.hasNext()) {
      counter += 1;
      const result = await indexesCursor.next();
      indexesCursor.close();
      console.log(result)

      await resultsCollection.findOneAndUpdate({_id:result.process.result_id}, {$set:{status:101}});

    }
  } finally {
    // Ensures that the client will close when you finish/error
    await rapdClient.close()
  }
}
run().catch(console.dir);
