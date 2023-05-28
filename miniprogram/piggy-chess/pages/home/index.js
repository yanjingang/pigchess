const requestUrl = require('../../config').requestUrl
import Toast from 'tdesign-miniprogram/toast/index';

Page({
  data: {
    imgSrcs: [
      'https://www.yanjingang.com/piglab/upload/chess/banner/banner1.jpg',
      'https://www.yanjingang.com/piglab/upload/chess/banner/banner2.jpg',
      'https://www.yanjingang.com/piglab/upload/chess/banner/banner3.jpg',
      'https://www.yanjingang.com/piglab/upload/chess/banner/banner4.jpg',
      'https://www.yanjingang.com/piglab/upload/chess/banner/banner5.jpg',
    ],
    tabIndex: 0,
    tabList: [{
        text: '我的棋谱',
        key: 0,
      },
      {
        text: '联盟观战',
        key: 1,
      },
      {
        text: '国际大师',
        key: 2,
      },
      {
        text: '竞赛直播',
        key: 3,
      }
    ],
    gameList: [],
    gameListLoadStatus: 0,
    pageLoading: false,
    current: 1,
    autoplay: true,
    duration: '500',
    interval: 5000,
    navigation: {
      type: 'dots'
    },
    swiperImageProps: {
      mode: 'scaleToFill'
    },
  },
  gameListPagination: {
    index: 0,
    num: 20,
  },
  onShow() {
    this.getTabBar().init();
  },
  onLoad() {
    this.init();
  },
  onReachBottom() {
    if (this.data.gameListLoadStatus === 0) {
      this.loadGoodsList();
    }
  },
  onPullDownRefresh() {
    this.init();
  },
  init() {
    // get user
    this.user_nick = '';
    const userInfo = wx.getStorageSync('userInfo');
    console.log("getStorageInfo:", userInfo);
    if (userInfo && userInfo.nickName != '') {
      this.user_nick = userInfo.nickName;
    }
    // get list
    wx.stopPullDownRefresh();
    this.loadGoodsList(true);
  },
  tabChangeHandle(e) {
    this.data.tabIndex = e.detail.value;
    this.loadGoodsList(true);
  },
  onReTry() {
    this.loadGoodsList();
  },
  async loadGoodsList(fresh = false) {
    if (fresh) {
      wx.pageScrollTo({
        scrollTop: 0,
      });
    }

    this.setData({
      gameListLoadStatus: 1
    });

    const pageSize = this.gameListPagination.num;
    let pageIndex = pageSize + this.gameListPagination.index + 1;
    if (fresh) {
      pageIndex = 0;
    }

    // 对战列表
    const self = this;
    wx.request({
      url: requestUrl,
      data: {
        'req_type': 'chess-list',
        'nick': self.user_nick,
        'page': pageIndex,
        'page_size': pageSize,
        'tab': self.data.tabIndex
      },
      success(result) {
        wx.hideToast();
        self.setData({
          gameListLoadStatus: 0
        });

        if (result['statusCode'] != 200) { //网络通信失败
          console.log('chess-list req http status err: ', result['statusCode'])
        } else if (result['data']['code'] != 0) { //状态异常
          console.log('chess-list req ret code err: ', result['data']['code'], result['data']['msg'])
          self.setData({
            gameList: fresh ? [] : self.data.gameList.concat([]),
          });
        } else if (result['statusCode'] == 200 && result['data']['code'] == 0) {
          const nextList = result['data']['data']
          console.log('chess-list req res: ', nextList)
          self.setData({
            gameList: fresh ? nextList : self.data.gameList.concat(nextList),
          });
          self.gameListPagination.index = pageIndex;
          self.gameListPagination.num = pageSize;
        }
      },
      fail({
        errMsg
      }) {
        wx.hideToast();
        console.log('chess-list req fail: ', errMsg)
      }
    });

  },

  gameListClickHandle(e) {
    const {
      index
    } = e.detail;
    const {
      id,
      nick,
      opponent,
      role,
      result,
    } = this.data.gameList[index];
    wx.navigateTo({
      url: `/pages/replay/index?id=${id}&nick=${nick}&opponent=${opponent}&role=${role}&result=${result}`,
    });
  }
});