## 强化学习+MCTS国际象棋

### 环境
```
# install python3.6.5
wget https://repo.anaconda.com/archive/Anaconda3-5.2.0-Linux-x86_64.sh --no-check-certificate
sh Anaconda3-5.2.0-Linux-x86_64.sh  #按提示安装，指定安装目录到/home/yanjingang/python3.6.5

# path 
vim ~/.bashrc
  # python3 pip3
  export PATH=/home/yanjingang/python3.6.5/bin:$PATH
  # cuda10.0 cudnn7.4  （参考：http://blog.yanjingang.com/?p=3864）
  export PATH=/usr/local/cuda-10.0/bin${PATH:+:${PATH}}
  export LD_LIBRARY_PATH=/usr/local/cuda-10.0/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}
  export CUDA_HOME=/usr/local/cuda-10.0
  #gpu
  export CUDA_VISIBLE_DEVICES=0  #指定使用第一张gpu卡(不设置默认用所有的卡)
  # lang utf8
  LC_ALL=en_US.UTF-8;export LC_ALL;date
source ~/.bashrc
which python
which pip

# lib
pip install --upgrade pip
pip install numpy opencv-python pillow python-chess tensorflow-gpu==1.14 keras==2.2.5 tornado pydp
*注：本机gpu卡使用cuda_v10.0+cudnn_v7.4+gcc7.5，因此安装tensorflow-gpu1.4配套keras2.2.5(对应表：https://tensorflow.google.cn/install/source)
```

### 模型训练
生成训练数据:  
```
nohup python main.py selfplay 400 > log/selfplay.log 2>&1 &
```
使用png生成训练数据:  
```
python main.py pgn anastasian-lewis.pgn
```
训练模型:  
```
nohup python main.py train 10000 > log/train.log 2>&1 &
*查看gpu卡使用情况：nvidia-smi -l
```
与模型对战:  
```
python main.py infer ai-vs-human
```
评估模型胜率:  
```
nohup python main.py evaluate > log/evaluate.log 2>&1 &
```
重放某次对战过程:  
```
python main.py replay 20190121193238-400-W-27111-d61b4636cdc011db4c7d46f402ab566b.data
```

