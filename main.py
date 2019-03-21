#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File: main.py
Desc: 国际象棋强化学习+MCTS策略价值网络模型训练-控制台
Author:yanjingang(yanjingang@mail.com)
Date: 2019/1/21 22:46
Cmd:
    生成训练数据：
        nohup python main.py selfplay 40 > log/selfplay.log 2>&1 &
    训练模型：
        nohup python main.py train 1 > log/train.log 2>&1 &
    评估模型：
        nohup python main.py evaluate 40 > log/evaluate.log 2>&1 &
    与模型对战：
        python main.py infer ai-vs-human
    重放某次对战过程：
        python main.py replay 20190122155910-40-B-65352-bd33dbb3a0742b46fe9cef383630abe2.data
    使用png生成训练数据：
        nohup python main.py pgn Bu.pgn >>log/pgn.log 2>&1 &
"""

from __future__ import print_function
import os
import sys
import getopt
import logging

# PATH
CUR_PATH = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.realpath(CUR_PATH + '/../../../')
sys.path.append(BASE_PATH)

from machinelearning.lib import utils
from game import Game
from train import Train
from evaluate import Evaluate


class Main():
    """控制台"""

    @staticmethod
    def selfplay(params=None):
        """生成对战数据"""
        os.environ["CUDA_VISIBLE_DEVICES"]="-1"
        n_playout = 400 if params is None else int(params)
        game = Game()
        game.start_selfplay(n_playout=n_playout, best_model=Train.BEST_MODEL)

    @staticmethod
    def train(params=None):
        """训练模型"""
        n_train = 10000 if params is None else int(params)
        train = Train()
        train.start_train(n_train=n_train, curr_model=Train.CURR_MODEL)

    @staticmethod
    def evaluate(params=None):
        """评估模型胜率"""
        n_playout_mcts = 400 if params is None else int(params)
        evaluate = Evaluate()
        evaluate.start_evaluate(n_playout_ai=400, n_playout_mcts=n_playout_mcts, curr_model=Train.CURR_MODEL)

    @staticmethod
    def infer(params=None):
        """与模型对战"""
        vs_type = 'human-vs-ai' if params is None else params
        game = Game()
        game.start_infer(vs_type=vs_type, n_playout=50, best_model=Train.CURR_MODEL)

    @staticmethod
    def replay(params=None):
        """重放某次对战数据"""
        os.environ["CUDA_VISIBLE_DEVICES"]="-1"
        data_file = '20190122155910-40-B-65352-bd33dbb3a0742b46fe9cef383630abe2.data' if params is None else params
        game = Game()
        game.replay_databuffer(data_file=data_file, replay_step=1000)

    @staticmethod
    def pgn(params=None):
        """使用png生成训练数据"""
        os.environ["CUDA_VISIBLE_DEVICES"]="-1"
        pgn_file = 'Bu.pgn' if params is None else params
        game = Game()
        game.pgn_to_databuffer(pgn_file=pgn_file)



if __name__ == '__main__':
    opts, args = getopt.getopt(sys.argv[1:], "p:", ["type="])
    if len(args) > 0 and args[0] in ['selfplay', 'train', 'evaluate', 'infer', 'replay', 'pgn']:
        type = args[0]
    else:
        exit("usage: python main.py [selfplay|train|evaluate|infer|replay|pgn] ")
    params = args[1] if len(args) > 1 else None

    # log init
    log_file = type + '-' + str(os.getpid())
    utils.init_logging(log_file=log_file, log_path=CUR_PATH)
    print("log_file: {}".format(log_file))

    # do main
    if type == 'selfplay':  # 生成对战数据
        Main.selfplay(params)
    elif type == 'train':  # 训练模型
        Main.train(params)
    elif type == 'evaluate':  # 评估模型
        Main.evaluate(params)
    elif type == 'infer':  # 与模型对战
        Main.infer(params)
    elif type == 'replay':  # 重放某次对战数据
        Main.replay(params)
    elif type == 'pgn':  # 使用png生成训练数据
        Main.pgn(params)
