const { MongoClient } = require("mongodb");

const config = require("./config");

const uri = config.control_conn;
const client = new MongoClient(uri, {useUnifiedTopology: true});

async function run() {
  try {
    await client.connect();
    const database = client.db('rapd');
    const chunksCollection = database.collection('fs.chunks');
    const filesCollection = database.collection('fs.files');
  
    // Query for chunks
    const query = {n:0};
    const options = {projection:{'data':false}}
    const chunksCursor = chunksCollection.find(query, options);    
    
    let counter = 0;
    while (await chunksCursor.hasNext()) {
      counter += 1;
      const chunk = await chunksCursor.next();
      const file = await filesCollection.findOne({_id:chunk.files_id});
      if (! file) {
        console.log("CHUNK");
        console.log(chunk);
        console.log("MISSING FILE");
        console.log(file);
      } else {
        console.log(counter);  
        // process.stdout.write('.');
      }
    }
  } finally {
    // Ensures that the client will close when you finish/error
    await client.close();
  }
  }
  run().catch(console.dir);