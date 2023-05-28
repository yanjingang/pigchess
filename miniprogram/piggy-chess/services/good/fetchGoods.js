import {
  config
} from '../../config/index';

/** 获取棋谱列表 */
function mockFetchGoodsList(pageIndex = 1, pageSize = 20) {
  const {
    delay
  } = require('../_utils/delay');
  const {
    getGoodsList
  } = require('../../model/goods');
  return delay().then(() =>
    getGoodsList(pageIndex, pageSize).map((item) => {
      return {
        id: item.id,
        thumb: item.primaryImage,
        title: item.nick,
      };
    }),
  );
}

/** 获取棋谱列表 */
export function fetchGoodsList(pageIndex = 1, pageSize = 20) {
  if (config.useMock) {
    return mockFetchGoodsList(pageIndex, pageSize);
  }
  return new Promise((resolve) => {
    resolve('real api');
  });
}