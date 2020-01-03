# Lip-Reading-2019创青春.交子杯AI赛道第18名代码
数据集中每个样本由唇语序列图片和对应的说话内容文本组成，数据被分为训练集和测试集，分别用于训练模型和测试模型效果。
数据集情况如下：     

        1. 训练集    

            训练集唇语数据：lip_train.zip      

            训练集唇语数据标签：lip _train.txt     

        2. 测试集      

            测试集唇语数据： lip_test.zip         

        3. 数据说明文档：数据说明.txt     

        4. 初赛线上提交结果示例：预测结果.csv  

        5. 唇语识别参考资料：参考资料.zip
由于比赛已结束，已无法从比赛主页获取数据集，大家可以尝试连续主办方获得比赛数据集。或如有类似数据集也可用我的模型进行测试。        
本人代码主要在 https://github.com/tstafylakis/Lipreading-ResNet 的基础上进行调整和修改，感谢先生的无私分享。     
该模型主要分3部分：          
1）训练一个3DCNN作为front end来抽取特征， 2DCNN作为back end进行预测。            
2）将3DCNN部分的参数进行freeze，抛弃掉2DCNN的部分，连接一个 2 layers Bilstm，用较大的学习率训练较少的eporch来为lstm层找到较好的初始学习率。   
3）将导入2）中的模型，解冻所有参数，用很小的学习率，端对端的训练我们的最终模型。          
模型运行流程如下：              
1）使用google colab作为平台进行训练                             
2）确保数据集的导入的路径无误               
3）运行lipread_cnnbackend.py （或可将代码转移至jupyter notebook），该步用0.0003的lr训练30个eporch（0.9的momentum和0.0001的weight decay）。Val acc可达到40%。          
4）运行lstm_init.py，该步启用lstm代替cnn用于预测，首先为lstm层寻找到较佳的初始参数。用0.05的lr训练5个eporch，Val acc略高于前者。    
5）运行end_to_end.py，该步导入前者的训练结果并解冻所有参数，用0.0003的lr训练30个eporch（0.9的momentum和0.0001的weight decay）。Val acc可达到60+%。              
6）运行predict.py生成预测结果，最终A榜和B榜得分分别为69.2%和70.8%。        

如代码如有任何bug,欢迎指出！           

