/*
 * Migrate collections to a new server
 * This will enable RAPD2 to be used by these users
 */
const { MongoClient } = require("mongodb");
const config = require("./config");

const client = new MongoClient(config.new_control_conn, {useUnifiedTopology: true});

async function run() {
  
  try {
    await client.connect();
    const db = client.db('rapd');

    const cursor = db.images.aggregate([
      {$group:{_id:"$fullname", count:{"$sum":1}}},
      {$limit:1},
    ])
    
    await cursor.hasNext();
    const record = await cursor.next();
    console.log(record)

    
  } finally {
    // Ensures that the client will close when you finish/error
    await new_client.close();
  }
}

  run().catch(console.dir);