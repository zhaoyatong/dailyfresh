from django.core.paginator import Paginator
from django.shortcuts import render, redirect, reverse
from django.views.generic import View
from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django_redis import get_redis_connection
from apps.user.models import Address
from apps.goods.models import GoodsSKU
from apps.order.models import OrderInfo, OrderGoods
from celery_tasks.tasks import send_active_email
import re
from apps.user.models import User
from utils.mixin import LoginRequiredMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired


# Create your views here.


class RegisterView(View):
    """注册"""

    def get(self, request):
        """显示注册页面"""
        return render(request, 'register.html')

    def post(self, request):
        # 接收数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 数据校验
        if not all([username, password, email]):
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请仔细阅读协议并同意'})

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None
        else:
            # 此处简写，应该判断user是否为None更严谨
            return render(request, 'register.html', {'errmsg': '用户已存在'})

        # 业务处理
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        # 生成邮件token
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info)
        token = token.decode()

        # 发送邮件
        send_active_email.delay(email, username, token)

        # 返回应答
        return redirect(reverse('goods:index'))


class ActiveView(View):
    def get(self, request, token):
        # 解密
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            # 获取待激活用户ID
            user_id = info['confirm']

            # 查询用户并激活
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            # 激活成功跳转到登录页
            return redirect(reverse('user:login'))
        except SignatureExpired:
            # 此处简写，应该提供新的发送激活链接入口，不然账户在有效时间内未激活则成了无效账户
            return HttpResponse('激活链接已过期')


class LoginView(View):
    """登录相关"""

    def get(self, request):
        # 判断是否记住用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''

        return render(request, 'login.html', {'username': username, 'checked': checked})

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('pwd')

        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '请完整填写用户名及密码'})

        # Django默认的用户校验
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)

                next_url = request.GET.get('next', reverse('goods:index'))

                response = redirect(next_url)

                # 判断是否记住用户名
                remember = request.POST.get('remember')
                if remember == 'on':
                    response.set_cookie('username', username, max_age=7 * 24 * 3600)
                else:
                    response.delete_cookie('username')

                return response
            else:
                return render(request, 'login.html', {'errmsg': '账户未激活'})
        else:
            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})


class LoginOutView(View):
    """退出登录"""

    def get(self, request):
        # 清除登录信息（session）
        logout(request)
        return redirect(reverse("goods:index"))


class UserInfoView(LoginRequiredMixin, View):
    """用户中心-信息页"""

    def get(self, request):
        # 获取用户地址信息
        user = request.user
        address = Address.object.get_default_address(user)

        # 获取用户浏览历史记录
        con = get_redis_connection('default')
        history_key = f'history_{user.id}'
        # 获取用户最新浏览的5个商品id
        sku_ids = con.lrange(history_key, 0, 4)

        # 循环获取用户浏览记录商品信息（这里会存在循环查5次数据库，也可以一次性查出来再通过循环排序）
        goods_li = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)

        # 组织上下文
        context = {'page': 'user',
                   'address': address,
                   'goods_li': goods_li}

        return render(request, 'user_center_info.html', context)


class UserOrderView(LoginRequiredMixin, View):
    """用户中心-订单页"""

    def get(self, request, page):
        # 获取用户的订单信息
        user = request.user
        orders = OrderInfo.objects.filter(user=user).order_by('-create_time')

        # 遍历获取订单商品的信息
        for order in orders:
            # 根据order_id查询订单商品信息
            order_skus = OrderGoods.objects.filter(order_id=order.order_id)

            # 遍历order_skus计算商品的小计
            for order_sku in order_skus:
                # 计算小计
                amount = order_sku.count * order_sku.price
                # 动态给order_sku增加属性amount,保存订单商品的小计
                order_sku.amount = amount

            # 动态给order增加属性，保存订单状态标题
            order.status_name = OrderInfo.ORDER_STATUS[order.order_status]
            # 动态给order增加属性，保存订单商品的信息
            order.order_skus = order_skus

        # 分页
        paginator = Paginator(orders, 1)

        # 获取第page页的内容
        try:
            page = int(page)
        except Exception as e:
            page = 1

        if page > paginator.num_pages:
            page = 1

        # 获取第page页的Page实例对象
        order_page = paginator.page(page)

        # todo: 进行页码的控制，页面上最多显示5个页码
        # 1.总页数小于5页，页面上显示所有页码
        # 2.如果当前页是前3页，显示1-5页
        # 3.如果当前页是后3页，显示后5页
        # 4.其他情况，显示当前页的前2页，当前页，当前页的后2页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        # 组织上下文
        context = {'order_page': order_page,
                   'pages': pages,
                   'page': 'order'}

        # 使用模板
        return render(request, 'user_center_order.html', context)


class AddressView(LoginRequiredMixin, View):
    """用户中心-地址页"""

    def get(self, request):
        user = request.user
        address = Address.object.get_default_address(user)

        return render(request, 'user_center_site.html', {'page': 'address', 'address': address})

    def post(self, request):
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        if not all([receiver, addr, phone]):
            return render(request, 'user_center_site.html', {'errmsg': '数据不完整'})
        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$', phone):
            return render(request, 'user_center_site.html', {'errmsg': '手机号格式不正确'})

        user = request.user

        address = Address.object.get_default_address(user)
        if address:
            is_default = False
        else:
            is_default = True

        Address.object.create(user=user,
                              receiver=receiver,
                              addr=addr,
                              zip_code=zip_code,
                              phone=phone,
                              is_default=is_default)

        return redirect(reverse('user:address'))
