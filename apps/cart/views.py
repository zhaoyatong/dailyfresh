from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse
from apps.goods.models import GoodsSKU
from django_redis import get_redis_connection
from utils.mixin import LoginRequiredMixin


# Create your views here.

class CartAddView(View):
    """购物车添加"""

    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 10001, 'errmsg': '请先登录'})

        # 接收数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 数据校验
        if not all([sku_id, count]):
            return JsonResponse({'res': 10002, 'errmsg': '数据不完整'})

        if not count.isdigit():
            return JsonResponse({'res': 10003, 'errmsg': '商品数量出错'})

        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 10004, 'errmsg': '商品不存在'})

        # 业务处理
        conn = get_redis_connection('default')
        cart_key = f'cart_{user.id}'
        # 先尝试获取sku_id的值，若不存在添加，存在累加
        cart_count = conn.hget(cart_key, sku_id)

        count = int(count)
        if cart_count:
            count += int(cart_count)

        if count > sku.stock:
            return JsonResponse({'res': 10005, 'errmsg': '商品库存不足'})

        conn.hset(cart_key, sku_id, count)

        # 购物车商品条目
        total_count = conn.hlen(cart_key)

        return JsonResponse({'res': 0, 'total_count': total_count, 'errmsg': '添加成功'})


class CartInfoView(LoginRequiredMixin, View):
    """购物车页面"""

    def get(self, request):
        # 获取用户
        user = request.user
        # redis链接
        conn = get_redis_connection('default')
        cart_key = f'cart_{user.id}'
        cart_dict = conn.hgetall(cart_key)

        skus = []
        total_count = 0
        total_price = 0
        # 遍历获取商品信息
        for sku_id, count in cart_dict.items():
            sku = GoodsSKU.objects.get(id=sku_id)
            # 动态给sku增加属性
            sku.count = int(count)
            sku.amount = sku.price * int(count)

            # 添加
            skus.append(sku)
            total_count += sku.count
            total_price += sku.amount

        # 组织上下文
        context = {'total_count': total_count,
                   'total_price': total_price,
                   'skus': skus}

        return render(request, 'cart.html', context)


class CartUpdateView(View):
    """更新购物车"""

    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            # 用户未登录
            return JsonResponse({'res': 10001, 'errmsg': '请先登录'})

        # 接收数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 数据校验
        if not all([sku_id, count]):
            return JsonResponse({'res': 10002, 'errmsg': '数据不完整'})

        # 校验添加的商品数量
        try:
            count = int(count)
        except Exception as e:
            # 数目出错
            return JsonResponse({'res': 10003, 'errmsg': '商品数目出错'})

        # 校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            # 商品不存在
            return JsonResponse({'res': 10004, 'errmsg': '商品不存在'})

        # 业务处理:更新购物车记录
        conn = get_redis_connection('default')
        cart_key = f'cart_{user.id}'

        # 校验商品的库存
        if count > sku.stock:
            return JsonResponse({'res': 10005, 'errmsg': '商品库存不足'})

        # 更新
        conn.hset(cart_key, sku_id, count)

        # 计算用户购物车中商品的总件数 {'1':5, '2':3}
        total_count = 0
        vals = conn.hvals(cart_key)
        for val in vals:
            total_count += int(val)

        # 返回应答
        return JsonResponse({'res': 0, 'total_count': total_count, 'message': '更新成功'})


# 删除购物车记录
# 采用ajax post请求
# 前端需要传递的参数:商品的id(sku_id)
# /cart/delete
class CartDeleteView(View):
    """购物车记录删除"""

    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            # 用户未登录
            return JsonResponse({'res': 10001, 'errmsg': '请先登录'})

        # 接收参数
        sku_id = request.POST.get('sku_id')

        # 数据的校验
        if not sku_id:
            return JsonResponse({'res': 10002, 'errmsg': '无效的商品id'})

        # 校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            # 商品不存在
            return JsonResponse({'res': 10003, 'errmsg': '商品不存在'})

        # 业务处理:删除购物车记录
        conn = get_redis_connection('default')
        cart_key = f'cart_{user.id}'

        # 删除 hdel
        conn.hdel(cart_key, sku_id)

        # 计算用户购物车中商品的总件数 {'1':5, '2':3}
        total_count = 0
        vals = conn.hvals(cart_key)
        for val in vals:
            total_count += int(val)

        # 返回应答
        return JsonResponse({'res': 0, 'total_count': total_count, 'message': '删除成功'})
