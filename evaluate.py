#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File: evaluate.py
Desc: 对价值网络模型进行评估（ai vs mcts）
Author:yanjingang(yanjingang@mail.com)
Date: 2019/1/21 22:46
"""

from __future__ import print_function
import os
import sys
import logging
import random
import pickle
import numpy as np
from collections import defaultdict, deque

# PATH
CUR_PATH = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.realpath(CUR_PATH + '/../../../')
sys.path.append(BASE_PATH)

from game import Board, Game
from player import MCTSPlayer, AIPlayer


class Evaluate():
    """模型胜率评估"""

    def __init__(self):
        """game对象"""
        self.game = Game()

    def policy_evaluate(self, n_playout_ai=400, n_playout_mcts=100, n_games=10):
        """
        策略胜率评估：模型与纯MCTS玩家对战n局看胜率
            n_playout_ai    ai预测每个action的mcts模拟次数
            n_playout_mcts  纯mcts随机走子时每个action的mcts模拟步数
            n_games         策略评估胜率时的模拟对局次数
        """
        logging.info("__policy_evaluate__")
        # ai玩家（使用策略价值网络来指导树搜索和评估叶节点）
        ai_player = AIPlayer(self.policy_value_net.policy_value_fn, n_playout=n_playout_ai)
        # 纯mcts玩家
        mcts_player = MCTSPlayer(n_playout=n_playout_mcts)
        win_cnt = {'ai': 0, 'mcts': 0, 'tie': 0}
        for i in range(n_games):  # 对战
            if i % 2 == 0:  # ai first
                logging.info("policy evaluate start: {}, ai use W".format(i + 1))
                winner = self.game.start_play(ai_player, mcts_player)
                if winner == 0:
                    win_cnt['ai'] += 1
                elif winner == 1:
                    win_cnt['mcts'] += 1
                else:
                    win_cnt['tie'] += 1
            else:  # mcts first
                logging.info("policy evaluate start: {}, ai use B".format(i + 1))
                winner = self.game.start_play(mcts_player, ai_player)
                if winner == 0:
                    win_cnt['mcts'] += 1
                elif winner == 1:
                    win_cnt['ai'] += 1
                else:
                    win_cnt['tie'] += 1
            # win_cnt[winner] += 1
            logging.info("policy evaluate res: {},{}".format(i + 1, win_cnt))
        # 胜率
        win_ratio = 1.0 * (win_cnt['ai'] + 0.5 * win_cnt['tie']) / n_games
        logging.info("evaluate n_playout_mcts:{}, win: {}, lose: {}, tie:{}".format(n_playout_mcts, win_cnt['ai'], win_cnt['mcts'], win_cnt['tie']))
        return win_ratio

    def start_evaluate(self, n_playout_ai=400, n_playout_mcts=100, curr_model=None):
        """启动模型评估
        Params:
            n_playout_ai    ai预测每个action的mcts模拟次数
            n_playout_mcts  纯mcts随机走子时每个action的mcts模拟步数
            curr_model      要评估的模型文件
        """
        logging.info("__start_evaluate__")
        # 1.初始化网络模型
        from net.policy_value_net_keras import PolicyValueNet  # Keras
        self.policy_value_net = PolicyValueNet(self.game.board.action_ids_size, model_file=curr_model)

        # 2. 开始预测
        self.best_win_ratio = 0.0
        try:
            logging.info("policy evaluate start. ")
            # 策略胜率评估：模型与纯MCTS玩家对战n局看胜率
            win_ratio = self.policy_evaluate(n_playout_ai, n_playout_mcts)
            if win_ratio > self.best_win_ratio:  # 胜率超过历史最优模型
                logging.info("policy evaluate res. new best policy!  win_ratio:{}->{} n_playout_mcts:{}".format(self.best_win_ratio, win_ratio, n_playout_mcts))
                self.best_win_ratio = win_ratio
                # 保存当前模型为最优模型best_policy
                self.policy_value_net.save_model(CUR_PATH + '/model/best_policy_{}_{}_{}.model'.format(n_playout_ai, n_playout_mcts, win_ratio))
                # 如果胜率=100%，则增加纯MCT的模拟数
                if (self.best_win_ratio == 1.0):
                    logging.info("policy evaluate n_playout_mcts need ++!!!!")
                    # self.n_playout_mcts += 200
                    # self.best_win_ratio = 0.0
        except KeyboardInterrupt:
            logging.info('\n\rquit')
