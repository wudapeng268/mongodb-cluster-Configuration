#mongoDB分片+复制集集群配置文档
所用版本 mongodb 3.2.7
参考文档:http://docs.mongoing.com/manual-zh/tutorial/deploy-shard-cluster.html

本文架构  

|   用途        |          IP               | 端口  |    备注    |      安装路径 | 
|---------|----------------------------|-----|------------|----------------|
|ConfigeServer  |外网 Ip 1/内网 Ip 1  |33000  |  主       |    /db2/config_server|
|               | 外网 Ip 2/内网 Ip 2    | 33000 |          |      /db2/config_server|
|                |外网 Ip 3/内网 Ip 3   | 33000 |          |      /db2/config_server|
|rs0             |外网 Ip 1/内网 Ip 1  | 43000 |  rs0主节点  | /db2/rs0|
|                |外网 Ip 2/内网 Ip 2    | 43000 |  rs0副本节点 | /db2/rs0|
|                |外网 Ip 3/内网 Ip 3   | 43000 |  rs0副本节点 | /db2/rs0|
|rs1             |外网 Ip 1/内网 Ip 1  | 43002 |  rs1主节点  | /db2/rs1|
|                |外网 Ip 2/内网 Ip 2    | 43002 |  rs1副本节点 | /db2/rs1|
|                |外网 Ip 3/内网 Ip 3   | 43002 |  rs1副本节点 | /db2/rs1|
|mongos          |外网 Ip 1/内网 Ip 1  | 53001 |            |  /db2/mongos|
|          |外网 Ip 2/内网 Ip 2    |53001|               |/db2/mongos|
|          |外网 Ip 3/内网 Ip 3    |53001|               |/db2/mongos|

注:IP 说明:前者是外网 IP 后者是内网 IP, 在集群内部配置的时候一定要用内网 IP, 这在下面还会提到

3.2 版本更改:官网文档建议我们配置3台 ConfigServer 这样如果其中的一台挂掉,其他的还能顶上去,接着用

So,我们配置3台 config_server 两个分片 每个分片配置三个复制集,其中外网 Ip 1/内网 Ip 1 是 primary 节点,剩下的两个是 secondary 节点,其实在复制集中,如果主节点挂了,另外两个副本节点会通过心跳检测自动推选出新的主节点.所以上文申明的主节点只是配置的时候的设置.

###下面来说具体的配置
####0.写在前面的话:
为了方便以后复用,我们都是用来配置文件的方式,来保存配置,我们把所有的配置文件都传到/ db2/conf 文件夹中,方便管理,为了隐私,本文的 ip 使用内网 ip1-3 外网 ip1-3代替.

####1.配置 config_server(3台服务器都需要配置)
config_server 的配置文件是 [config_server.conf](./config_server.conf)
首先我们需要把这个文件传到服务器上,路径随便选.
然后执行 `mongod -f /db2/conf/config_server.conf`
正常情况下,我们会看到 端口已经打开,等待连接的提示(ps. 当然是用英语的,大意就是这样了)


三台服务器的 config_server 都后台运行了,我们登录到 config_server 的主服务器 把这三台服务器关联起来.
`mongo 内网 Ip 1:33000`
`rs.initiate( {
   _id: "configReplSet",
   configsvr: true,
   members: [
      { _id: 0, host: "内网 Ip 1:33000" },
      { _id: 1, host: "内网 Ip 2:33000" },
      { _id: 2, host: "内网 Ip 3:33000" }
   ]
} )` 注意:这里要用内网 IP ,外网 IP 之后会出现很奇葩的问题.

####2.配置 mongos
mongons 的配置文件是 [mongos.conf](./mongos.conf)
同样的先上传配置文件
然后执行 `mongos -f /db2/conf/mongos.conf`

####3.配置分片
我们这里用到两个分片,事实上,后期可以再加入分片,只要再重新执行步骤3就可以了.
根据官方文档所说,生产环境中,每个分片建议都是一个复制集.
首先,写好配置文件: [rs0.conf](./rs0.conf) 注意:注意:注意:bindIp 一定要配,而且要配成所启动服务器的内网 ip 否则在添加复制集的时候就没有办法互相连接了
将配置文件分别上传到三台服务器上,并分别执行
`mongod -f /db2/conf/rs0.conf`
这样三个分片就都可以启动了,然后在主服务器(外网 Ip 1)上连接到 mongod上:
`mongo 内网 Ip 1:43000`
然后执行`rs.initiate()`初始化配置
执行`rs.conf()`显示配置,这里我们可以看到控制台显示出 primary 的字样,说明一切正常
之后,添加另外两个复制集
`rs.add("内网 Ip 2:43000")`
`rs.add("内网 Ip 3:43000")`
正常情况都会显示 ok:1
最后用`rs.status()`这条命令来查看配置,可以看到不同的配置集和他们的级别,是 primary 还是 secondary
分片的复制集的配置到这里就结束了
下面向集群中添加这个分片:
如果我们之前把 mongos config_server 关掉的话,现在要重新打开.
然后我们连接到 mongos 终端 命令如下:
`mongo 内网 Ip 1:53001`
然后键入加入分片的命令`sh.addShard("rs0/内网 Ip 1:43000")`
至此,完整的配置一个分片的任务就结束了,后期需要增加分片,只需要重新执行以下这个步骤,修改必要的参数就可以了
这部分的官方文档:http://docs.mongoing.com/manual-zh/tutorial/deploy-replica-set.html

####4.为数据库/集合开启分片
4.1通过 mongo登录到 mongos 终端 `mongo 内网 Ip 1:53001`
4.2使用` sh.enableSharding("<database>") `开启所需要数据库的分片
4.3为集合设置分片.sh.shardCollection`("<database>.<collection>", shard-key-pattern)` 其中 shard-key-pattern 是片键,表示分片的依据,如果集合非空,需要使用 `ensureIndex() `在片键上创建索引.如果集合是空的,MongoDB会在` sh.shardCollection()` 过程中自动创建索引.我们选择_id 作为片键,所以输入命令如下:
`sh.shardCollection("testsharding.testshardtable",{_id: 1})`
片键的选择,需要考虑最频繁的查询字段,比如我们一般都用age 来查询,则片键选择为 age.

####5.测试
为了很快看到结果,我们把chunk 的大小改为1MB(默认是64MB) 方法可以看http://docs.mongoing.com/manual-zh/tutorial/modify-chunk-size-in-sharded-cluster.html
测试程序见 xx.py 注意:因为要看到自动分片,所以数据量不能太小,我们在程序中插入100W 条数据,事实证明还是可以的.
运行结束后,需要登录到 mongos 上,然后,进入到目标数据库中
`db.testshardtable.stats()`
`db.printShardingStatus()`
`db.testshardtable.getShardDistribution()`
上面的几个命令都是查看分片的状态,我们通过第二个命令可以看出数据在逐渐的在两个分片之间迁移,这说明一切成功.成功的效果是这样的:
`mongos> db.printShardingStatus()
--- Sharding Status ---
  sharding version: {
    "_id" : 1,
    "minCompatibleVersion" : 5,
    "currentVersion" : 6,
    "clusterId" : ObjectId("578f5a4a38172faf34f12ff2")
}
  shards:
    {  "_id" : "rs0",  "host" : "rs0/内网 Ip 1:43000,内网 Ip 3:43000,内网 Ip 2:43000" }
    {  "_id" : "rs1",  "host" : "rs1/内网 Ip 1:43002,内网 Ip 3:43002,内网 Ip 2:43002" }
  active mongoses:
    "3.2.7" : 1
  balancer:
    Currently enabled:  yes
    Currently running:  no
    Failed balancer rounds in last 5 attempts:  0
    Migration Results for the last 24 hours:
        60 : Success
  databases:
    {  "_id" : "testsharding",  "primary" : "rs0",  "partitioned" : true }
        testsharding.testshardtable
            shard key: { "_id" : 1 }
            unique: false
            balancing: true
            chunks:
                rs0 61
                rs1 60
            too many chunks to print, use verbose if you want to force print
`(ps:如果发现并没有分片,请等待,我们可以逐渐看到 rs0 和 rs1 在慢慢变得平衡)

####6.常见问题
#####6.1我们登录mongod的时候,有时会遇到端口被占用的情况,这时候执行`killall -15 mongod`, 再重新登录,一般可以解决问题
#####6.2如果中间的某步启动出问题,比如初始化 config_server 出错,或者分片出问题,最稳妥的办法是(好吧,也是我能想到的唯一办法),删除出问题的文件夹里 data 的所有东西,重新配置,比如config_server 出错,则
`cd /db2/config_server/data
rm -rf *`
#####6.3通过`ps -fe|grep mongod`来查看 mongod 的运行
#####6.4启动 mongos 时会出现`ERROR: child process failed, exited with error number 51`,这时需要新建相关目录,路径就是[mongos.conf](./mongos.conf)配的那个
#####6.5关于分片的仲裁节点,如果我们的复制集节点数是偶数个,则需要一个仲裁节点[arbiters.conf](./arbiters.conf),如果是奇数个,则不需要仲裁节点.配置仲裁节点的配置文件已经写好,[arbiters.conf](./arbiters.conf),使用的时候只需把这个文件上传到所需要的服务器上,通过`mongod -f /db2/conf/arbiters.conf`启动服务,在复制集上的主节点下,使用`rs.addArb("内网 Ip 3:43100")`来添加仲裁节点就可以了.记得在有仲裁节点的机器的`run.sh`增加启动仲裁节点的语句.配仲裁节点的参考文档是:https://docs.mongodb.com/manual/tutorial/add-replica-set-arbiter/
#####6.5最后,建议大家,一定要看官方文档,但不能只依靠官方文档,版本不同真的会害死人的,比如说配置 sharding 的分片里面的 bindIp 选项,就是官方文档没有提到的,是我从 Google 的某个网页找到的,我现在都忘了怎么找的了...充分说明这活也看人品~~(更新:后来发现不配 bindIp 也是可以的,反正用的话一定要内网 Ip, 外网是肯定不可以的)
配这货一定要仔细,把所有的服务都打开 config_server mongos sharding 这些都是有依赖关系的

####7.读写端口
#####读写都可以从 mongos 的 ip+ 端口(外网 Ip 1:53001)(外网 Ip 2:53001)(外网 Ip 3:53001)进行,由集群自己进行数据迁移和查找数据.
####8.写成批处理文件
我们可以把每个服务器的启动命令,携程批处理文件`run.sh`,上传到服务器上,这样每次启动集群只需要在每台服务器上运行这个批处理即可


