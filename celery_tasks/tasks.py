# 使用celery处理耗时任务

from django.conf import settings
from django.core.mail import send_mail
from django.template import loader
from apps.goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner
from celery import Celery

# 创建Celery对象
cel = Celery('celery_tasks.tasks', broker=settings.CELERY_BROKER, backend=settings.CELERY_BACKEND)


# 发送邮件
@cel.task
def send_active_email(to_email, username, token):
    """发送激活邮件"""
    subject = '天天生鲜账户激活'
    message = ''
    sender = settings.DEFAULT_FROM_EMAIL
    receiver = [to_email]
    html_message = f'<h1>{username},欢迎您成为天天生鲜注册会员</h1>请点击下方超链接激活您的账户：<br />' \
                   f'<a href="{settings.REALM_NAME + token}">请点此激活</a> '
    send_mail(subject, message, sender, receiver, html_message=html_message)


@cel.task
def generate_static_index_html():
    """生成首页静态页面"""

    # 获取商品种类信息
    goods_types = GoodsType.objects.all()

    # 获取轮播商品信息
    goods_banners = IndexGoodsBanner.objects.all().order_by('index')

    # 获取促销活动信息
    promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

    # 获取分类商品展示信息
    for goods_type in goods_types:
        image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1)
        title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0)

        type.image_banners = image_banners
        type.title_banners = title_banners

    # 组织上下文
    context = {'types': goods_types,
               'goods_banners': goods_banners,
               'promotion_banners': promotion_banners
               }

    # 使用模板生成HTML
    temp = loader.get_template('static_index.html')
    static_index_html = temp.render(context)

    # 生成静态文件
    save_path = settings.STATICFILES_DIRS + '/index.html'
    with open(save_path, 'w') as f:
        f.write(static_index_html)
