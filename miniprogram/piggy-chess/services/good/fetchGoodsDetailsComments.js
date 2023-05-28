import { config } from '../../config/index';

/** 获取商品详情页评论数 */
function mockFetchGoodDetailsCommentsCount(id = 0) {
  const { delay } = require('../_utils/delay');
  const {
    getGoodsDetailsCommentsCount,
  } = require('../../model/detailsComments');
  return delay().then(() => getGoodsDetailsCommentsCount(id));
}

/** 获取商品详情页评论数 */
export function getGoodsDetailsCommentsCount(id = 0) {
  if (config.useMock) {
    return mockFetchGoodDetailsCommentsCount(id);
  }
  return new Promise((resolve) => {
    resolve('real api');
  });
}

/** 获取商品详情页评论 */
function mockFetchGoodDetailsCommentList(id = 0) {
  const { delay } = require('../_utils/delay');
  const { getGoodsDetailsComments } = require('../../model/detailsComments');
  return delay().then(() => getGoodsDetailsComments(id));
}

/** 获取商品详情页评论 */
export function getGoodsDetailsCommentList(id = 0) {
  if (config.useMock) {
    return mockFetchGoodDetailsCommentList(id);
  }
  return new Promise((resolve) => {
    resolve('real api');
  });
}
