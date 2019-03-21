#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File: train.py
Desc: cnn训练价值网络模型
Author:yanjingang(yanjingang@mail.com)
Date: 2019/1/21 22:46
"""

from __future__ import print_function
import os
import sys
import random
import logging
import time
import json
import numpy as np
from collections import defaultdict, deque

# PATH
CUR_PATH = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.realpath(CUR_PATH + '/../../../')
sys.path.append(BASE_PATH)

from machinelearning.lib import utils
from game import Board


class Train():
    """模型训练"""
    # 评估产出的最优模型
    BEST_MODEL = CUR_PATH + '/model/best_policy.model'
    # 训练中的模型
    CURR_MODEL = CUR_PATH + '/model/current_policy.model'

    def __init__(self):
        """训练参数"""
        self.learn_rate = 2e-3
        self.lr_multiplier = 1.0  # 基于KL的自适应学习率
        self.epochs = 5  # 每次更新策略价值网络的训练步骤数
        self.kl_targ = 0.02  # 策略价值网络KL值目标

    def policy_update(self, data_buffer, train_step_size=512):
        """更新策略价值网络policy-value"""
        logging.info("__policy_update__")
        # 随机抽取data_buffer中的对抗数据
        mini_batch = random.sample(data_buffer, train_step_size)
        state_batch = [data[0] for data in mini_batch]
        mcts_probs_batch = [data[1] for data in mini_batch]
        winner_batch = [data[2] for data in mini_batch]
        """
        utils.pickle_dump(state_batch, CUR_PATH+'/log/state_batch.data')
        utils.pickle_dump(mcts_probs_batch, CUR_PATH+'/log/mcts_probs_batch.data')
        utils.pickle_dump(winner_batch, CUR_PATH+'/log/winner_batch.data')
        """
        old_probs, old_v = self.policy_value_net.policy_value(state_batch)
        # 训练策略价值网络
        for i in range(self.epochs):
            loss, entropy = self.policy_value_net.train_step(state_batch, mcts_probs_batch, winner_batch, self.learn_rate * self.lr_multiplier)
            new_probs, new_v = self.policy_value_net.policy_value(state_batch)
            kl = np.mean(np.sum(old_probs * (np.log(old_probs + 1e-10) - np.log(new_probs + 1e-10)), axis=1))
            if kl > self.kl_targ * 4:  # 如果D_KL跑偏则尽早停止
                break
        # 自动调整学习率
        if kl > self.kl_targ * 2 and self.lr_multiplier > 0.1:
            self.lr_multiplier /= 1.5
        elif kl < self.kl_targ / 2 and self.lr_multiplier < 10:
            self.lr_multiplier *= 1.5

        explained_var_old = (1 - np.var(np.array(winner_batch) - old_v.flatten()) / np.var(np.array(winner_batch)))
        explained_var_new = (1 - np.var(np.array(winner_batch) - new_v.flatten()) / np.var(np.array(winner_batch)))
        logging.info(("train kl:{:.3f},lr_multiplier:{:.3f},loss:{:.4f},entropy:{:.4f},explained_var_old:{:.6f},explained_var_new:{:.6f}"
                      ).format(kl, self.lr_multiplier, loss, entropy, explained_var_old, explained_var_new))
        return loss, entropy

    def start_train(self, n_train=10000, buffer_size=10000, train_step_size=512, curr_model=None):
        """启动模型训练
        Params:
            n_train     训练次数
            buffer_size 用于随机的buffer大小（走子步数）
            train_step_size    训练时从buffer中随机抽取的数量（走子步数）
        """
        logging.info("__start_train__")
        # 1.初始化网络模型
        from net.policy_value_net_keras import PolicyValueNet  # Keras
        if curr_model:  # 使用一个训练好的策略价值网络
            self.policy_value_net = PolicyValueNet(Board().action_ids_size, model_file=curr_model)
        else:  # 使用一个新的的策略价值网络
            self.policy_value_net = PolicyValueNet(Board().action_ids_size)
        # 2.开始训练
        try:
            data_buffer = deque(maxlen=buffer_size)
            skip_files = set()
            trained_file = CUR_PATH + '/data/databuffer.trained'
            with open(trained_file, 'r') as f:  # 加载已训练过文件列表
                for line in f:
                    skip_files.add(line)
            best_file = CUR_PATH + '/model/best.info'
            best_info = {'step':0, 'loss':100.0, 'entropy':0.0, 'time':0}
            with open(best_file, 'r') as f:  # 加载最优模型信息
                jstr = f.read()
                if len(jstr) > len(str(best_info)):
                    best_info = json.loads(jstr)
            logging.info("best_info: {}".format(best_info))
            trained_step = 0
            for i in range(n_train):  # 训练次数
                # 2.1.加载自我对抗数据
                data_path = CUR_PATH + '/data/databuffer'
                data_files = os.listdir(data_path)
                logging.info("skip_files len: {}".format(len(skip_files)))
                new_files = list(set(data_files).difference(skip_files))  # 只加载新增的databuffer文件
                # skip_files = skip_files | set(data_files)
                if len(new_files) == 0:
                    logging.info("nofound new file! sleep 60s.")
                    time.sleep(60)
                    continue
                for j in range(len(new_files)):
                    data_file = new_files[j]
                    skip_files.add(data_file)
                    # [ctime, nplayout, winner, pid, hostname, step_num] = data_file.split('-')
                    datainfo = data_file.split('-')
                    if datainfo[2] == 'Tie':  # when first train skip Tie data
                        continue
                    logging.info("load data: {}".format(data_file))
                    play_data = []
                    try:
                        play_data = utils.pickle_load(data_path + '/' + data_file)
                    except:
                        logging.error("load databuffer fail! {}\n{}".format(data_file, utils.get_trace()))
                        continue
                    data_buffer.extend(play_data)
                    logging.info("load databuffer.  batch:{}-{}, size:{}".format(i + 1, j, len(data_buffer)))
                    # 2.2.使用对抗数据重新训练策略价值网络模型
                    if len(data_buffer) > train_step_size:
                        trained_step += 1
                        logging.info("train policy value net start: {}".format(trained_step))
                        loss, entropy = self.policy_update(data_buffer, train_step_size)
                        if loss < best_info['loss']:    #保存最优模型
                            best_info['step'] = len(skip_files)
                            best_info['loss'] = float(loss)
                            best_info['entropy'] = float(entropy)
                            best_info['time'] = time.time()
                            logging.info("get new best model! {}".format(best_info))
                            # save best_info
                            with open(best_file, 'w') as f:
                                f.write(json.dumps(best_info))
                            # save best model
                            self.policy_value_net.save_model(Train.BEST_MODEL)
                        # 保存最新模型
                        self.policy_value_net.save_model(curr_model)
                        # append trained
                        with open(trained_file, 'a') as f:
                            f.write(data_file + "\n")
                    else:
                        logging.info("train policy value net not start! data_buffer:{} < train_step_size:{} !".format(len(data_buffer), train_step_size))

        except KeyboardInterrupt:
            logging.info('\n\rquit')
