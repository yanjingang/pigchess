# -*- coding: utf-8 -*-
"""
使用Keras实现PolicyValueNet
    在Keras 2.0.5下测试，tensorflow-gpu 1.2.1作为后端
"""

from __future__ import print_function
import os
import sys
import logging
import numpy as np
from keras.engine.topology import Input
from keras.engine.training import Model
from keras.layers.convolutional import Conv2D
from keras.layers.core import Activation, Dense, Flatten
from keras.layers.merge import Add
from keras.layers.normalization import BatchNormalization
from keras.regularizers import l2
from keras.optimizers import Adam
import keras.backend as K

# PATH
CUR_PATH = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.realpath(CUR_PATH + '/../../../../')
sys.path.append(BASE_PATH)

from machinelearning.lib import utils

class PolicyValueNet():
    """策略价值网络"""

    #def __init__(self, board_width, board_height, model_file=None):
    def __init__(self, policy_infer_size, model_file=None):
        #self.board_width = board_width
        #self.board_height = board_height
        self.policy_infer_size = policy_infer_size
        self.l2_const = 1e-4  # coef of l2 penalty 
        self.create_policy_value_net()
        self._loss_train_op()

        if model_file:
            self.load_model_done = False
            self.load_model(model_file)

    def load_model(self, model_file):
        """重新加载模型(仅用于selfplay时load new model)"""
        #net_params = pickle.load(open(model_file, 'rb'), encoding='iso-8859-1')
        try:
            net_params = utils.pickle_load(model_file)
            self.model.set_weights(net_params)
            self.load_model_done = True
        except:
            logging.error("load_model fail! {}\t{}".format(model_file, utils.get_trace()))
            self.load_model_done =  False
        return self.load_model_done


    def create_policy_value_net(self):
        """创建policy-value网络"""
        # 输入层
        #in_x = network = Input((4, self.board_width, self.board_height))
        in_x = network = Input((4, 1, self.policy_infer_size))

        # conv layers
        network = Conv2D(filters=32, kernel_size=(3, 3), padding="same", data_format="channels_first", activation="relu", kernel_regularizer=l2(self.l2_const))(network)
        network = Conv2D(filters=64, kernel_size=(3, 3), padding="same", data_format="channels_first", activation="relu", kernel_regularizer=l2(self.l2_const))(network)
        network = Conv2D(filters=128, kernel_size=(3, 3), padding="same", data_format="channels_first", activation="relu", kernel_regularizer=l2(self.l2_const))(network)
        # 走子策略 action policy layers
        policy_net = Conv2D(filters=4, kernel_size=(1, 1), data_format="channels_first", activation="relu", kernel_regularizer=l2(self.l2_const))(network)
        policy_net = Flatten()(policy_net)
        # infer self.board_width * self.board_height action_probs
        #self.policy_net = Dense(self.board_width * self.board_height, activation="softmax", kernel_regularizer=l2(self.l2_const))(policy_net)
        self.policy_net = Dense(self.policy_infer_size, activation="softmax", kernel_regularizer=l2(self.l2_const))(policy_net)
        # 盘面价值 state value layers
        value_net = Conv2D(filters=2, kernel_size=(1, 1), data_format="channels_first", activation="relu", kernel_regularizer=l2(self.l2_const))(network)
        value_net = Flatten()(value_net)
        value_net = Dense(64, kernel_regularizer=l2(self.l2_const))(value_net)
        # infer one current state score
        self.value_net = Dense(1, activation="tanh", kernel_regularizer=l2(self.l2_const))(value_net)

        # 创建网络模型
        self.model = Model(in_x, [self.policy_net, self.value_net])

        # 返回走子策略和价值概率
        def policy_value(state_input):
            state_input_union = np.array(state_input)
            #print(state_input_union)
            results = self.model.predict_on_batch(state_input_union)
            return results

        self.policy_value = policy_value

    def policy_value_fn(self, board):
        """使用模型预测棋盘所有actionid的价值概率"""
        # 棋盘所有可移动action_ids
        legal_positions = board.availables
        #print(legal_positions)
        # 当前玩家角度的actions过程
        current_actions = board.current_actions()
        #print(current_actions)
        # 使用模型预测走子策略和价值概率
        #print(self.policy_infer_size)
        #act_probs, value = self.policy_value(current_actions.reshape(-1, 4, self.board_width, self.board_height))
        act_probs, value = self.policy_value(current_actions.reshape(-1, 4, 1, self.policy_infer_size))
        act_probs = zip(legal_positions, act_probs.flatten()[legal_positions])
        # 返回[(action, 概率)] 以及当前玩家的后续走子value
        return act_probs, value[0][0]

    def _loss_train_op(self):
        """初始化损失
        3个损失函数因子
        loss = (z - v)^2 + pi^T * log(p) + c||theta||^2
        loss = value损失函数 + policy损失函数 + 惩罚项
        """
        # 定义优化器和损失函数
        opt = Adam()
        losses = ['categorical_crossentropy', 'mean_squared_error']
        self.model.compile(optimizer=opt, loss=losses)

        def self_entropy(probs):
            return -np.mean(np.sum(probs * np.log(probs + 1e-10), axis=1))

        def train_step(state_input, mcts_probs, winner, learning_rate):
            """输出训练过程中的结果"""
            state_input_union = np.array(state_input)
            mcts_probs_union = np.array(mcts_probs)
            winner_union = np.array(winner)
            # 评估
            loss = self.model.evaluate(state_input_union, [mcts_probs_union, winner_union], batch_size=len(state_input), verbose=0)
            # 预测
            action_probs, _ = self.model.predict_on_batch(state_input_union)
            entropy = self_entropy(action_probs)
            K.set_value(self.model.optimizer.lr, learning_rate)
            self.model.fit(state_input_union, [mcts_probs_union, winner_union], batch_size=len(state_input), verbose=0)
            return loss[0], entropy

        self.train_step = train_step

    def get_policy_param(self):
        """获得模型参数"""
        net_params = self.model.get_weights()
        return net_params

    def save_model(self, model_file):
        """保存模型参数到文件"""
        net_params = self.get_policy_param()
        #pickle.dump(net_params, open(model_file, 'wb'), protocol=4)
        utils.pickle_dump(net_params, model_file)
