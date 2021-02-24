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
    const collection = db.collection('sessions');

    const cursor = collection.aggregate([
      {$group:{_id:"$data_root_dir", count:{"$sum":1}}},
      {$match:{count:{$gt:1}}}
    ])
    let counter = 0;
    while (await cursor.hasNext()) {
        counter += 1;
        const record = await cursor.next();
        console.log(counter, record);

        const rCursor = collection.find({data_root_dir:record.data_root_dir});
        

    }
  } finally {
    // Ensures that the client will close when you finish/error
    await client.close();
  }
}

  run().catch(console.dir);