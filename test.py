#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File: test.py
Desc: 测试
Cmd: nohup python3 test.py > log/test.log 2>&1 &
"""

from __future__ import print_function
import os
import sys
import logging
import time
import copy
import pickle
import zlib
import chess
import random
import numpy as np
from collections import defaultdict, deque

# PATH
CUR_PATH = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.realpath(CUR_PATH + '/../../../')
sys.path.append(BASE_PATH)
# print(CUR_PATH, BASE_PATH)

from machinelearning.lib import utils
from game import Game, Board
from player import MCTS, MCTSPlayer, AIPlayer
from train import Train
from net.policy_value_net_keras import PolicyValueNet

"""class Board2():
    def __init__(self):
        self.board = chess.Board()
        print('xx')"""


class Test():
    def __init__(self):
        pass


if __name__ == '__main__':
    """"
    #deepcopy test
    board2 = Board2()
    board3 = copy.deepcopy(board2)
    board3.board.push(chess.Move.from_uci('e2e4'))
    print(board3.board)
    print(board2.board)
    print('-----')
    board = Board()
    board.init_board()
    board.graphic()
    print(board.current_player)
    print(board.availables)
    print(board.book_variations['last'])
    copy.deepcopy(board)
    
    #构建一个纯mcts
    mcts_player = MCTSPlayer(c_puct=5,n_playout=1)
    print('------get_action------MCTSPlayer')
    #走第一步
    action = mcts_player.get_action(board)
    print('------get_action res')
    print(action)
    print(board.action_ids[action])


    #构建一个策略价值网络指导的mcts
    board = Board()
    board.init_board()
    policy_value_net = PolicyValueNet(board.action_ids_size)
    ai_player = AIPlayer(policy_value_net.policy_value_fn, c_puct=5, n_playout=2, is_selfplay=1)
    print('------get_action------AIPlayer')
    #走第一步
    action = ai_player.get_action(board)
    print('------get_action res')
    print(action)
    print(board.action_ids[action])

    game = Game(board)
    data_buffer = deque(maxlen=100)
    batch_size = 10
    logger.info("TRAIN Batch start i:{}".format(1), Test)
    print('------start_self_play start')
    winner, play_data = game.start_self_play(ai_player, temp=1.0)
    print('------start_self_play res')
    print(winner)
    play_data = list(play_data)[:]
    episode_len = len(play_data)
    data_buffer.extend(play_data)
    print(data_buffer)
    print(len(data_buffer))
    
    # net train test
    state_batch = utils.pickle_load(CUR_PATH+'/log/state_batch.data')
    mcts_probs_batch = utils.pickle_load(CUR_PATH+'/log/mcts_probs_batch.data')
    winner_batch = utils.pickle_load(CUR_PATH+'/log/winner_batch.data')
    print(state_batch)
    print(mcts_probs_batch)
    print(winner_batch)
    #board = Board()
    #policy_value_net = PolicyValueNet(board.action_ids_size)
    #old_probs, old_v = policy_value_net.policy_value(state_batch)
   

    #replay_databuffer
    data_file = BASE_PATH + '/machinelearning/game/chess/data/playdata/20190122155910-40-B-65352-bd33dbb3a0742b46fe9cef383630abe2.data'
    game = Game()
    game.replay_databuffer(data_file)
    """

    # png
    log_file = 'pgn-' + str(os.getpid())
    utils.init_logging(log_file=log_file, log_path=CUR_PATH)
    logging.debug("log_file: {}".format(log_file))
    # pgn->databuffer
    game = Game()
    for pgn_file in os.listdir(CUR_PATH+"/data/pgn/"):
        if pgn_file[-4:] == '.pgn':
            try:
                game.pgn_to_databuffer(pgn_file=pgn_file)
            except:
                logging.warning(utils.get_trace())
    
    for data_file in os.listdir(CUR_PATH + "/data/databuffer/"):
        tmp = data_file.split('-')
        if len(tmp) < 6:
            continue
        try:
            step_num = int(tmp[5])
            winner = tmp[2]
            if step_num < 6:
                logging.debug("RM\t"+str(step_num)+"\t"+winner+"\t"+data_file)
                os.remove(CUR_PATH + "/data/databuffer/"+data_file)
            if step_num < 30 and winner == 'Tie':
                logging.debug("RM\t"+str(step_num)+"\t"+winner+"\t"+data_file)
                os.remove(CUR_PATH + "/data/databuffer/"+data_file)
            if step_num < 30:
                logging.debug(str(step_num) + "\t" + winner + "\t" + data_file)
        except:
            logging.warning("name fail! \t" + data_file +"\n" + utils.get_trace())

    """
    board = Board()
    print(board.action_ids_size)

    # 批量下载pgn棋谱
    game = Game()
    game.download_pgn()
    """
