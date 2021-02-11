/*
 * Migrate collections to a new server
 * This will enable RAPD2 to be used by these users
 */
const { MongoClient } = require("mongodb");
const config = require("./config");

const old_client = new MongoClient(config.control_conn, {useUnifiedTopology: true});
const new_client = new MongoClient(config.new_control_conn, {useUnifiedTopology: true});

async function run() {
  
  try {
    await old_client.connect();
    await new_client.connect();

    const fromDB = old_client.db('rapd');
    const toDB = new_client.db('rapd');


    // // Sessions
    // const fromDB = old_client.db('rapd');
    // const toDB = new_client.db('rapd');

    // const fromSessions = fromDB.collection('sessions');
    // const toSessions = toDB.collection('sessions');

    // const fromSessionsCursor = fromSessions.find();
    // let counter = 0;
    // while (await fromSessionsCursor.hasNext()) {
    //   counter += 1;
    //   console.log(counter);
    //   const session = await fromSessionsCursor.next();
    //   // console.log(session);
    //   let new_session = await toSessions.findOne({_id:session._id});
    //   // console.log(new_session);
    //   if (new_session === null) {
    //     new_session = await toSessions.insertOne(session);
    //     // console.log(new_session.result);
    //   }
    // }

    // Results
    // ['results'].forEach((collectionName) => {
    const collectionName = "results";
    console.log(collectionName);
    
      const fromCollection = fromDB.collection(collectionName);
      const toCollection = toDB.collection(collectionName);

      const fromCursor = fromCollection.find();
      let counter = 0;
      while (await fromCursor.hasNext()) {
        counter += 1;
        console.log(counter);
        const record = await fromCursor.next();
        // console.log(record);
        let new_record = await toCollection.findOne({_id:record._id});
        // console.log(new_record);
        if (new_record === null) {
          new_record = await toCollection.insertOne(record);
          // console.log(new_record.result);
        }
      }
    // });
    
  } finally {
    // Ensures that the client will close when you finish/error
    await old_client.close();
    await new_client.close();
  }
}

  run().catch(console.dir);