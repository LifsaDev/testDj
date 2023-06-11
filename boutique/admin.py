from django.contrib import admin
from . models import *
# Register your models here.
 
class AdminCustomer(admin.ModelAdmin):
    list_display = ('username','email','phone_number')
    search_fields = ('username',)

class AdminCategory(admin.ModelAdmin):
    list_display = ('name','date_added')
    search_fields = ('name',)
 
class AdminProduct(admin.ModelAdmin):
    list_display = ('name','reducedprice','actualprice','reduction','categorie','digital','available','date_added')
    search_fields = ('name',)
    list_filter = ('categorie',)
 
class AdminOrder(admin.ModelAdmin):
    list_display = ('customer','complete','transaction_id','shipping','get_cart_items')
    search_fields = ('transaction_id',)
 
class AdminOrderItem(admin.ModelAdmin):
    list_display = ('product','order','quantity','get_total','date_added')
    search_fields = ('order',)

class AdminShippingAdress(admin.ModelAdmin):
    list_display = ('customer','order','address','city','state','zipcode','date_added')
    search_fields = ('customer','order')
 
class AdminPayment(admin.ModelAdmin):
    list_display = ('order','payment_method','timestamp')
    search_fields = ('order',)
 
class AdminReview(admin.ModelAdmin):
    list_display = ('customer','product','rating','review_text','timestamp')
    search_fields = ('customer','product','rating')
 
class AdminRefund(admin.ModelAdmin):
    list_display = ('order','reason','timestamp')
    search_fields = ('order',)
 
class AdminCoupon(admin.ModelAdmin):
    list_display = ('code','discount','valid_from','valid_to')
    search_fields = ('code',)

class AdminVariation(admin.ModelAdmin):
    list_display = ('product','size','color','price','stock')
    search_fields = ('product',)
 

admin.site.register(Customer, AdminCustomer)
admin.site.register(Category, AdminCategory)
admin.site.register(Product, AdminProduct)
admin.site.register(Order, AdminOrder)
admin.site.register(OrderItem, AdminOrderItem)
admin.site.register(ShippingAddress, AdminShippingAdress)
admin.site.register(Payment, AdminPayment)
admin.site.register(Review, AdminReview)
admin.site.register(Refund, AdminRefund)
admin.site.register(Coupon, AdminCoupon)
admin.site.register(Variation, AdminVariation)
