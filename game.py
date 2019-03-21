#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File: game.py
Desc: 国际象棋棋盘&对局
Author:yanjingang(yanjingang@mail.com)
Date: 2019/1/12 11:37
"""

from __future__ import print_function
import os
import sys
import time
import socket
import logging
import pickle
import numpy as np
import chess, chess.pgn

# PATH
CUR_PATH = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.realpath(CUR_PATH + '/../../../')
sys.path.append(BASE_PATH)

from machinelearning.lib import utils
from player import AIPlayer, MCTSPlayer, HumanPlayer, MiniMaxPlayer


class Board():
    """棋盘"""
    # player
    WHITE = 0
    BLACK = 1
    PLAYERS = ['w', 'b']

    def __init__(self):
        # 棋盘对象 不继承的原因是deepcopy报错 
        # self.width = 8
        # self.height = 8
        # 初始化actionid列表
        self.action_ids = self._init_action_ids()
        self.action_ids_size = len(self.action_ids)  # 策略网络预测范围
        # players
        # self.players = ['w', 'b']  # player1 and player2

    def init_board(self, start_player=0):
        """初始化棋盘"""
        self.current_player_name = Board.PLAYERS[start_player]  # start player
        self.current_player_id = start_player
        # re init board
        self.base = chess.Board()
        # 当前player所有可合法移动action id list
        self.availables = self.get_legal_actions()
        # 创建棋谱
        """
        self.book = chess.pgn.Game()  # 创建pgn棋谱
        self.book.headers["Event"] = "AI Game"
        self.book.headers["Site"] = "Beijing, China"
        self.book.headers["Date"] = "2019.01.11"
        self.book.headers["Round"] = "1"
        self.book.headers["White"] = "AI"
        self.book.headers["Black"] = "YJY"
        self.book.headers["Result"] = "*"  # 游戏进行中
        self.booknode = self.book
        """
        # 棋谱move记录 key: move, value: player
        self.book_variations = {'w': [], 'b': [], 'last': {}, 'all': []}

    def get_legal_actions(self):
        """当前player所有可合法移动action id list"""
        # print('__get_legal_actions__')
        actions = []
        for move in self.base.generate_legal_moves():  # 所有可合法移动action list(包含王车移位、将军、吃子等)
            # 将move 转为 action id
            action = self.move_to_action(str(move))
            # print(str(move) + '\t' + self.san(move) + '\t' + str(action))
            actions.append(action)
        return actions

    def move_to_action(self, move):
        """
        将move字符串 转为 action id
            d1e2 = 3*64+12 -> 204
        """
        # mov->action对应的数字表示
        # print(move)
        move = str(move).lower()
        action = -1
        if move in self.action_ids:
            action = self.action_ids.index(move)
        else:
            logging.warning('move_to_action fail [{}] !'.format(move))
        return action

    def action_to_move(self, action):
        """
        将action id 还原为 move字符串
            204 = 3 12 -> d1e2
        """
        # print('__action_to_move__')
        action = int(action)
        move = ''
        if action < self.action_ids_size:
            move = self.action_ids[action]
        else:
            logging.warning('action_to_move fail [{}] !'.format(action))
        return move

    def san_to_move(self, san):
        """
        将san指令 转为 move (需在do_move前调用)
            Qg5 -> d8g5
        """
        if len(san) >= 3:  # 非兵移位时，首字母大写
            san = san.capitalize()
        if san[0:2].upper() == 'O-':  # 移位全大写
            san = san.upper()
        # san to move
        return str(self.base.parse_san(san))

    def move_to_san(self, move):
        """
        将move字符串 转为 san (需在do_move前调用)
            g1f3 -> Nf3
        """
        # print(move)
        move = str(move).lower()
        return self.base.san(chess.Move.from_uci(move))

    def san_to_action(self, san):
        """
        将san指令 转为 action id (需在do_move前调用)
            Qg5 -> 3814
        """
        # san to move
        move = str(self.san_to_move(san))
        # move to actionid
        return self.move_to_action(move)

    def current_actions(self):
        """返回当前玩家角度的历史action状态，do_move前调用，用于模型预测和积累data_buffer训练数据。形状：4*1*action_ids_size"""
        # logging.debug("__current_actions__")
        square_state = np.zeros((4, 1, self.action_ids_size))
        # print(self.book_variations)
        if len(self.book_variations['w']) > 0:
            # 当前待do_move玩家的历史action状态
            curr = self.current_player_name
            # logging.debug("curr: "+curr)
            # logging.debug(self.book_variations[curr])
            for action in self.book_variations[curr]:
                square_state[0][0][action] += 1.0
                # square_state[0][0][action] = 1.0
            # 对家历史action状态
            oppo = 'b' if curr == 'w' else 'w'  # 同self.book_variations['last']['player_name']
            # logging.debug("oppo: "+oppo)
            # logging.debug(self.book_variations[oppo])
            for action in self.book_variations[oppo]:
                square_state[1][0][action] += 1.0
                # square_state[1][0][action] = 1.0
            # 对家最后一次action
            square_state[2][0][self.book_variations['last']['action']] = 1.0
            # 对家playerid
            square_state[3][:, :] = self.book_variations['last']['player_id']
        # logging.debug(square_state)
        return square_state[:, ::-1, :]  # 翻转对家和最后一次落子位置的棋盘视角

    def do_move(self, action):
        """落子"""
        # print("__do_move__"+str(action))
        curr_player_name = self.base.fen().split()[1]
        # action to move
        move = self.action_to_move(action)
        #logging.debug("do_move: "+str(action)+"  "+move)
        move_obj = chess.Move.from_uci(move)
        # logging.info(curr_player_name.upper() + ': ' + move)
        # do move
        self.base.push(move_obj)
        """
        # 记录棋谱
        self.booknode = self.booknode.add_variation(move_obj)  #记录move到棋谱
        gameover, winner = self.game_end()
        if gameover:
            self.book.headers["Result"] = self.base.result()
        #print(self.book)
        """
        # 棋谱
        self.book_variations[curr_player_name].append(action)
        self.book_variations['all'].append(action)
        self.book_variations['last'] = {'player_name': curr_player_name, 'player_id': Board.PLAYERS.index(curr_player_name), 'move': move, 'action': action}
        # print(self.book_variations)
        # print(self.base)
        # 所有合法action id list
        self.availables = self.get_legal_actions()
        # next player
        self.current_player_name = self.base.fen().split()[1]
        self.current_player_id = Board.PLAYERS.index(self.current_player_name)

    def game_end(self):
        """检查游戏是否结束"""
        game_over = self.base.is_game_over()  # 游戏是否结束
        if game_over:
            result = self.base.result()  # 获取游戏结果
            if result == '0-1':
                return True, 1  # 黑胜
            elif result == '1-0':
                return True, 0  # 白胜
            elif result == '1/2-1/2':
                return True, -1  # 和棋

        return False, -1  # 游戏中

    def graphic(self, angle_player=0, vsprint=False):
        """绘制棋盘并显示游戏信息"""
        # print(str(self.base))
        state = str(self.base).split('\n')
        # a-h str
        ah_str = "  "
        for w in range(8):
            if angle_player == Board.WHITE:
                ah_str += "{} ".format(chr(w + ord('a')))
            else:  # 黑方视角
                ah_str += "{} ".format(chr(ord('h') - w))
        # first row a-h
        state_str = ah_str + '\n'
        # each  state row
        for i in range(len(state)):
            h = i
            num = "{} ".format(8 - i)  # row num
            if angle_player == Board.BLACK:  # 黑方视角
                h = 8 - 1 - i
                num = "{} ".format(1 + i)  # row num
            state[h] = state[h].split(' ')
            state_str += num  # state left num
            for w in range(len(state[h])):
                piece = state[h][w]
                if angle_player == Board.BLACK:  # 黑方视角
                    piece = state[h][8 - 1 - w]
                if piece == '.':
                    state_str += ". "
                else:  # 打印棋子icon
                    state_str += "{} ".format(chess.Piece.from_symbol(piece).unicode_symbol())
            state_str += " " + num + "\n"  # state right num
        # last row a-h
        state_str += ah_str
        logging.info("\n" + state_str)
        if vsprint:  # 人类与模型对战需要打印模型走子情况到屏幕
            print("\n" + state_str)

    def state(self, san=''):
        """返回棋盘非空位置的棋子信息"""
        logging.info("__state__ {}".format(san))
        state = {}
        # each  state row
        st = str(self.base).split('\n')
        for i in range(len(st)):
            h = i
            num = "{}".format(8 - i)  # row num
            st[h] = st[h].split(' ')
            for w in range(len(st[h])):
                piece = st[h][w]
                if piece != '.':
                    state[chr(w + ord('a')) + num] = piece
        if len(san) == 3:  # append last move
            state[san[1:3]] = san[:1]
        return state

    def _init_action_ids(self):
        """初始化所有可能的move指令，下标为move对应的actionid"""
        labels_array = []
        letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        numbers = ['1', '2', '3', '4', '5', '6', '7', '8']
        promoted_to = ['q', 'r', 'b', 'n']  # 升变

        for l1 in range(8):
            for n1 in range(8):
                destinations = [(t, n1) for t in range(8)] + \
                               [(l1, t) for t in range(8)] + \
                               [(l1 + t, n1 + t) for t in range(-7, 8)] + \
                               [(l1 + t, n1 - t) for t in range(-7, 8)] + \
                               [(l1 + a, n1 + b) for (a, b) in
                                [(-2, -1), (-1, -2), (-2, 1), (1, -2), (2, -1), (-1, 2), (2, 1), (1, 2)]]
                for (l2, n2) in destinations:
                    if (l1, n1) != (l2, n2) and l2 in range(8) and n2 in range(8):
                        move = letters[l1] + numbers[n1] + letters[l2] + numbers[n2]
                        labels_array.append(move)
        for l1 in range(8):
            l = letters[l1]
            for p in promoted_to:
                labels_array.append(l + '2' + l + '1' + p)
                labels_array.append(l + '7' + l + '8' + p)
                if l1 > 0:
                    l_l = letters[l1 - 1]
                    labels_array.append(l + '2' + l_l + '1' + p)
                    labels_array.append(l + '7' + l_l + '8' + p)
                if l1 < 7:
                    l_r = letters[l1 + 1]
                    labels_array.append(l + '2' + l_r + '1' + p)
                    labels_array.append(l + '7' + l_r + '8' + p)
        return labels_array


class Game(object):
    """游戏对局"""

    def __init__(self, **kwargs):
        self.board = Board()
        self.winners = {'0': 'W', '1': 'B', '-1': 'Tie'}  # winner id dict

    def start_play(self, player1, player2, is_shown=1, vsprint=False, angle_player=0):
        """启动对局（评估 or 预测）"""
        # 初始化棋盘
        self.board.init_board(Board.WHITE)  # hold white first
        # 指定对局玩家
        p1, p2 = Board.PLAYERS
        player1.set_player_ind(p1)
        player2.set_player_ind(p2)
        players = {p1: player1, p2: player2}
        # 绘制棋盘
        if is_shown:
            self.board.graphic(vsprint=vsprint, angle_player=angle_player)
        # 开始对局
        while True:
            current_player = players[self.board.current_player_name]
            # 获取落子位置并落子
            action = current_player.get_action(self.board)
            self.board.do_move(action)
            if is_shown:
                self.board.graphic(vsprint=vsprint, angle_player=angle_player)
            # 检查游戏是否结束
            end, winner = self.board.game_end()
            if end:
                if is_shown:
                    if winner != -1:
                        logging.info("Game end. Winner is {}".format(Board.PLAYERS[winner]))
                    else:
                        logging.info("Game end. Tie")
                return winner

    def _load_policy_value_net(self, best_model):
        """加载网络模型"""
        from net.policy_value_net_keras import PolicyValueNet  # Keras
        policy_value_net = PolicyValueNet(self.board.action_ids_size, model_file=best_model)
        while policy_value_net.load_model_done is False:
            try:
                policy_value_net.load_model(best_model)
            except:
                logging.warning("_load_policy_value_net fail! sleep 10s to reload.")
                time.sleep(10)
        return policy_value_net

    def start_selfplay(self, batch_num=10000, c_puct=5, n_playout=400, best_model=None):
        """
        启动持续的selfplay，用于为模型train生成训练数据
        Params:
            batch_num   selfplay对战次数
            c_puct      MCTS child搜索深度
            n_playout   模型训练时每个action的mcts模拟次数
        """
        logging.info("__start_selfplay__")
        # 1.init net & ai player
        model_last_mdy_time = os.stat(best_model).st_mtime  # 模型最后更新时间
        policy_value_net = self._load_policy_value_net(best_model)
        ai_player = AIPlayer(policy_value_net.policy_value_fn, c_puct=c_puct, n_playout=n_playout, is_selfplay=1)

        # 2.start selfplay
        try:
            for i in range(batch_num):  # 对战盘数
                # 2.1使用MCTS蒙特卡罗树搜索进行自我对抗
                logging.info("selfplay batch start: {}".format(i + 1))
                winner, play_data = self._selfplay(ai_player)
                logging.info("selfplay batch res. batch:{}, winner:{}, step_num:{}".format(i + 1, winner, len(play_data)))
                # 2.2保存本局数据到databuffer目录文件
                data_file = self._get_databuffer_file(event=n_playout, winner=winner, step_num=len(play_data))
                utils.pickle_dump(play_data, data_file)
                logging.info("selfplay batch save. batch:{}, file:{}".format(i + 1, data_file))
                # 2.3检查是否有新的模型需要reload
                if os.stat(best_model).st_mtime > model_last_mdy_time:
                    logging.info("selfplay reload model! new:{} > old:{}".format(utils.get_date(os.stat(best_model).st_mtime), utils.get_date(model_last_mdy_time)))
                    model_last_mdy_time = os.stat(best_model).st_mtime  # 模型最后更新时间
                    policy_value_net = self._load_policy_value_net(best_model)
                    ai_player = AIPlayer(policy_value_net.policy_value_fn, c_puct=c_puct, n_playout=n_playout, is_selfplay=1)

        except KeyboardInterrupt:
            logging.info('\n\rselfplay quit')

    def _selfplay(self, player, temp=1.0, is_shown=1):
        """启动对局（ai selfplay生成训练数据）
        使用MCTS蒙特卡罗树搜索进行自我对抗，直到本局结束
            重用搜索树并保存自我对抗数据用于训练(state, mcts_probs, winners_z)
            player：ai_player
        """
        logging.info("___selfplay__")
        # 初始化棋盘
        self.board.init_board()
        actions, mcts_probs = [], []
        while True:  # 在棋局没有赢家或和棋结束前交替落子
            # MCTS搜索最佳落子位置
            action, probs = player.get_action(self.board, temp=temp, return_prob=1)
            # print(action)
            # print(probs)
            # save state
            actions.append(self.board.current_actions())
            # print('--actions--')
            # print(actions)
            mcts_probs.append(probs)
            # 执行落子
            self.board.do_move(action)
            # print(action,is_shown)
            if is_shown:
                self.board.graphic()
            # 检查游戏是否结束
            end, winner = self.board.game_end()
            if end:
                # print(winner)
                # append last move
                # actions.append(self.board.current_actions())
                # mcts_probs.append(np.zeros(self.board.action_ids_size))
                # 从当前玩家视角确定winner
                winners_z = np.zeros(len(self.board.book_variations['all']))
                if winner != -1:  # 不是和棋
                    for i in range(len(winners_z)):
                        if (i + winner) % 2 == 0:
                            winners_z[i] = 1.0  # 更新赢家步骤位置=1
                        else:
                            winners_z[i] = -1.0  # 更新输家步骤位置=-1
                # 重置MCTS根结点
                player.reset_player()
                if is_shown:
                    if winner != -1:
                        logging.info("Game end. Winner is {}".format(Board.PLAYERS[winner]))
                    else:
                        logging.info("Game end. Tie")
                # print(actions, mcts_probs, winners_z)
                # print(list(zip(actions, mcts_probs, winners_z))[:])
                return winner, list(zip(actions, mcts_probs, winners_z))[:]

    def start_infer(self, vs_type='human-vs-ai', n_playout=400, best_model=None):
        """
        启动对战
        Params:
            batch_num       selfplay对战次数
            c_puct          MCTS child搜索深度
            n_playout_ai    ai预测每个action的mcts模拟次数
            n_playout_mcts  纯mcts随机走子时每个action的mcts模拟步数
        """
        logging.info("__start_vsplay__")

        # 1.初始化棋盘
        self.board.init_board()
        # 2.初始化棋手
        # 初始化AI棋手
        from net.policy_value_net_keras import PolicyValueNet  # Keras
        best_policy = PolicyValueNet(self.board.action_ids_size, model_file=best_model)
        ai_player = AIPlayer(best_policy.policy_value_fn, n_playout=n_playout)
        # 初始化MCTS棋手
        mcts_player = MCTSPlayer(n_playout=n_playout)
        # 初始化人类棋手，输入移动命令的格式： Nf3
        human_player = HumanPlayer()
        # 初始化MiniMax棋手
        minimax_player = MiniMaxPlayer(depth=4)

        # 3.启动游戏
        logging.info("vsplay start: ".format(vs_type))
        if vs_type == 'human-vs-ai':
            self.start_play(human_player, ai_player, vsprint=True)
        elif vs_type == 'human-vs-mcts':
            self.start_play(human_player, mcts_player, vsprint=True)
        elif vs_type == 'human-vs-minimax':
            self.start_play(human_player, minimax_player, vsprint=True)
        elif vs_type == 'ai-vs-human':
            self.start_play(ai_player, human_player, vsprint=True, angle_player=Board.BLACK)
        elif vs_type == 'mcts-vs-human':
            self.start_play(mcts_player, human_player, vsprint=True, angle_player=Board.BLACK)
        elif vs_type == 'minimax-vs-human':
            self.start_play(minimax_player, human_player, vsprint=True, angle_player=Board.BLACK)
        else:
            exit("undefind vs-type: ".format(vs_type))

    def replay_databuffer(self, data_file, replay_step=1000):
        """重放某个playdata的走子过程"""
        self.board.init_board()
        # load file
        play_data = utils.pickle_load(CUR_PATH + '/data/databuffer/' + data_file)
        logging.info('step_num: {}'.format(len(play_data)))
        data_info = data_file.split('-')
        player_names = ['', '']
        if data_info[1].isdigit() == False:  # 赛事信息的，获取姓名
            if data_info[3] != '?':
                player_names[0] = data_info[3]
            if data_info[4] != '?':
                player_names[1] = data_info[4]
        last_w_acts = []
        last_b_acts = []
        # setp replay
        for i in range(len(play_data)):
            if i >= replay_step:
                logging.warning('break replay! ')
                break
            curr_player = i % 2
            curr_player_name = Board.PLAYERS[curr_player].upper()
            oppo_player = (i + 1) % 2
            oppo_player_name = Board.PLAYERS[oppo_player].upper()
            [actions, mcts_probs, winners_z] = play_data[i]
            logging.info("-----------step: {}, curr: {} {}, winner: {}-----------".format(i + 1, curr_player_name, player_names[curr_player], winners_z == 1.0))
            # 黑白双方的action情况
            w_play_data = actions[curr_player][0]
            b_play_data = actions[oppo_player][0]
            w_acts = []
            for j in range(len(w_play_data)):
                if w_play_data[j] > 0:
                    w_acts.append(self.board.action_ids[j] + '-' + str(int(w_play_data[j])))
            logging.info("w: {}".format(w_acts))
            b_acts = []
            for j in range(len(b_play_data)):
                if b_play_data[j] > 0:
                    b_acts.append(self.board.action_ids[j] + '-' + str(int(b_play_data[j])))
            logging.info("b: {}".format(b_acts))
            # 对家lastmove
            new_w_act = list(set(w_acts).difference(set(last_w_acts)))
            new_b_act = list(set(b_acts).difference(set(last_b_acts)))
            last_w_acts = w_acts
            last_b_acts = b_acts
            move = ''
            if curr_player == 0 and len(new_b_act) > 0:
                move = new_b_act[0].split('-')[0]
            elif curr_player == 1 and len(new_w_act) > 0:
                move = new_w_act[0].split('-')[0]
            if move != '':  # replay走子过程
                self.board.do_move(self.board.move_to_action(move))
                self.board.graphic()  # vsprint=True
            logging.info("{}'s move: {}".format(oppo_player_name, move))
            # 推荐curr的action及概率
            act_probs = {}
            for j in range(len(mcts_probs)):
                if mcts_probs[j] > 0.001:
                    act_probs[self.board.action_ids[j]] = round(mcts_probs[j], 4)
            act_probs = sorted(act_probs.items(), key=lambda d: d[1])
            logging.info("{}'s probs: {}".format(curr_player_name, act_probs))

            # if i==5:
            #    break

    def download_pgn(self):
        """批量下载pgn棋谱"""
        from pyquery import PyQuery
        import requests
        import zipfile

        # 1.get zip url list
        domain = 'http://www.pgnmentor.com'
        doc = PyQuery(url=domain + '/files.html')
        # print(doc('head'))
        a_l = doc('body div:first table:eq(3) tr td:first table').find('tr')  # body->第一个div->第4个table->tr下第1个td->table下的tr列表
        m_z = doc('body div:first table:eq(3) tr td:last table').find('tr')  # body->第一个div->第4个table->tr下最后一个td->table下的tr列表
        # print(len(a_l))
        # print(len(m_z))
        urls = set()
        for tr in a_l:
            urls.add(domain + '/' + PyQuery(tr)('td:first a').attr('href'))
        for tr in m_z:
            urls.add(domain + '/' + PyQuery(tr)('td:first a').attr('href'))
        print(urls)
        # 2.download zip file
        for zip_url in urls:
            print(zip_url)
            zip = requests.get(zip_url, timeout=50)
            save_path = CUR_PATH + "/data/pgn/"
            save_file = zip_url.split('/')[-1]
            with open(save_path + save_file, 'wb') as f:
                f.write(zip.content)
            # 3.unzip gpn
            f = zipfile.ZipFile(save_path + save_file, 'r')
            for file in f.namelist():
                f.extract(file, save_path)
                # 4.to databuffer
                # self.pgn_to_databuffer(file)
            # 5.cleaar zip file
            os.unlink(save_path + save_file)

    def _get_pgn_winner(self, pgn_result):
        """pgn result转为winner数字"""
        winner = -1
        if pgn_result == '1-0':
            winner = 0  # 白胜
        elif pgn_result == '0-1':
            winner = 1  # 黑胜
        elif pgn_result == '1/2-1/2':
            winner = -1  # 和棋
        return winner

    def pgn_to_databuffer(self, pgn_file):
        """将pgn棋谱转为databuffer用于模型训练"""
        logging.info("__pgn_to_databuffer__ {}".format(pgn_file))
        from xpinyin import Pinyin
        pinyin = Pinyin()
        # 1.加载棋谱
        pgn = open(CUR_PATH + "/data/pgn/" + pgn_file)
        # 2.读取第一局
        game = chess.pgn.read_game(pgn)
        batch = 0
        while game:  # 棋谱包含多局
            batch += 1
            logging.info(game)
            logging.info(game.headers)
            winner = self._get_pgn_winner(game.headers['Result'])
            event = pinyin.get_pinyin(game.headers['Event'].replace(' ', '').replace('.', '').replace('-', '').replace('/', '').replace('(', '').replace(')', '').replace("'",""), "")
            white = pinyin.get_pinyin(game.headers['White'].replace(' ', '').replace(',', '').replace('-', '').replace('/', '').replace('(', '').replace(')', '').replace("'",""), "")
            black = pinyin.get_pinyin(game.headers['Black'].replace(' ', '').replace(',', '').replace('-', '').replace('/', '').replace('(', '').replace(')', '').replace("'",""), "")
            players = [white, black]
            # 3.重放对局过程，获得playdata
            # 初始化棋盘
            self.board.init_board()
            self.board.graphic()
            actions, mcts_probs = [], []
            # 重放走子
            step = 0
            # for move in game.mainline_moves():
            moves = game.mainline_moves().__iter__()
            move = next(moves, None)
            while move:
                step += 1
                logging.info("step: {},  curr: {} {},  winner: {}".format(step, Board.PLAYERS[self.board.current_player_id].upper(), players[self.board.current_player_id],
                                                                                    self.board.current_player_id == winner))
                actions.append(self.board.current_actions())
                # 执行落子
                action = self.board.move_to_action(move)
                if action == -1:
                    logging.error("invalid move! {}".format(move))
                    break
                probs = np.zeros(self.board.action_ids_size)
                if self.board.current_player_id == winner:
                    probs[action] = 1.0
                else:
                    probs[action] = 0.8
                if pgn_file == 'chessease.pgn': #非top大师棋谱，权重调低
                    probs[action] *= 0.1
                mcts_probs.append(probs)
                logging.info("{}'s probs: {}".format(Board.PLAYERS[self.board.current_player_id].upper(), {self.board.action_to_move(action): probs[action]}))
                self.board.do_move(action)
                self.board.graphic()
                # next move
                move = next(moves, None)
                # 检查游戏是否结束
                end, win = self.board.game_end()
                agreement = ""
                if end or move is None:
                    if end is False and move is None:  # 人工投降或协议和棋了
                        agreement = "Agreement"
                    # 从当前玩家视角确定winner
                    winners_z = np.zeros(len(self.board.book_variations['all']))
                    if winner != -1:  # 不是和棋
                        for i in range(len(winners_z)):
                            if (i + winner) % 2 == 0:
                                winners_z[i] = 1.0  # 更新赢家步骤位置=1
                            else:
                                winners_z[i] = -1.0  # 更新输家步骤位置=-1
                    if winner != -1:
                        logging.info("Game end. {} Winner is {}".format(agreement, Board.PLAYERS[winner]))
                    else:
                        logging.info("Game end. {} Tie".format(agreement))
                    # print(actions, mcts_probs, winners_z)
                    # print(list(zip(actions, mcts_probs, winners_z))[:])
                    play_data = list(zip(actions, mcts_probs, winners_z))[:]
                    if len(play_data) < 7:  # 6步不足以将杀，肯定是人工协议和棋，没有训练意义
                        continue
                    if len(play_data) < 30 and winner == -1:  # 30步内和棋肯定是人工协议和棋，没有训练意义
                        continue

                    # 4.保存本局数据到databuffer目录文件
                    data_file = self._get_databuffer_file(date=game.headers['Date'].replace('.', '').replace('?', '0'),
                                                          event=event,
                                                          winner=winner,
                                                          white=white,
                                                          black=black,
                                                          step_num=len(play_data),
                                                          agreement=agreement)
                    utils.pickle_dump(play_data, data_file)
                    logging.info("pgn_to_databuffer save. pgn:{}, batch:{}, databuffer:{}".format(pgn_file, batch, data_file))
            # 5.读取棋谱下一局
            game = chess.pgn.read_game(pgn)
            # break

    def _get_databuffer_file(self, date='', event='', winner=-1, white='', black='', step_num=0, agreement=0):
        """生成databuffer 文件名"""
        # path
        data_path = CUR_PATH + '/data/databuffer'
        utils.mkdir(data_path)
        # file
        if date == '':
            date = time.strftime('%Y%m%d%H%M%S')
        if white == '':
            white = os.getpid()
        if black == '':
            black = utils.md5(socket.gethostname())
        data_file = "{}-{}-{}-{}-{}-{}-{}.data".format(date, event, self.winners[str(winner)], white, black, step_num, 1 if agreement else 0)
        return data_path + '/' + data_file
