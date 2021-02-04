const { MongoClient } = require("mongodb");

const uri =
  "mongodb://rapd:shallowkillerbeg@164.54.212.169,164.54.212.172,164.54.212.170/rapd?replicaSet=rs0";
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