const requestUrl = require('../../config').requestUrl
const uploadFileUrl = require('../../config').uploadFileUrl

Page({
    onShareAppMessage() {
        return {
            title: '国际象棋AI-小猪实验室',
            path: 'page/replay/index'
        }
    },
    data: { //会被api返回值覆盖，不要随便添加
        id: 0,
        event: '',
        nick: '',
        opponent: '',
        role: 0,
        result: 0,
        game_info: {},
        i: 0,
        human_player_id: 0,
        ai_player_id: 1,
        curr_player: 0,
        state: {},
        step: 0,
        availables: [],
        msg: '选择角色并点击开始按钮开始与国际象棋AI对战',
    },
    // 接收参数
    onLoad(query) {
        // 参数
        const {
            id,
            event,
            nick,
            opponent,
            role,
            result,
        } = query;
        this.setData({
            id: id,
            event: event,
            nick: nick,
            opponent: opponent,
            role: role,
            result: result,
            human_player_id: role,
            ai_player_id: 1 - role,
        });

        // 标题
        wx.setNavigationBarTitle({
            title: nick + " vs " + opponent + " [" + result + "]"
        });
    },
    //page初始化
    onReady() {
        this.init();
    },
    onPullDownRefresh() {
        this.init();
    },
    init() {
        this.canvas_width = 370; //画布宽度
        this.piece_width = 2; //棋子半径
        this.border_width = 18; //边框宽度
        this.board_size = 8; //棋盘大小8*8
        this.line_width = (this.canvas_width - this.border_width * 2) / this.board_size; //网格线像素宽度
        this.session_id = Date.now();
        this.user_nick = '';
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

        // 对局信息
        const self = this;
        wx.request({
            url: requestUrl,
            data: {
                'req_type': 'chess-info',
                'id': self.data.id,
            },
            success(result) {
                wx.hideToast();

                if (result['statusCode'] != 200) { //网络通信失败
                    console.log('chess-info req http status err: ', result['statusCode'])
                } else if (result['data']['code'] != 0) { //状态异常
                    console.log('chess-info req ret code err: ', result['data']['code'], result['data']['msg'])
                } else if (result['statusCode'] == 200 && result['data']['code'] == 0) {
                    console.log('chess-info req res: ', result['data']['data'])
                    self.setData({
                        game_info: result['data']['data'],
                        i: 0,
                    });
                    // 没有封面图的，自动重放后生成
                    if (result['data']['data'].thumb.indexOf(".png") == -1) {
                        // auto replay
                        for (var i = 0; i < result['data']['data'].moves.length; i++) {
                            var move = result['data']['data'].moves[i];
                            var san = result['data']['data'].sans[i];
                            console.log(result['data']['data'].moves[i]);
                            self.movePiece((self.data.role + i) % 2, move, san);
                        }
                        // auto upload 
                        self.UploadEndBoardImage();
                        // reset board
                        self.initBoard(self.data.human_player_id);
                    }
                }
            },
            fail({
                errMsg
            }) {
                wx.hideToast();
                console.log('chess-info req fail: ', errMsg)
            }
        });
    },
    //下一步
    onReplay(e) {
        if (this.data.i >= this.data.game_info.step) {
            return;
        }

        var move = this.data.game_info.moves[this.data.i];
        var san = this.data.game_info.sans[this.data.i];
        console.log(this.data.i, move, san);
        this.movePiece((this.data.role + this.data.i) % 2, move, san);
        this.data.i += 1;
    },
    //初始化棋盘
    initBoard(angle_player) {
        this.data.step = 0;
        this.data.availables = [];
        this.data.state = {};
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
        // console.log('__drawPiece__' + move + '\t' + player + '\t' + angle_player)
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
    //上传终局盘面截屏
    UploadEndBoardImage() {
        const self = this;
        wx.canvasToTempFilePath({
            canvasId: 'board',
            success: (res) => {
                wx.uploadFile({
                    url: uploadFileUrl,
                    filePath: res.tempFilePath,
                    name: 'data',
                    formData: {
                        'type': 'chess',
                        'id': self.data.id,
                    },
                    success(res) {
                        console.log('uploadImage success, res is:', res)
                        if (res.statusCode != 200) {
                            // wx.showToast({
                            //     title: '网络异常',
                            //     icon: 'none',
                            //     duration: 1000
                            // })
                            return
                        }
                        res = JSON.parse(res.data)
                        if (res.status != 0) {
                            console.log('uploadImage fail:', res.status)
                            // wx.showToast({
                            //     title: '上传失败' + res.status,
                            //     icon: 'none',
                            //     duration: 1000
                            // });
                            return;
                        }
                        const imageUrl = res.data['url']
                        console.log('uploadImage success, url:', res.data)
                        // wx.showToast({
                        //     title: '上传成功',
                        //     icon: 'success',
                        //     duration: 1000
                        // })
                        self.setData({
                            imageUrl,
                        })
                    },
                    fail({
                        errMsg
                    }) {
                        console.log('uploadImage fail, errMsg is', errMsg)
                    }
                });
            },
            fail: (err) => {
                console.log(err);
            }
        }, this);
    }
})