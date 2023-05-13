// import { fetchUserCenter } from '../../services/usercenter/fetchUsercenter';
import Toast from 'tdesign-miniprogram/toast/index';

const menuData = [
    [
        /* {
          title: '收货地址',
          tit: '',
          url: '',
          type: 'address',
        },
        {
          title: '优惠券',
          tit: '',
          url: '',
          type: 'coupon',
        }, */
        {
            title: '积分',
            tit: '0',
            url: '',
            type: 'point',
        },
    ],
    [
        /* {
          title: '关于',
          tit: '',
          url: '',
          type: 'help-center',
        }, */
        {
            title: '客服热线',
            tit: '',
            url: '',
            type: 'service',
            icon: 'service',
        },
    ],
];

const orderTagInfos = [{
        title: '待付款',
        iconName: 'wallet',
        orderNum: 0,
        tabType: 5,
        status: 1,
    },
    {
        title: '待发货',
        iconName: 'deliver',
        orderNum: 0,
        tabType: 10,
        status: 1,
    },
    {
        title: '待收货',
        iconName: 'package',
        orderNum: 0,
        tabType: 40,
        status: 1,
    },
    {
        title: '待评价',
        iconName: 'comment',
        orderNum: 0,
        tabType: 60,
        status: 1,
    },
    {
        title: '退款/售后',
        iconName: 'exchang',
        orderNum: 0,
        tabType: 0,
        status: 1,
    },
];

const getDefaultData = () => ({
    showMakePhone: false,
    userInfo: {
        avatarUrl: '',
        nickName: '正在登录...',
        phoneNumber: '',
    },
    menuData,
    orderTagInfos,
    customerServiceInfo: {
        servicePhone: '+8613810526265',
        serviceTimeDuration: '每周六至周日 9:00-12:00  13:00-15:00',
    },
    currAuthStep: 1,
    showKefu: true,
    versionNo: '',
});

Page({
    data: getDefaultData(),

    onLoad() {
        this.getVersionInfo();
    },

    onShow() {
        this.getTabBar().init();
        this.init();
    },
    onPullDownRefresh() {
        this.init();
    },

    init() {
        this.loadStorageUserInfo();
    },
    loadStorageUserInfo() {
        // 加载缓存用户信息
        const userInfo = wx.getStorageSync('userInfo');
        console.log("getStorageInfo:");
        console.log(userInfo);
        if (userInfo && userInfo.nickName != '') {
            this.setData({
                userInfo: userInfo,
                currAuthStep: 3,
            });
        }
    },
    fetUseriInfoHandle() {
        // 加载缓存用户信息
        this.loadStorageUserInfo();
        // 微信用户授权
        wx.getUserProfile({
            desc: '获取您的微信个人信息',
            success: (res) => {
                console.log("getUserProfile res:");
                console.log(res.userInfo);
                this.setData({
                    userInfo: res.userInfo,
                    // hasUserInfo: true,
                    currAuthStep: 3,
                    // menuData,
                });
                wx.setStorageSync('userInfo', res.userInfo)
                wx.stopPullDownRefresh();
            },
            fail: function (e) {
                // wx.showToast({
                //   title: '你选择了取消',
                //   icon: "none",
                //   duration: 1500,
                //   mask: true
                // })
                console.log("wx.getUserProfile fail!")
            }
        });
        // console.log("getUserProfile done");

        // fetchUserCenter().then(
        //   ({
        //     userInfo,
        //     countsData,
        //     orderTagInfos: orderInfo,
        //     customerServiceInfo,
        //   }) => {
        //     // eslint-disable-next-line no-unused-expressions
        //     menuData?.[0].forEach((v) => {
        //       countsData.forEach((counts) => {
        //         if (counts.type === v.type) {
        //           // eslint-disable-next-line no-param-reassign
        //           v.tit = counts.num;
        //         }
        //       });
        //     });
        //     const info = orderTagInfos.map((v, index) => ({
        //       ...v,
        //       ...orderInfo[index],
        //     }));


        //     this.setData({
        //       userInfo,
        //       menuData,
        //       orderTagInfos: info,
        //       customerServiceInfo,
        //       currAuthStep: 1,
        //     });
        //     wx.stopPullDownRefresh();
        //   },
        // );
    },

    onClickCell({
        currentTarget
    }) {
        const {
            type
        } = currentTarget.dataset;

        switch (type) {
            case 'address': {
                wx.navigateTo({
                    url: '/pages/usercenter/address/list/index'
                });
                break;
            }
            case 'service': {
                this.openMakePhone();
                break;
            }
            case 'help-center': {
                Toast({
                    context: this,
                    selector: '#t-toast',
                    message: '你点击了关于',
                    icon: '',
                    duration: 1000,
                });
                break;
            }
            case 'point': {
                // Toast({
                //   context: this,
                //   selector: '#t-toast',
                //   message: '你的积分未0分',
                //   icon: '',
                //   duration: 1000,
                // });
                break;
            }
            case 'coupon': {
                wx.navigateTo({
                    url: '/pages/coupon/coupon-list/index'
                });
                break;
            }
            default: {
                Toast({
                    context: this,
                    selector: '#t-toast',
                    message: '未知跳转',
                    icon: '',
                    duration: 1000,
                });
                break;
            }
        }
    },

    jumpNav(e) {
        const status = e.detail.tabType;

        if (status === 0) {
            wx.navigateTo({
                url: '/pages/order/after-service-list/index'
            });
        } else {
            wx.navigateTo({
                url: `/pages/order/order-list/index?status=${status}`
            });
        }
    },

    jumpAllOrder() {
        wx.navigateTo({
            url: '/pages/order/order-list/index'
        });
    },

    openMakePhone() {
        this.setData({
            showMakePhone: true
        });
    },

    closeMakePhone() {
        this.setData({
            showMakePhone: false
        });
    },

    call() {
        wx.makePhoneCall({
            phoneNumber: this.data.customerServiceInfo.servicePhone,
        });
    },

    gotoUserEditPage() {
        const {
            currAuthStep
        } = this.data;
        // console.log("gotoUserEditPage currAuthStep:");
        // console.log(currAuthStep);
        if (currAuthStep === 2) {
            wx.navigateTo({
                url: '/pages/usercenter/person-info/index'
            });
        } else {
            this.fetUseriInfoHandle();
        }
    },

    getVersionInfo() {
        const versionInfo = wx.getAccountInfoSync();
        const {
            version,
            envVersion = __wxConfig
        } = versionInfo.miniProgram;
        this.setData({
            versionNo: envVersion === 'release' ? version : envVersion,
        });
    },
});