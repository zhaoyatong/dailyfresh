from django.contrib import admin
from django.core.cache import cache
from apps.goods.models import *
from celery_tasks.tasks import generate_static_index_html


# Register your models here.

class BaseModelAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        """增加或修改时调用"""
        super().save_model(request, obj, form, change)

        # 调用celery重新生成静态页
        generate_static_index_html.delay()

        # 清除首页缓存
        cache.delete('index_page_data')

    def delete_model(self, request, obj):
        """删除时调用"""
        super().delete_model(request, obj)

        # 调用celery重新生成静态页
        generate_static_index_html.delay()

        # 清除首页缓存
        cache.delete('index_page_data')


admin.site.register(GoodsType, BaseModelAdmin)
admin.site.register(GoodsSKU)
admin.site.register(Goods)
admin.site.register(GoodsImage)
admin.site.register(IndexGoodsBanner, BaseModelAdmin)
admin.site.register(IndexTypeGoodsBanner, BaseModelAdmin)
admin.site.register(IndexPromotionBanner, BaseModelAdmin)
