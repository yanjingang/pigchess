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
  # cuda8.0 cudnn5.1
  export CUDA_HOME=/home/work/cuda-8.0
  export CUDNN_HOME=/home/yanjingang/cudnn_v5.1/cuda/
  export CUDNN_ROOT=/home/yanjingang/cudnn_v5.1/cuda/
  export PATH=${CUDA_HOME}/bin:${PATH}
  export CPATH=${CUDNN_HOME}/include:${CUDA_HOME}/include
  export LIBRARY_PATH=${CUDA_HOME}/lib64:${CUDNN_HOME}/lib64:${LIBRARY_PATH}
  export LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${CUDNN_HOME}/lib64:${LD_LIBRARY_PATH}
  #gpu
  export CUDA_VISIBLE_DEVICES=0  #指定使用第一张gpu卡(不设置默认用所有的卡)
  # lang utf8
  LC_ALL=en_US.UTF-8;export LC_ALL;date
source ~/.bashrc
which python
which pip

# lib
pip install --upgrade pip
pip install numpy opencv-python pillow python-chess keras==2.0 tensorflow-gpu==1.2 tornado
*注：本机gpu卡使用cuda_v8.0+cudnn_v5.1，因此只能安装tensorflow-gpu1.2，配套keras2.0(对应表：https://tensorflow.google.cn/install/source)
```

### 模型训练
生成训练数据:  
```
nohup python main.py selfplay 400 > log/selfplay.log 2>&1 &
```
训练模型:  
```
nohup python main.py train 10000 > log/train.log 2>&1 &
*查看gpu卡使用情况：nvidia-smi -l
```
评估模型胜率:  
```
nohup python main.py evaluate > log/evaluate.log 2>&1 &
```
与模型对战:  
```
python main.py infer ai-vs-human
```
重放某次对战过程:  
```
python main.py replay 20190121193238-400-W-27111-d61b4636cdc011db4c7d46f402ab566b.data
```
使用png生成训练数据:  
```
python main.py pgn anastasian-lewis.pgn
```
