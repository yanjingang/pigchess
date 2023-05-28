import {
    cdnBase
} from '../config/index';
const imgPrefix = cdnBase;

const defaultDesc = [`${imgPrefix}/goods/details-1.png`];

const allGoods = [{
        id: '135686633',
        title: '2023-05-28 09:49:41',
        primaryImage: 'https://www.yanjingang.com/piglab/upload/230528/168523858325.png',
    },
    {
        id: '135686633',
        title: '2023-05-28 09:49:42',
        primaryImage: 'https://www.yanjingang.com/piglab/upload/230528/1685204717107.png',
    },
    {
        id: '135691628',
        title: '2023-05-28 09:49:43',
        primaryImage: 'https://www.yanjingang.com/piglab/upload/230528/1685204424998.png',
    }
];

/**
 * @param {string} id
 * @param {number} [available] 库存, 默认1
 */
export function genGood(id, available = 1) {
    const specID = ['135681624', '135681628'];
    if (specID.indexOf(id) > -1) {
        return allGoods.filter((good) => good.id === id)[0];
    }
    const item = allGoods[id % allGoods.length];
    return {
        ...item,
        id: `${id}`,
        available: available,
        desc: item?.desc || defaultDesc,
        images: item?.images || [item?.primaryImage],
    };
}