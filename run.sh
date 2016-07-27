export LC_ALL=C  #本人的机子远程登录
mongod -f /db2/conf/config_server.conf
mongod -f /db2/conf/rs0.conf
mongod -f /db2/conf/rs1.conf
mongos -f /db2/conf/mongos.conf #没有 mongos 的服务器不需要这条