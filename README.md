# dailyfresh
天天生鲜


黑马程序员的Django项目，跟着教程一点点码出来的。  
教学视频中有一些功能没有实现，自己做了一些优化，也有一些细微的调整，主要如下：  
1、增加了商品详情页面切换sku功能；  
2、修改了原有的FastDFS，改为本地存储（现在更流行Minio，暂时替换到本地了）；  
3、解决了原有的购物车数量信息显示错误的bug，优化了购物车页面结构，把账单页面明细展示出来了；  
4、更新类别、商品信息后更新首页存入缓存中，提高页面访问效率。  
5、修复了很多样式问题。  

项目用到了redis缓存、celery分布式任务、Jieba分词、全文检索等中间件。  


项目仅供学习交流。  
