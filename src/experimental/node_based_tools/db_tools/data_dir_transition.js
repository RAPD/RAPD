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

    const cursor = collection.find({'data_root_dir':null})
    
    let counter = 0;
    while (await cursor.hasNext()) {
      counter += 1;
      const record = await cursor.next();
      if (record.data_dir) {
        console.log(counter);
        ret = await collection.updateOne({_id:record._id},{$set:{data_root_dir:record.data_dir}});
      }
      
    }
  } finally {
    // Ensures that the client will close when you finish/error
    await client.close();
  }
}

  run().catch(console.dir);