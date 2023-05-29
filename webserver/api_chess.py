#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
File: api_chess.py
Desc: 国际象棋 强化学习模型 API 封装
Demo: 
    nohup python api_chess.py > log/api_chess.log &
    
    http://www.yanjingang.com:8024/piglab/game/chess?session_id=1548849426270&move=d7d5

    ps aux | grep api_chess.py |grep -v grep| cut -c 9-15 | xargs kill -9
Author: yanjingang(yanjingang@mail.com)
Date: 2019/1/30 23:08
"""

import sys
import os
import json
import time
import logging
import numpy as np
import tornado.ioloop
import tornado.web
import tornado.httpserver
CUR_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(CUR_PATH + '/../')
from player import AIPlayer, StockfishPlayer
from game import Board, Game
from dp import utils
from mysql import Mysql
#from net.policy_value_net_keras import PolicyValueNet
#from net.policy_value_net_tensorflow import PolicyValueNet  # Tensorflow


class ApiGameChess(tornado.web.RequestHandler):
    """下棋逻辑封装"""
    #model_file = CUR_PATH + '/model/best_policy.model'
    #best_policy = PolicyValueNet(Board().action_ids_size, model_file=model_file)
    games = {}

    def get(self):
        """get请求处理"""
        try:
            result = self.execute()
        except:
            logging.error('execute fail ' + utils.get_trace())
            result = {'code': 1, 'msg': '请求失败'}
        logging.info('API RES[' + self.request.path + '][' + self.request.method + ']['
                     + str(result['code']) + '][' + str(result['msg']) + '][' + str(result['data']) + ']')
        self.write(json.dumps(result))

    def post(self):
        """post请求处理"""
        try:
            result = self.execute()
        except:
            logging.error('execute fail ' + utils.get_trace())
            result = {'code': 1, 'msg': '请求失败'}
        logging.info('API RES[' + self.request.path + '][' + self.request.method + ']['
                     + str(result['code']) + '][' + str(result['msg']) + ']')
        self.write(json.dumps(result))

    def execute(self):
        """执行业务逻辑"""
        logging.info('API REQUEST INFO[' + self.request.path + '][' + self.request.method + ']['
                     + self.request.remote_ip + '][' + str(self.request.arguments) + ']')
        session_id = self.get_argument('session_id', '')
        res = {'session_id': session_id, 'player': -1, 'step': 0, 'move': '', 'san': '', 'end': False, 'winner': -1, 'curr_player': 0, 'state': {}, 'ponder': '', 'score': -1}
        move = self.get_argument('move', '')
        if session_id == '':
            return {'code': 2, 'msg': 'session_id不能为空', 'data': res}

        try:
            # 1.新的对局
            session = {}
            if session_id not in self.games:
                logging.info("[{}] init new game!".format(session_id))
                # plays id
                session['human_player_id'] = int(self.get_argument('human_player_id', '1'))  # human默认执黑
                session['ai_player_id'] = (session['human_player_id'] + 1) % 2  # ai与human相反
                session['players'] = {session['human_player_id']: 'Human', session['ai_player_id']: 'AI'}
                session['nick'] = self.get_argument('user_nick', '')
                session['step'] = 0
                session['actions'], session['mcts_probs'] = [], []
                session['moves'], session['sans'], session['scores'] = [], [], []
                # 初始化棋盘
                session['game'] = Game()
                session['game'].board.init_board()
                # 初始化AI棋手
                #session['ai_player'] = AIPlayer(self.best_policy.policy_value_fn, n_playout=50)
                session['ai_player'] = StockfishPlayer()
                self.games[session_id] = session
            else:
                session = self.games[session_id]
                # clear old games
                for k in list(self.games.keys()):
                    if int(time.time()) - int(k) / 1000 > 60 * 40:  # 超过40分钟的session清理
                        del (self.games[k])
                        logging.warning("[{}] timeout clear!".format(k))
            # 2.get ai move
            res['players'], res['human_player_id'], res['ai_player_id'] = session['players'], session['human_player_id'], session['ai_player_id']
            res['curr_player'] = session['game'].board.current_player_id
            res['availables'] = [session['game'].board.action_to_move(act) for act in session['game'].board.availables]
            res['state'] = session['game'].board.state()
            action = -1
            if res['curr_player'] == session['ai_player_id']:  # 轮到ai时，忽略传入的move参数
                action, probs, ponder, res['score'] = session['ai_player'].get_action(session['game'].board, return_prob=1, return_ponder=1, return_score=1)
                move = session['game'].board.action_to_move(action)
                res['ponder'] = session['game'].board.action_to_move(ponder)
                logging.info("[{}] {} AI move: {}  Score: {} Ponder: {}".format(session_id, res['curr_player'], move, res['score'], res['ponder']))
                # save state
                session['actions'].append(session['game'].board.current_actions())
                session['mcts_probs'].append(probs)
            else:  # 轮到human走
                if len(move) < 4:  # 没有传入move
                    logging.info("[{}] {} Human need give move !".format(session_id, res['curr_player']))
                    return {'code': 2, 'msg': '轮到人类走子', 'data': res}
                logging.info("[{}] {} Human move: {}".format(session_id, res['curr_player'], move))
                action = session['game'].board.move_to_action(move)
                if action not in session['game'].board.availables:  # human action不合法
                    logging.info("[{}] {} Human action ({},{}) invalid !".format(session_id, res['curr_player'], move, action))
                    return {'code': 3, 'msg': '错误的落子位置:{}'.format(move), 'data': res}
                # save state
                session['actions'].append(session['game'].board.current_actions())
                probs = np.zeros(session['game'].board.action_ids_size)
                probs[action] = 0.01
                session['mcts_probs'].append(probs)

            # 3.do move
            if len(move) >= 4 and action != -1:
                # do move
                res['san'] = session['game'].board.move_to_san(move)
                session['game'].board.do_move(action)  # do move
                try:
                    if len(res['ponder']) > 2:
                        res['ponder'] = session['game'].board.move_to_san(res['ponder'])
                except:
                    logging.warning(utils.get_trace())
                session['step'] += 1
                res['player'], res['move'], res['step'] = res['curr_player'], move, session['step']
                res['end'], res['winner'] = session['game'].board.game_end()
                res['curr_player'] = session['game'].board.current_player_id
                res['availables'] = [session['game'].board.action_to_move(act) for act in session['game'].board.availables]
                res['state'] = session['game'].board.state()  # res['state'][move[:2]] + move[:2]
                # save games
                session['moves'].append(res['move'])
                session['sans'].append(res['san'])
                session['scores'].append(str(res['score']))
                # save state -> databuffer
                if res['end']:
                    result = 0.5
                    # 从当前玩家视角确定winner
                    winners_z = np.zeros(len(session['game'].board.book_variations['all']))
                    if res['winner'] != -1:  # 不是和棋
                        for i in range(len(winners_z)):
                            if (i + res['winner']) % 2 == 0:
                                winners_z[i] = 1.0  # 更新赢家步骤位置=1
                            else:
                                winners_z[i] = -1.0  # 更新输家步骤位置=-1
                        # 人类玩家的对局结果
                        if res['winner'] == session['human_player_id']:
                            result = 1
                        else:
                            result = 0
                    play_data = list(zip(session['actions'], session['mcts_probs'], winners_z))[:]
                    data_file = session['game']._get_databuffer_file(event='vs',
                                                                     winner=res['winner'],
                                                                     white=session['players'][0],
                                                                     black=session['players'][1],
                                                                     step_num=len(play_data))
                    utils.pickle_dump(play_data, data_file)
                    logging.info("api vs play save to databuffer: {}".format(data_file))
                    ret = db.insert('games', {
                        'session': session_id,
                        'nick': session['nick'],
                        'role': session['human_player_id'], 
                        'step': session['step'],
                        'moves': ','.join(session['moves']), 
                        'sans': ','.join(session['sans']), 
                        'scores': ','.join(session['scores']),
                        'winner': res['winner'],
                        'result': result,
                    })
                    logging.info("game save to db: {}".format(ret))

                return {'code': 0, 'msg': 'success', 'data': res}
        except:
            logging.error('execute fail [' + str(move) + '][' + session_id + '] ' + utils.get_trace())
            return {'code': 5, 'msg': '请求失败', 'data': res}

        # 组织返回格式
        return {'code': 0, 'msg': 'success', 'data': res}



class ApiChessThumb(tornado.web.RequestHandler):
    """终局盘面截屏图片处理"""
    def get(self):
        """get请求处理"""
        try:
            result = self.execute()
        except:
            logging.error('execute fail ' + utils.get_trace())
            result = {'code': 1, 'msg': '请求失败'}
        logging.info('API RES[' + self.request.path + '][' + self.request.method + ']['
                     + str(result['code']) + '][' + str(result['msg']) + '][' + str(result['data']) + ']')
        self.write(json.dumps(result))

    def post(self):
        """post请求处理"""
        try:
            result = self.execute()
        except:
            logging.error('execute fail ' + utils.get_trace())
            result = {'code': 1, 'msg': '请求失败'}
        logging.info('API RES[' + self.request.path + '][' + self.request.method + ']['
                     + str(result['code']) + '][' + str(result['msg']) + ']')
        self.write(json.dumps(result))

    def execute(self):
        """执行业务逻辑"""
        logging.info('API REQUEST INFO[' + self.request.path + '][' + self.request.method + ']['
                     + self.request.remote_ip + '][' + str(self.request.arguments) + ']')
        id = int(self.get_argument('id', 0))
        session = self.get_argument('session', '')
        nick = self.get_argument('nick', '')
        img_file = self.get_argument('img_file', '')
        ret = 0
        if session == '' and nick == '' and id <= 0:
            return {'code': 2, 'msg': 'thumb info is empty', 'data': {}}

        if id > 0:
            ret = db.update('games', {'id': id}, {'thumb': img_file})
        else:
            ret = db.update('games', {'session': session, 'nick': nick}, {'thumb': img_file})
        logging.info("game board thumb save to db: {}".format(ret))

        return {'code': 0, 'msg': 'success', 'data': ret}



class ApiChessList(tornado.web.RequestHandler):
    """棋谱列表查询"""
    def get(self):
        """get请求处理"""
        try:
            result = self.execute()
        except:
            logging.error('execute fail ' + utils.get_trace())
            result = {'code': 1, 'msg': '请求失败'}
        logging.info('API RES[' + self.request.path + '][' + self.request.method + ']['
                     + str(result['code']) + '][' + str(result['msg']) + '][' + str(result['data']) + ']')
        self.write(json.dumps(result))

    def post(self):
        """post请求处理"""
        try:
            result = self.execute()
        except:
            logging.error('execute fail ' + utils.get_trace())
            result = {'code': 1, 'msg': '请求失败'}
        logging.info('API RES[' + self.request.path + '][' + self.request.method + ']['
                     + str(result['code']) + '][' + str(result['msg']) + ']')
        self.write(json.dumps(result))

    def execute(self):
        """执行业务逻辑"""
        logging.info('API REQUEST INFO[' + self.request.path + '][' + self.request.method + ']['
                     + self.request.remote_ip + '][' + str(self.request.arguments) + ']')
        nick = self.get_argument('nick', '')
        page = int(self.get_argument('page', 0))
        page_size = int(self.get_argument('page_size', 10))
        tab = int(self.get_argument('tab', 0))
        if tab == 0 and nick == '':
            return {'code': 2, 'msg': 'nick is empty', 'data': {}}


        where = {'nick': nick}  # 用户自己
        if tab == 1: # 所有普通用户
            where = {'type': 0}
        elif tab == 2: # 所有国际大师
            where = {'type': 1}
        elif tab == 3: # 赛事直播
            where = {'type': 2}
        select = 'id,event,nick,role,opponent,step,sans,result,thumb,createtime as date'
        orderby = 'id desc'
        limit = str(page * page_size) + ',' + str(page_size)
        res = db.query('games', where=where, select=select, orderby=orderby, limit=limit)
        logging.info("game get list: {}".format(res))

        # roles = {'0': '白', '1': '黑'}
        results = {'0.0': '负', '0.5': '和', '1.0': '胜'}
        for i in range(len(res)):
            res[i]['role'] = res[i]['role']    # roles[str(res[i]['role'])]
            res[i]['result'] = results[str(res[i]['result'])]
            thumb = res[i]['thumb'] if len(res[i]['thumb']) > 0 else 'upload/230529/1685326009327.png'
            res[i]['thumb'] = 'http://www.yanjingang.com/piglab/' + thumb
            if time.strftime("%Y", time.localtime()) == str(res[i]['date'])[0:4]:   # 当年棋谱不显示年份
                res[i]['date'] = str(res[i]['date'])[5:7] + '月' + str(res[i]['date'])[8:10] + '日'
            else:
                res[i]['date'] = str(res[i]['date'])[0:4] + '年' + str(res[i]['date'])[5:7] + '月' + str(res[i]['date'])[8:10] + '日'
        return {'code': 0, 'msg': 'success', 'data': res}


class ApiChessInfo(tornado.web.RequestHandler):
    """棋谱列表查询"""
    def get(self):
        """get请求处理"""
        try:
            result = self.execute()
        except:
            logging.error('execute fail ' + utils.get_trace())
            result = {'code': 1, 'msg': '请求失败'}
        logging.info('API RES[' + self.request.path + '][' + self.request.method + ']['
                     + str(result['code']) + '][' + str(result['msg']) + '][' + str(result['data']) + ']')
        self.write(json.dumps(result))

    def post(self):
        """post请求处理"""
        try:
            result = self.execute()
        except:
            logging.error('execute fail ' + utils.get_trace())
            result = {'code': 1, 'msg': '请求失败'}
        logging.info('API RES[' + self.request.path + '][' + self.request.method + ']['
                     + str(result['code']) + '][' + str(result['msg']) + ']')
        self.write(json.dumps(result))

    def execute(self):
        """执行业务逻辑"""
        logging.info('API REQUEST INFO[' + self.request.path + '][' + self.request.method + ']['
                     + self.request.remote_ip + '][' + str(self.request.arguments) + ']')
        id = int(self.get_argument('id', 0))
        if id <= 0:
            return {'code': 2, 'msg': 'id is invalid', 'data': {}}


        where = {'id': id}
        select = 'id,event,nick,role,opponent,step,moves,sans,result,thumb,createtime as date'
        res = db.query('games', where=where, select=select)
        logging.info("game get info: {}".format(res))
        if len(res) == 0:
            return {'code': 3, 'msg': 'id is not exists', 'data': {}}
        res = res[0]

        # roles = {'0': '白', '1': '黑'}
        results = {'0.0': '负', '0.5': '和', '1.0': '胜'}
        res['role'] = res['role']    # roles[str(res['role'])]
        res['moves'] = res['moves'].split(',')
        res['sans'] = res['sans'].split(',')
        res['result'] = results[str(res['result'])]
        res['thumb'] = 'http://www.yanjingang.com/piglab/' + res['thumb']
        if time.strftime("%Y", time.localtime()) == str(res['date'])[0:4]:   # 当年棋谱不显示年份
            res['date'] = str(res['date'])[5:7] + '月' + str(res['date'])[8:10] + '日'
        else:
            res['date'] = str(res['date'])[0:4] + '年' + str(res['date'])[5:7] + '月' + str(res['date'])[8:10] + '日'

        return {'code': 0, 'msg': 'success', 'data': res}


if __name__ == '__main__':
    """服务入口"""
    port = 8024

    # log init
    log_file = ApiGameChess.__name__.lower()  # + '-' + str(os.getpid())
    utils.init_logging(log_file=log_file, log_path=CUR_PATH)
    print("log_file: {}".format(log_file))

    # conn db
    db = Mysql(
        host='127.0.0.1',
        port='3306',
        user='chess',
        password='2o0kxAmpZM6rfhFA',
        db='chess',
        debug=1,
        autocommit=True,
    )
    db.connect()
    


    # 启动服务
    app = tornado.web.Application(
        handlers=[
            (r'/piggy-chess/move', ApiGameChess),
            (r'/piggy-chess/thumb', ApiChessThumb),
            (r'/piggy-chess/list', ApiChessList),
            (r'/piggy-chess/info', ApiChessInfo),
        ]
    )
    http_server = tornado.httpserver.HTTPServer(app, xheaders=True)
    http_server.listen(port)
    tornado.ioloop.IOLoop.instance().start()
