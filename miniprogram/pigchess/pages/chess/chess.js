const requestUrl = require('../../config').requestUrl
Page({
  onShareAppMessage() {
    return {
      title: '国际象棋AI-小猪实验室',
      path: 'page/chess/chess'
    }
  },
  data: { //会被api返回值覆盖，不要随便添加
    human_player_select: ['执白', '执黑'],
    human_player_id: 0,
    ai_player_id: 1,
    curr_player: 0,
    state: {},
    step: 0,
    availables: [],
    can_choose: true, //仅页面初始态下角色、开始按钮可点击
    msg: '选择角色并点击开始按钮开始与国际象棋AI对战',
  },
  //page初始化
  onReady() {
    this.canvas_width = 370; //画布宽度
    this.piece_width = 2; //棋子半径
    this.border_width = 18; //边框宽度
    this.board_size = 8; //棋盘大小8*8
    this.line_width = (this.canvas_width - this.border_width * 2) / this.board_size; //网格线像素宽度
    this.session_id = Date.now();
    this.color = '#6f84b3'; //蓝紫色
    //cost
    this.WHITE = 0;
    this.BLACK = 1;
    this.PLAYERS = ['白方', '黑方'];
    this.WINNER = {
      '0': '白方',
      '1': '黑方',
      '-1': '和棋'
    };

    //canvas
    this.ctx = wx.createCanvasContext('board')
    this.ctx.strokeStyle = this.color; //边框颜色
    //init board
    this.initBoard(this.data.human_player_id);
    //move
    //this.movePiece(this.WHITE, 'g1f3', 'Nf4')

    //start play
    //this.aiMove();
  },
  //初始化棋盘
  initBoard(angle_player) {
    //绘制棋盘
    this.drawBoard(angle_player);
    console.log("human_player_id: " + this.data.human_player_id)
    this.select_mf = ''; //点击选字：''未选子；'d4'选中了d4位置的棋子
    //初始化棋子
    for (var i = 0; i < this.board_size; i++) {
      var w_char = String.fromCharCode(97 + i);
      //P
      this.drawPiece('P' + w_char + '2', 0, angle_player);
      this.drawPiece('P' + w_char + '7', 1, angle_player);
      this.data['state'][w_char + '2'] = 'P';
      this.data['state'][w_char + '7'] = 'p';
      if (i == 0 || i == this.board_size - 1) {
        //R
        this.drawPiece('R' + w_char + '1', 0, angle_player);
        this.drawPiece('R' + w_char + '8', 1, angle_player);
        this.data['state'][w_char + '1'] = 'R';
        this.data['state'][w_char + '8'] = 'r';
        //N
        var ni = i;
        if (i == this.board_size - 1) {
          ni -= 2;
        }
        var wn_char = String.fromCharCode(97 + ni + 1);
        this.drawPiece('N' + wn_char + '1', 0, angle_player);
        this.drawPiece('N' + wn_char + '8', 1, angle_player);
        this.data['state'][wn_char + '1'] = 'N';
        this.data['state'][wn_char + '8'] = 'n';
        //B
        var bi = i;
        if (i == this.board_size - 1) {
          bi -= 4;
        }
        var wb_char = String.fromCharCode(97 + bi + 2);
        this.drawPiece('B' + wb_char + '1', 0, angle_player);
        this.drawPiece('B' + wb_char + '8', 1, angle_player);
        this.data['state'][wb_char + '1'] = 'B';
        this.data['state'][wb_char + '8'] = 'b';
      }
    }
    //K&Q
    this.drawPiece('Qd1', 0, angle_player);
    this.drawPiece('Qd8', 1, angle_player);
    this.data['state']['d1'] = 'Q';
    this.data['state']['d8'] = 'q';
    this.drawPiece('Ke1', 0, angle_player);
    this.drawPiece('Ke8', 1, angle_player);
    this.data['state']['e1'] = 'K';
    this.data['state']['e8'] = 'k';
  },
  //绘制棋盘
  drawBoard(angle_player) {
    this.ctx.beginPath();
    //网格
    for (var i = 0; i <= this.board_size; i++) {
      var x = this.border_width + i * this.line_width;
      var y = this.canvas_width - this.border_width;
      //只画最外层边框
      this.ctx.lineWidth = 0.8;
      if (i == 0 || i == this.board_size) {
        //竖线
        this.ctx.moveTo(x, this.border_width);
        this.ctx.lineTo(x, y);
        this.ctx.stroke();
        //横线
        this.ctx.moveTo(this.border_width, x);
        this.ctx.lineTo(y, x);
        this.ctx.stroke();
      }
      //只画黑格矩形
      if (i < this.board_size) {
        if (angle_player == this.WHITE) { //白方视角
          //标号
          this.ctx.setFontSize(10)
          this.ctx.setFillStyle(this.color)
          this.ctx.fillText(String.fromCharCode(97 + i), x + this.line_width / 2 - 2, y + this.border_width / 2 + 2) //底部
          this.ctx.fillText(this.board_size - i, y + 5, x + this.line_width / 2 + 2) //右侧
          this.ctx.fillText(String.fromCharCode(97 + i), x + this.line_width / 2 - 2, this.border_width - 4) //顶部
          this.ctx.fillText(this.board_size - i, this.border_width / 2 - 4, x + this.line_width / 2 + 2) //左侧
          //黑格
          this.ctx.setFillStyle(this.color)
          for (var j = 0; j < this.board_size; j++) {
            if (((i + 1) % 2 == 0 && (j + 1) % 2 == 1) || ((i + 1) % 2 == 1 && (j + 1) % 2 == 0)) { //左上角视角：偶数行+偶数行奇数列 || 奇数行+偶数列
              this.ctx.fillRect(this.border_width + i * this.line_width, this.border_width + j * this.line_width, this.line_width, this.line_width)
            }
          }
        } else { //黑方视角
          //标号
          this.ctx.setFontSize(10)
          this.ctx.setFillStyle(this.color)
          this.ctx.fillText(String.fromCharCode(104 - i), x + this.line_width / 2 - 2, y + this.border_width / 2 + 2) //底部
          this.ctx.fillText(i + 1, y + 5, x + this.line_width / 2 + 2) //右侧
          this.ctx.fillText(String.fromCharCode(104 - i), x + this.line_width / 2 - 2, this.border_width - 4) //顶部
          this.ctx.fillText(i + 1, this.border_width / 2 - 4, x + this.line_width / 2 + 2) //左侧
          //黑格
          this.ctx.setFillStyle(this.color)
          for (var j = 0; j < this.board_size; j++) {
            if (((i + 1) % 2 == 0 && (j + 1) % 2 == 1) || ((i + 1) % 2 == 1 && (j + 1) % 2 == 0)) { //左上角视角：偶数行+偶数行奇数列 || 奇数行+偶数列
              this.ctx.fillRect(this.border_width + i * this.line_width, this.border_width + j * this.line_width, this.line_width, this.line_width)
            }
          }
        }
      }
    }
    this.ctx.closePath();
    this.ctx.draw()
  },
  //绘制棋子
  drawPiece(move, player, angle_player) {
    console.log('__drawPiece__' + move + '\t' + player + '\t' + angle_player)
    var h = parseInt(move.substring(2, 3)) - 1;
    var w = move.charCodeAt(1) - 97;
    if (angle_player == 1) { //黑方视角
      h = this.board_size - parseInt(move.substring(2, 3));
      w = this.board_size - (move.charCodeAt(1) - 97) - 1;
    }
    var piece_type = move.substring(0, 1).toUpperCase();
    //console.log(move);
    //console.log(h);
    //console.log(w);
    //console.log(piece_type);
    var x = this.border_width + w * this.line_width;
    var y = this.border_width + (this.board_size - h - 1) * this.line_width;
    var icon = piece_type + player;
    this.ctx.beginPath();
    //console.log(icon);
    this.ctx.drawImage('../../image/chess/' + icon + '.png', x + 1, y + 1, this.line_width - 2, this.line_width - 2)
    this.ctx.closePath();
    this.ctx.draw(true);
  },
  //消除棋子
  clearPiece(move, angle_player) {
    console.log('__clearPiece__' + move + '\t' + angle_player)
    //注：h/w是以左下角视角计算的
    var h = parseInt(move.substring(1, 2)) - 1;
    var w = move.charCodeAt(0) - 97;
    if (angle_player == 1) { //黑方视角
      h = this.board_size - parseInt(move.substring(1, 2));
      w = this.board_size - (move.charCodeAt(0) - 97) - 1;
    }
    //console.log(h);
    //console.log(w);
    var x = this.border_width + w * this.line_width;
    var y = this.border_width + (this.board_size - h - 1) * this.line_width;
    this.ctx.beginPath();
    //擦除该圆 (注：会连此区域的背景图都擦掉露出背景色，所以需要让convas的background-color与背景图rgb保持一致)
    this.ctx.clearRect(x + 1, y + 1, this.line_width - 2, this.line_width - 2);
    // 重画黑格
    //console.log((h + 1) % 2)
    //console.log((w + 1) % 2)
    if (((h + 1) % 2 == 1 && (w + 1) % 2 == 1) || ((h + 1) % 2 == 0 && (w + 1) % 2 == 0)) { //左下角视角
      this.ctx.fillRect(this.border_width + w * this.line_width, this.border_width + (this.board_size - h - 1) * this.line_width, this.line_width, this.line_width)
    }
    this.ctx.closePath();
    this.ctx.draw(true);
  },
  //走子
  movePiece(player, move, san) {
    //*注：mf位置是否有棋子需要在调用此函数前检查
    console.log("__movePiece__ " + move + " " + san)
    var mf = move.substring(0, 2);
    var mt = move.substring(2, 4);
    var piece_type = san.substring(0, 1);
    if (san.substring(0, 1) == 'O') { //移位
      piece_type = 'K';
    } else if (san.indexOf('=') != -1) { //兵升变，直接draw升变后的棋子
      piece_type = san.substring(san.indexOf('=') + 1, san.indexOf('=') + 2);
    } else if (san.substring(0, 1) >= 'a' && san.substring(0, 1) <= 'h') { //兵移动\将军\将死\吃子
      piece_type = 'P';
    }
    this.clearPiece(mf, this.data.human_player_id);
    this.clearPiece(mt, this.data.human_player_id);
    this.drawPiece(piece_type + mt, player, this.data.human_player_id);
    //补画车的移位
    if (san.substring(0, 1) == 'O') {
      var h = move.substring(1, 2);
      var mf = mt = '';
      if (san == 'O-O') { //短移位
        mf = 'h' + h;
        mt = 'f' + h;
      } else { //长移位
        mf = 'a' + h;
        mt = 'd' + h;
      }
      this.clearPiece(mf, this.data.human_player_id);
      this.drawPiece('R' + mt, player, this.data.human_player_id);
    }
    return true;
  },
  /*//悔棋
  rollbackMove(move) {
    //*注：此函数未实现完毕
    var mf = move.substring(0, 2);
    var mt = move.substring(2, 4);
    var piece_type = this.data['state'][mt]; //区分大小写
    var player = 0;
    if (piece_type >= 'b' && piece_type <= 'r') { //小写是黑方
      player = 1;
    }
    this.clearPiece(mt, this.data.human_player_id);
    this.drawPiece(piece_type + mf, player, this.data.human_player_id);
    this.data['state'][mf] = piece_type;
    delete this.data['state'][mt];
    //TODO:王车移位逻辑
    //TODO:后端通信逻辑
    return true;
  },*/
  //人类选择角色
  onPlayerSelect(e) {
    this.setData({
      human_player_id: e.detail.value
    })
    console.log('select human_player_id:', this.data.human_player_id)
    this.setData({
      msg: '你选择了角色: ' + this.PLAYERS[this.data.human_player_id]
    });
    //重绘棋盘
    this.initBoard(this.data.human_player_id)
  },
  //开始游戏
  onStartPlay(e) {
    this.setData({ //角色、开始按钮不可点击
      can_choose: false,
      msg: '开始游戏，请走子'
    })
    if (this.data.human_player_id == this.BLACK) { //human执黑时，让ai先走
      this.aiMove();
    }
  },
  //棋盘点击事件
  onBoardClick(e) {
    //检查游戏是否已结束
    if (this.data['end']) {
      return false;
    }
    //check是否该human了
    if (this.data['curr_player'] != this.data.human_player_id) { //该ai走了
      var msg = '当前应 ' + this.PLAYERS[this.data['curr_player']] + 'AI 走子';
      if (this.data.can_choose) {
        msg += '\n请点击[开始]按钮开始游戏'
      }
      this.setData({
        msg: msg
      });
      console.log("curr_player is ai!")
      return false;
    }
    //检查是否已开始
    if (this.data.can_choose && this.data.human_player_id == this.WHITE) { //human执白未点开始就走子时，将开始按钮置灰
      this.setData({ //角色、开始按钮不可点击
        can_choose: false,
        msg: '游戏已自动开始'
      });
    }
    //获取当前点击位置的坐标
    //console.log(e)
    var x = e.touches[0].pageX - e.target.offsetLeft - this.border_width;
    var y = e.touches[0].pageY - e.target.offsetTop - this.border_width;
    var w = Math.floor(x / this.line_width);
    var h = this.board_size - Math.floor(y / this.line_width) - 1;
    if (this.data.human_player_id == 1) { //黑方视角
      w = this.board_size - Math.floor(x / this.line_width) - 1;
      h = Math.floor(y / this.line_width);
    }
    var select = String.fromCharCode(97 + w) + (h + 1);
    if (this.select_mf == '') { //选子操作
      //检查选子是否合法（选中的是否自己的棋子/是否是空位置）
      if (!(select in this.data['state'])) { //此位置没有棋子
        console.log(select + " empty!");
        this.setData({
          msg: '选择位置没有棋子！'
        });
        return false;
      }
      var piece_player = (this.data['state'][select] >= 'B' && this.data['state'][select] <= 'R') ? this.WHITE : this.BLACK;
      //console.log(this.data.human_player_id)
      //console.log(piece_player)
      if (this.data.human_player_id != piece_player) { //检查选中棋子是否自己的棋子
        console.log(select + " not your piece! " + this.data['state'][select])
        this.setData({
          msg: '选中的不是你的棋子！' + select + '是' + this.PLAYERS[piece_player] + this.data['state'][select]
        });
        return false;
      }
      //选中
      this.select_mf = select;
      console.log(h + ',' + w + ' | select: ' + select)
      this.setData({
        msg: '你选中: ' + select + ', ' + this.data['state'][select]
      });
      return;
    }
    //确定move操作
    var move = this.select_mf + select;
    var piece_type = this.data['state'][this.select_mf];
    var piece_player = (this.data['state'][this.select_mf] >= 'B' && this.data['state'][this.select_mf] <= 'R') ? this.WHITE : this.BLACK;
    var mt_h = parseInt(select.substring(1, 2));
    console.log(piece_type + ' | ' + piece_player + ' | ' + mt_h)
    if (piece_type.toUpperCase() == 'P' && ((piece_player == this.WHITE && mt_h == 8) || (piece_player == this.BLACK && mt_h == 1))) { //兵已经攻到底要升变了
      move += 'q'; //自动升变为后
    }
    this.select_mf = '';
    console.log(h + ',' + w + ' | move: ' + move)
    this.setData({
      msg: '你选择move: ' + move
    });

    //落子操作
    //检查落子是否合法
    //console.log(this.data['availables'].indexOf(move))
    if (this.data['availables'].indexOf(move) == -1 && this.data['step'] > 0) {
      this.setData({
        msg: '错误的落子位置: ' + move
      });
      console.log("move not in availables!")
      return false;
    }
    //human走子
    const self = this;
    wx.showToast({
      icon: 'loading',
      duration: 100000
    });
    self.setData({
      msg: '正在执行走子...'
    });
    wx.request({
      url: requestUrl,
      data: {
        'req_type': 'chess',
        'session_id': self.session_id,
        'human_player_id': this.data.human_player_id,
        'move': move
      },
      success(result) {
        wx.hideToast();
        console.log('human req res: ', result)
        if (result['statusCode'] != 200) { //网络通信失败
          console.log('human req http status err: ', result['statusCode'])
          self.setData({
            msg: '网络请求失败！ ' + result['statusCode']
          });
          wx.showToast({
            title: '网络请求失败',
            icon: 'none',
            duration: 3000
          });
        } else if (result['data']['code'] != 0) {  //状态异常
          console.log('human req ret code err: ', result['data']['code'] + result['data']['msg'])
          self.setData({
            msg: result['data']['msg']
          });
          wx.showToast({
            title: result['data']['msg'],
            icon: 'none',
            duration: 3000
          });
        } else if (result['statusCode'] == 200 && result['data']['code'] == 0) { //执行Human走子
          self.data = result['data']['data']
          console.log('data: ', self.data)
          //move
          self.movePiece(self.data['player'], self.data['move'], self.data['san'])
          self.setData({
            msg: '你走子: ' + self.data['san']
          });
          //check end
          if (self.data['end']) {
            wx.showModal({
              title: 'Game Over',
              content: '游戏结束，Winner is ' + self.WINNER[self.data['winner']],
              showCancel: false,
              confirmText: '确定'
            });
            self.setData({
              msg: '游戏结束，Winner is ' + self.WINNER[self.data['winner']]
            });
            return true;
          }
          //远端ai走子
          self.aiMove();
        }
      },
      fail({
        errMsg
      }) {
        wx.hideToast();
        console.log('human req fail: ', errMsg)
        self.setData({
          msg: '网络请求失败！ ' + errMsg
        });
        wx.showToast({
          title: '网络请求失败',
          icon: 'none',
          duration: 3000
        })
      }
    });
  },
  //获取AI走子
  aiMove() {
    const self = this
    //请求ai走子
    wx.showToast({
      title: 'AI Loading',
      icon: 'loading',
      duration: 100000
    });
    self.setData({
      msg: '等待' + self.WINNER[self.data.curr_player] + 'AI走子...'
    });
    wx.request({
      url: requestUrl,
      data: {
        'req_type': 'chess',
        'session_id': self.session_id,
        'human_player_id': this.data.human_player_id,
        'move': ''
      },
      success(result) {
        wx.hideToast();
        console.log('ai req succ: ', result)
        //执行AI走子
        if (result['statusCode'] == 200 && result['data'] !== null && result['data']['code'] == 0) {
          self.data = result['data']['data']
          console.log('data: ', self.data)
          //move
          self.movePiece(self.data['player'], self.data['move'], self.data['san']);
          self.setData({
            msg: self.WINNER[self.data['player']] + '走子: ' + self.data['san'] + '  盘面打分: ' + self.data['score'] + '  AI推荐: ' + self.data['ponder']
          });
          //check end
          if (self.data['end']) {
            wx.showModal({
              title: 'Game Over',
              content: '游戏结束，Winner is ' + self.WINNER[self.data['winner']],
              showCancel: false,
              confirmText: '确定'
            });
            self.setData({
              msg: '游戏结束，Winner is ' + self.WINNER[self.data['winner']]
            });
            return true;
          }
        } else {
          console.log('ai req err: ', result)
          var msg = 'statusCode: ' + result['statusCode'];
          if (result['data'] !== null) {
            msg = result['data']['code'] + ':' + result['data']['msg']
          }
          self.setData({
            msg: 'AI走子请求失败！ ' + msg
          });
          wx.showToast({
            title: '网络请求失败',
            icon: 'none',
            duration: 3000
          })
        }
      },
      fail({
        errMsg
      }) {
        wx.hideToast()
        console.log('ai req fail: ', errMsg)
        self.setData({
          msg: '网络请求失败! ' + errMsg
        });
        wx.showToast({
          title: '网络请求失败',
          icon: 'none',
          duration: 3000
        });
      }
    });
  }
})