sh.addShard("Shard1ReplSet/shard1:27018")
sh.addShard("Shard2ReplSet/shard2:27018")
db.getSiblingDB("geobase")
db.createCollection("geodata")
sh.enableSharding("geobase")
sh.shardCollection("geobase.geodata",{"fieldA" : "hashed"})