# -*- coding: utf-8 -*-
"""
各类Player及对应走子算法
    MCTSPlayer      纯蒙特卡罗树搜索（MCTS）的Player
    AIPlayer        基于模型指导的蒙特卡罗树搜索（MCTS）的Player
    HumanPlayer     人类手工指令的Player
    MinimaxPlayer   基于miniMax树搜索的Player
"""
import os
import sys
import time
import numpy as np
import copy
import logging
from operator import itemgetter

# PATH
CUR_PATH = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.realpath(CUR_PATH + '/../../../')
sys.path.append(BASE_PATH)

from machinelearning.lib import utils


class MCTSTreeNode(object):
    """MCTS树中的节点类。 每个节点跟踪其自身的值Q，先验概率P及其访问次数调整的先前得分u。"""

    def __init__(self, parent, prior_p):
        self._parent = parent
        self._children = {}  # a map from action to MCTSTreeNode
        self._Q = 0  # 节点分数，用于mcts树初始构建时的充分打散（每次叶子节点被最优选中时，节点隔级-leaf_value逻辑，以避免构建树时某分支被反复选中）
        self._n_visits = 0  # 节点被最优选中的次数，用于树构建完毕后的走子选择
        self._u = 0
        self._P = prior_p  # action概率

    def expand(self, action_priors):
        """把策略函数返回的[(action,概率)]列表追加到child节点上
            Params：action_priors=走子策略函数返回的走子概率列表[(action,概率)]
        """
        # print("__expand__")
        for action, prob in action_priors:
            # print(action,prob,action not in self._children)
            if action not in self._children:
                self._children[action] = MCTSTreeNode(self, prob)

    def select(self, c_puct):
        """从child中选择最大action Q+奖励u(P) 的动作
            Params：c_puct=child搜索深度
            Return: (action, next_node)
        """
        return max(self._children.items(), key=lambda act_node: act_node[1].get_value(c_puct))

    def get_value(self, c_puct):
        """计算并返回当前节点的值
            c_puct:     child搜索深度
            self._P:    action概率
            self._parent._n_visits  父节点的最优选次数
            self._n_visits          当前节点的最优选次数
            self._Q                 当前节点的分数，用于mcts树初始构建时的充分打散
        """
        self._u = (c_puct * self._P * np.sqrt(self._parent._n_visits) / (1 + self._n_visits))
        return self._Q + self._u

    def update(self, leaf_value):
        """更新当前节点的访问次数和叶子节点评估结果
            leaf_value: 从当前玩家的角度看子树的评估值.
        """
        # 访问计数
        self._n_visits += 1
        # Update Q, a running average of values for all visits.
        self._Q += 1.0 * (leaf_value - self._Q) / self._n_visits

    def update_recursive(self, leaf_value):
        """同update(), 但是对所有祖先进行递归应用
            注意：这里递归-leaf_value用于输赢交替player的分数交错+-
        """
        # 非root节点时递归update祖先
        if self._parent:
            self._parent.update_recursive(-leaf_value)
        self.update(leaf_value)

    def is_leaf(self):
        """检查当前是否叶子节点"""
        return self._children == {}

    def is_root(self):
        """检查当前是否root节点"""
        return self._parent is None


class MCTS(object):
    """蒙特卡罗树搜索的实现"""

    def __init__(self, policy_value_fn, c_puct=5, n_playout=10000):
        """初始化参数"""
        self._root = MCTSTreeNode(None, 1.0)  # root
        self._policy = policy_value_fn  # 可走子action及对应概率
        self._c_puct = c_puct  # MCTS child搜索深度
        self._n_playout = n_playout  # 构建MCTS初始树的随机走子步数

    def get_move(self, board):
        """用于纯MCTS走子
        构建纯MCTS初始树(节点分布充分)，并返回child中访问量最大的action
            board: 当前游戏盘面
            Return: 构建的树中访问量最大的action
        """
        # print("__get_move__")
        # print(board.base)
        logging.info("__get_move__ {}".format(self._n_playout))
        # build mcts pure tree
        for n in range(self._n_playout):  # 模拟n_playout次下一步的走法及对应快速走子的输赢，并更新到树中
            board_copy = copy.deepcopy(board)
            self._playout(board_copy)
        return max(self._root._children.items(), key=lambda act_node: act_node[1]._n_visits)[0]

    def _playout(self, board):
        """使用纯mcts走子策略指导,模拟1次下一步的走法及对应快速走子的输赢，并更新到树中
        执行一步随机走子，对应一次MCTS树持续构建过程（选择最优叶子节点->根据走子策略概率扩充mcts树->评估并更新树的最优选次数）
            board 当前棋盘的deepcopy副本
        """
        # 1.Selection（在树中找到一个最好的值得探索的节点，一般策略是先选择未被探索的子节点，如果都探索过就选择UCB值最大的子节点）
        # print('XXXXXXXXXXXXXXXXXXXXXXXXX-0')
        node = self._root
        # 找到最优叶子节点：递归从child中选择并执行最大 动作Q+奖励u(P) 的动作
        while (1):
            if node.is_leaf():
                # print("node.is_leaf")
                break
            # 从child中选择最优action
            action, node = node.select(self._c_puct)
            # print('-------node.select--------')
            # 执行action走子
            board.do_move(action)

        # 2.Expansion（就是在前面选中的子节点中走一步创建一个新的子节点。一般策略是随机自行一个操作并且这个操作不能与前面的子节点重复）
        # 走子策略返回的[(action,概率)]list
        # print('XXXXXXXXXXXXXXXXXXXXXXXXX-a')
        action_probs, _ = self._policy(board)
        # print(action_probs, _)
        # print('XXXXXXXXXXXXXXXXXXXXXXXXX-b')
        # 检查游戏是否有赢家
        end, winner = board.game_end()
        # print(end,winner)
        if not end:  # 没有结束时，把走子策略返回的[(action,概率)]list加载到mcts树child中
            node.expand(action_probs)
        # print('XXXXXXXXXXXXXXXXXXXXXXXXX-c')
        # 3.Simulation（在前面新Expansion出来的节点开始模拟游戏，直到到达游戏结束状态，这样可以收到到这个expansion出来的节点的得分是多少）
        # 使用快速随机走子评估此叶子节点继续往后走的胜负（board执行快速走子）
        leaf_value = self._evaluate_rollout(board)
        # print(leaf_value)
        # print('XXXXXXXXXXXXXXXXXXXXXXXXX-d')
        # 4.Backpropagation（把前面expansion出来的节点得分反馈到前面所有父节点中，更新这些节点的quality value和visit times，方便后面计算UCB值）
        # 递归更新当前节点及所有父节点的最优选中次数和Q分数（最优选中次数是累加的，Q分数递归-1的目的在于输赢对于交替的player来说是正负交错的）
        node.update_recursive(-leaf_value)

    def update_root_cursor(self, last_action):
        """根据action更新根节点"""
        if last_action in self._root._children:
            self._root = self._root._children[last_action]
            self._root._parent = None
        else:
            self._root = MCTSTreeNode(None, 1.0)

    def _evaluate_rollout(self, board, limit=1000):
        """使用随机快速走子策略评估叶子节点
            Params：
                board 当前盘面
                limit 随机走子次数
            Return：如果当前玩家获胜返回+1
                    如果对手获胜返回-1
                    如果平局返回0
        """
        current_player_id = board.current_player_id
        # print('------_evaluate_rollout-------')
        for i in range(limit):  # 随机快速走limit次，用于快速评估当前叶子节点的优略
            end, winner = board.game_end()
            if end:
                # print("board.game_end")
                # print(board.base)
                break
            # 给棋盘所有可落子位置随机分配概率，并取其中最大概率的action移动
            action_probs = MCTS.rollout_policy_fn(board)
            # print(action_probs)
            max_action = max(action_probs, key=itemgetter(1))[0]
            board.do_move(max_action)
        else:
            # If no break from the loop, issue a warning.
            print("WARNING: rollout reached move limit")
            # print(board.base)
        if winner == -1:  # tie平局
            return 0
        else:
            return 1 if winner == current_player_id else -1

    @staticmethod
    def rollout_policy_fn(board):
        """给棋盘所有可落子位置分配随机概率，用于纯MCTS快速随机走子"""
        action_probs = np.random.rand(len(board.availables))
        return zip(board.availables, action_probs)

    @staticmethod
    def policy_value_fn(board):
        """给棋盘所有可落子位置分配平均概率,用于纯MCTS走子策略 [(0, 0.015625), (action, probability), ...], 0"""
        action_probs = np.ones(len(board.availables)) / len(board.availables)
        # print("__policy_value_fn__")
        # print(len(board.availables),action_probs)
        return zip(board.availables, action_probs), 0

    def get_move_probs(self, board, temp=1e-3):
        """
        构建模型网络MCTS初始树，并返回所有action及对应模型概率
            Params：
                board: 当前游戏盘面
                temp：温度参数  控制探测水平，范围(0,1]
            Return: 所有action及对应概率
        """
        logging.info("__get_move_probs__ {}".format(self._n_playout))
        # build mcts tree by net
        # 主进程阻塞式模拟
        for n in range(self._n_playout):  # 模拟n_playout次下一步的走法及对应快速走子的输赢，并更新到树中
            board_copy = copy.deepcopy(board)
            self._playout_network(board_copy)

        # 分解出child中的action和最优选访问次数
        act_visits = [(act, node._n_visits) for act, node in self._root._children.items()]
        logging.info("act_visits: {}".format(act_visits))
        move_visits = [(board.action_ids[act], node._n_visits) for act, node in self._root._children.items()]
        logging.info("move_visits: {}".format(move_visits))
        acts, visits = zip(*act_visits)
        # softmax概率
        act_probs = MCTS.softmax(1.0 / temp * np.log(np.array(visits) + 1e-10))
        return acts, act_probs

    @staticmethod
    def softmax(x):
        """softmax"""
        probs = np.exp(x - np.max(x))
        probs /= np.sum(probs)
        return probs

    def _playout_network(self, board):
        """使用模型策略指导，模拟1次下一步的走法及对应快速走子的输赢，并更新到树中
        执行一步走子，对应一次MCTS树持续构建过程（选择最优叶子节点->根据模型走子策略概率扩充mcts树->评估并更新树的最优选次数）
            Params：board盘面 构建过程中会模拟走子，必须传入盘面的copy.deepcopy副本
        """
        current_player_id = board.current_player_id
        # print(board.current_player_name)
        node = self._root
        # 找到最优叶子节点：递归从child中选择并执行最大 动作Q+奖励u(P) 的动作
        while (1):
            if node.is_leaf():
                break
            # 从child中选择最优action
            action, node = node.select(self._c_puct)
            # 执行action走子
            board.do_move(action)

        # 使用训练好的模型策略评估此叶子节点，返回[(action,概率)]list 以及当前玩家的后续走子胜负
        # print(board.base)
        action_probs, leaf_value = self._policy(board)
        # act_probs = list(action_probs)[:]
        # act_probs = sorted(act_probs, key=lambda d: d[1])
        # print(act_probs,leaf_value)
        # print([(board.action_ids[act], prob) for act, prob in act_probs])
        # 检查游戏是否有赢家
        end, winner = board.game_end()
        # print(end,winner)
        if not end:  # 没有结束时，把走子策略返回的[(action,概率)]list加载到mcts树child中
            node.expand(action_probs)
        else:
            # 游戏结束时返回真实的叶子胜负
            if winner == -1:  # tie平局
                leaf_value = 0.0
            else:
                leaf_value = (1.0 if winner == current_player_id else -1.0)

        # 递归更新当前节点及所有父节点的最优选中次数和Q分数
        node.update_recursive(-leaf_value)

    def __str__(self):
        return "MCTS"


class MCTSPlayer(object):
    """基于纯MCTS的Player"""

    def __init__(self, c_puct=5, n_playout=2000):
        """初始化参数"""
        self.mcts = MCTS(MCTS.policy_value_fn, c_puct, n_playout)

    def set_player_ind(self, p):
        """指定MCTS的playerid"""
        self.player = p

    def reset_player(self):
        """更新根节点:根据最后action向前探索树"""
        self.mcts.update_root_cursor(-1)

    def get_action(self, board):
        """计算下一步走子action"""
        logging.info("__get_action__ {}".format(len(board.book_variations['all'])))
        # print(board.availables)
        # 构建纯MCTS初始树(节点分布充分)，并返回child中访问量最大的action
        action = self.mcts.get_move(board)
        # print(str(action) + '\t' + board.action_to_move(action))
        # 更新根节点:根据最后action向前探索树
        self.mcts.update_root_cursor(-1)
        logging.info("MCTS action: %s %d,%s" % (board.current_player_name.upper(), action, board.action_to_move(action)))
        return action

    def __str__(self):
        return "MCTSPlayer {}".format(self.player)


class AIPlayer(object):
    """基于模型指导MCTS概率的AI Player"""

    def __init__(self, policy_value_function, c_puct=5, n_playout=2000, is_selfplay=0):
        """初始化参数"""
        self.mcts = MCTS(policy_value_function, c_puct, n_playout)
        self._is_selfplay = is_selfplay

    def set_player_ind(self, p):
        """指定MCTS的playerid"""
        self.player = p

    def reset_player(self):
        """根据最后action向前探索树（通过_root保存当前探索位置）"""
        self.mcts.update_root_cursor(-1)

    def get_action(self, board, temp=1e-3, return_prob=0):
        """计算下一步走子action"""
        # the pi vector returned by MCTS as in the alphaGo Zero paper
        logging.info("__get_action__ {}".format(len(board.book_variations['all'])))
        # move_probs = np.zeros(board.width * board.height)
        move_probs = np.zeros(board.action_ids_size)
        acts, probs = self.mcts.get_move_probs(board, temp)
        # print(acts)
        # print(probs)
        move_probs[list(acts)] = probs
        if self._is_selfplay:  # 自我对抗
            # 添加Dirichlet Noise进行探索（自我训练所需）
            # dirichlet噪声参数中的0.3：一般按照反比于每一步的可行move数量设置，所以棋盘扩大或改围棋之后这个参数需要减小（此值设置过大容易出现在自我对弈的训练中陷入到两方都只进攻不防守的困境中无法提高）
            action = np.random.choice(acts, p=0.75 * probs + 0.25 * np.random.dirichlet(0.6 * np.ones(len(probs))))
            # 更新根节点并重用搜索树
            self.mcts.update_root_cursor(action)
        else:  # 和人类对战
            # 使用默认的temp = 1e-3，它几乎相当于选择具有最高概率的移动
            action = np.random.choice(acts, p=probs)
            # 更新根节点:根据最后action向前探索树
            self.mcts.update_root_cursor(-1)
        # 打印AI走子信息
        logging.info("AI action: %s %d,%s" % (board.current_player_name.upper(), action, board.action_to_move(action)))
        if return_prob:
            return action, move_probs
        else:
            return action

    def __str__(self):
        return "AIPlayer {}".format(self.player)


class HumanPlayer(object):
    """人类Player"""

    def __init__(self):
        self.player = None

    def set_player_ind(self, p):
        self.player = p

    def get_action(self, board):
        action = 0
        while True:
            san = input("Your move: ")
            try:
                action = board.san_to_action(san)
            except Exception as e:
                logging.warning(utils.get_trace())
                action = -1
            logging.info("Human action: %s %d,%s" % (board.current_player_name.upper(), action, board.action_to_move(action)))
            if action in board.availables:  # action legal check
                break
            else:
                print("invoid action [{}] !".format(san))
        return action

    def __str__(self):
        return "HumanPlayer {}".format(self.player)


class MiniMaxPlayer(object):
    """基于miniMax树搜索+alphabeta剪枝的Player"""
    # evaluate
    PIECE_SCORE = {'P': 10, 'N': 30, 'B': 30, 'R': 50, 'Q': 90, 'K': 900}
    PIECE_EVAL = {
        'P': [
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0],
            [1.0, 1.0, 2.0, 3.0, 3.0, 2.0, 1.0, 1.0],
            [0.5, 0.5, 1.0, 2.5, 2.5, 1.0, 0.5, 0.5],
            [0.0, 0.0, 0.0, 2.0, 2.0, 0.0, 0.0, 0.0],
            [0.5, -0.5, -1.0, 0.0, 0.0, -1.0, -0.5, 0.5],
            [0.5, 1.0, 1.0, -2.0, -2.0, 1.0, 1.0, 0.5],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        ],
        'N': [
            [-5.0, -4.0, -3.0, -3.0, -3.0, -3.0, -4.0, -5.0],
            [-4.0, -2.0, 0.0, 0.0, 0.0, 0.0, -2.0, -4.0],
            [-3.0, 0.0, 1.0, 1.5, 1.5, 1.0, 0.0, -3.0],
            [-3.0, 0.5, 1.5, 2.0, 2.0, 1.5, 0.5, -3.0],
            [-3.0, 0.0, 1.5, 2.0, 2.0, 1.5, 0.0, -3.0],
            [-3.0, 0.5, 1.0, 1.5, 1.5, 1.0, 0.5, -3.0],
            [-4.0, -2.0, 0.0, 0.5, 0.5, 0.0, -2.0, -4.0],
            [-5.0, -4.0, -3.0, -3.0, -3.0, -3.0, -4.0, -5.0]
        ],
        'B': [
            [-2.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -2.0],
            [-1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0],
            [-1.0, 0.0, 0.5, 1.0, 1.0, 0.5, 0.0, -1.0],
            [-1.0, 0.5, 0.5, 1.0, 1.0, 0.5, 0.5, -1.0],
            [-1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0, -1.0],
            [-1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, -1.0],
            [-1.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.5, -1.0],
            [-2.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -2.0]
        ],
        'R': [
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5],
            [-0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.5],
            [-0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.5],
            [-0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.5],
            [-0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.5],
            [-0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.5],
            [0.0, 0.0, 0.0, 0.5, 0.5, 0.0, 0.0, 0.0]
        ],
        'Q': [
            [-2.0, -1.0, -1.0, -0.5, -0.5, -1.0, -1.0, -2.0],
            [-1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0],
            [-1.0, 0.0, 0.5, 0.5, 0.5, 0.5, 0.0, -1.0],
            [-0.5, 0.0, 0.5, 0.5, 0.5, 0.5, 0.0, -0.5],
            [0.0, 0.0, 0.5, 0.5, 0.5, 0.5, 0.0, -0.5],
            [-1.0, 0.5, 0.5, 0.5, 0.5, 0.5, 0.0, -1.0],
            [-1.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, -1.0],
            [-2.0, -1.0, -1.0, -0.5, -0.5, -1.0, -1.0, -2.0]
        ],
        'K': [
            [-3.0, -4.0, -4.0, -5.0, -5.0, -4.0, -4.0, -3.0],
            [-3.0, -4.0, -4.0, -5.0, -5.0, -4.0, -4.0, -3.0],
            [-3.0, -4.0, -4.0, -5.0, -5.0, -4.0, -4.0, -3.0],
            [-3.0, -4.0, -4.0, -5.0, -5.0, -4.0, -4.0, -3.0],
            [-2.0, -3.0, -3.0, -4.0, -4.0, -3.0, -3.0, -2.0],
            [-1.0, -2.0, -2.0, -2.0, -2.0, -2.0, -2.0, -1.0],
            [2.0, 2.0, 0.0, 0.0, 0.0, 0.0, 2.0, 2.0],
            [2.0, 3.0, 1.0, 0.0, 0.0, 1.0, 3.0, 2.0]
        ]
    }

    def __init__(self, depth=4, player_id=0):
        """初始化参数"""
        self.player = player_id
        self.depth = depth  # 搜索深度最好为偶数（探索步数*2方走子），这样score>0即对自己有利，<0相反，=0相持

    def set_player_ind(self, p):
        """指定playerid"""
        self.player = p

    def get_action(self, board, isMaximisingPlayer=True):
        """计算下一步走子action
            isMaximisingPlayer: 是否利益最大化player
        """
        availables_cnt = len(board.availables)
        logging.info("__get_action__ step:{} availables_count:{}".format(len(board.book_variations['all']), availables_cnt))
        startTime = time.time()
        # print(board.availables)
        # 模拟走子，取对当前player最有利的走子
        score, action = -9999, -1
        for act in board.availables:
            # 模拟棋盘
            board_copy = copy.deepcopy(board)
            # 模拟走子
            board_copy.do_move(act)
            # 模拟minimax搜索并返回最大得分
            bestScore = self.minimax(self.depth - 1, board_copy, -10000, 10000, not isMaximisingPlayer)
            logging.debug("==============board_copy move minimax: {},{}={}   best:{},{}={}".format(str(act), board_copy.action_to_move(act),bestScore,action,board_copy.action_to_move(action),score))
            if bestScore > score:
                score = bestScore
                action = act

        # print(str(action) + '\t' + board.action_to_move(action))
        logging.info("MiniMax action: {} {},{}  score:{}  availables_cnt:{},time:{}s".format(board.current_player_name.upper(), action, board.action_to_move(action), score, availables_cnt, int(time.time()-startTime)))
        return action

    def minimax(self, depth, board, alpha, beta, isMaximisingPlayer):
        """执行后续的minimax搜索 + alphabeta剪枝"""
        if depth == 0:
            return self.evaluateBoard(board)

        if isMaximisingPlayer:  # 利益最大化player：自己走子
            score = -9999
            for act in board.availables:
                # 模拟棋盘
                board_copy = copy.deepcopy(board)
                # 模拟走子
                board_copy.do_move(act)
                # minimax搜索
                score = max(score, self.minimax(depth - 1, board_copy, alpha, beta, not isMaximisingPlayer))
                # alphabeta剪枝
                alpha = max(alpha, score)
                if beta <= alpha:
                    return score
            return score
        else:  # 利益最小化player：对手走子
            score = 9999
            for act in board.availables:
                # 模拟棋盘
                board_copy = copy.deepcopy(board)
                # 模拟走子
                board_copy.do_move(act)
                # minimax搜索
                score = min(score, self.minimax(depth - 1, board_copy, alpha, beta, not isMaximisingPlayer))
                # alphabeta剪枝
                beta = min(beta, score)
                if beta <= alpha:
                    return score
            return score

    def evaluateBoard(self, board):
        """评估当前棋盘分数"""
        logging.info("__evaluateBoard__")
        board.graphic()
        score = 0
        st = str(board.base).split('\n')
        for h in range(len(st)):
            st[h] = st[h].split(' ')
            for w in range(len(st[h])):
                piece = st[h][w]
                if piece == '.':
                    continue
                piece_type = piece.upper()
                x, y = h, w
                if piece not in self.PIECE_SCORE:   #黑方棋子旋转x,y
                    x, y = 8 - 1 - h, 8 - 1 - w
                absScore = self.PIECE_SCORE[piece_type] + self.PIECE_EVAL[piece_type][x][y]
                # MiniMaxPlayer自己棋子+分，对手棋子-分
                if (self.player == 'w' and piece!=piece_type) or (self.player == 'b' and piece==piece_type):  #对手棋子
                    absScore *= -1
                #logging.debug("evaluateBoard: {} {},{} {}   {} {} {}".format(piece, x, y, absScore, self.player, self.player == board.WHITE, piece!=piece_type))
                score += absScore

        logging.info("evaluateResult: {}".format(score))
        return score

    def __str__(self):
        return "MiniMaxPlayer {}".format(self.player)
