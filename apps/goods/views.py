from django.shortcuts import render, redirect, reverse
from django.views.generic import View
from apps.goods.models import GoodsType, GoodsSKU, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner
from apps.order.models import OrderGoods
from django_redis import get_redis_connection
from django.core.cache import cache
from django.core.paginator import Paginator


# Create your views here.


# 127.0.0.1:8000
class IndexView(View):
    """首页"""

    def get(self, request):
        # 通过缓存查询数据
        context = cache.get('index_page_data')

        if context is None:
            # 获取商品种类信息
            goods_types = GoodsType.objects.all()

            # 获取轮播商品信息
            goods_banners = IndexGoodsBanner.objects.all().order_by('index')

            # 获取促销活动信息
            promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

            # 获取分类商品展示信息
            for good_type in goods_types:
                image_banners = IndexTypeGoodsBanner.objects.filter(type=good_type, display_type=1)
                title_banners = IndexTypeGoodsBanner.objects.filter(type=good_type, display_type=0)

                good_type.image_banners = image_banners
                good_type.title_banners = title_banners

            # 组织上下文
            context = {'types': goods_types,
                       'goods_banners': goods_banners,
                       'promotion_banners': promotion_banners}

            # 设置缓存
            cache.set('index_page_data', context, 3600)

        # 购物车数量
        user = request.user
        cart_count = 0
        if user.is_authenticated:
            conn = get_redis_connection('default')
            cart_key = f'cart_{user.id}'
            cart_count = conn.hlen(cart_key)

        # 添加购物车数量到上下文
        context.update(cart_count=cart_count)

        return render(request, 'index.html', context)


class DetailView(View):
    """详情页"""

    def get(self, request, goods_id):
        try:
            sku = GoodsSKU.objects.get(id=goods_id)
        except GoodsSKU.DoesNotExist:
            return redirect(reverse('goods:index'))

        # 获取商品分类信息
        types = GoodsType.objects.all()

        # 获取商品评论信息
        sku_orders = OrderGoods.objects.filter(sku=sku).exclude(comment='').order_by('-update_time')

        # 获取新品信息
        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by('-create_time')[:2]

        # 获取同一个SPU的其他规格商品
        same_spu_skus = GoodsSKU.objects.filter(goods=sku.goods).exclude(id=goods_id)

        # 购物车数量
        user = request.user
        cart_count = 0
        if user.is_authenticated:
            conn = get_redis_connection('default')
            cart_key = f'cart_{user.id}'
            cart_count = conn.hlen(cart_key)

            # 添加用户浏览记录
            history_key = f'history_{user.id}'
            # 先移除浏览的记录，再添加
            conn.lrem(history_key, 0, goods_id)
            conn.lpush(history_key, goods_id)
            # 只保存5条
            conn.ltrim(history_key, 0, 4)

        # 组织上下文
        context = {'sku': sku,
                   'types': types,
                   'sku_orders': sku_orders,
                   'new_skus': new_skus,
                   'cart_count': cart_count,
                   'same_spu_skus': same_spu_skus}

        return render(request, 'detail.html', context)


class ListView(View):
    """列表页"""

    def get(self, request, type_id, page):
        # 获取种类信息
        try:
            type = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist:
            return redirect(reverse('goods:index'))

        # 获取商品分类信息
        types = GoodsType.objects.all()

        # 获取分类商品信息
        sort = request.GET.get('sort')
        if sort == 'price':
            skus = GoodsSKU.objects.filter(type=type).order_by('price')
        elif sort == 'hot':
            skus = GoodsSKU.objects.filter(type=type).order_by('-sales')
        else:
            sort = 'default'
            skus = GoodsSKU.objects.filter(type=type).order_by('-id')

        # 对数据进行分页
        paginator = Paginator(skus, 20)
        try:
            page = int(page)
        except Exception as e:
            page = 1

        if page > paginator.num_pages:
            page = 1

        skus_page = paginator.page(page)

        # 控制页面显示5个页码
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        # 获取新品信息
        new_skus = GoodsSKU.objects.filter(type=type).order_by('-create_time')[:2]

        # 购物车数量
        user = request.user
        cart_count = 0
        if user.is_authenticated:
            conn = get_redis_connection('default')
            cart_key = f'cart_{user.id}'
            cart_count = conn.hlen(cart_key)

        # 组织上下文
        context = {'type': type,
                   'types': types,
                   'skus_page': skus_page,
                   'new_skus': new_skus,
                   'cart_count': cart_count,
                   'pages': pages,
                   'sort': sort}

        return render(request, 'list.html', context)
