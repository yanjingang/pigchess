/* eslint-disable no-param-reassign */
import {
  config
} from '../../config/index';

/** 获取搜索历史 */
function mockSearchResult(params) {
  const {
    delay
  } = require('../_utils/delay');
  const {
    getSearchResult
  } = require('../../model/search');

  const data = getSearchResult(params);

  if (data.spuList.length) {
    data.spuList.forEach((item) => {
      item.id = item.id;
      item.thumb = item.primaryImage;
      item.nick = item.nick;
      item.price = item.minSalePrice;
      item.originPrice = item.maxLinePrice;
      if (item.spuTagList) {
        item.tags = item.spuTagList.map((tag) => ({
          title: tag.nick
        }));
      } else {
        item.tags = [];
      }
    });
  }
  return delay().then(() => {
    return data;
  });
}

/** 获取搜索历史 */
export function getSearchResult(params) {
  if (config.useMock) {
    return mockSearchResult(params);
  }
  return new Promise((resolve) => {
    resolve('real api');
  });
}