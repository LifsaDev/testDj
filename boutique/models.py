from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator,MinValueValidator
from decimal import Decimal


class Customer(models.Model):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)
    username = models.CharField(max_length=200, null=True)
    email = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=15, null=True)

    def __str__(self):
        return self.username

class Category(models.Model):
    name = models.CharField(max_length=200, null=True)
    date_added=models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering=['-date_added',]
	
    def __str__(self):
        return self.name
    
class Product(models.Model):
    name = models.CharField(max_length=200)
    reducedprice = models.FloatField()
    actualprice = models.FloatField(null=True, blank=True)
    categorie = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='category_products')
    image = models.ImageField(upload_to='products/',null=True, blank=True)
    digital = models.BooleanField(default=False,null=True, blank=True)
    available = models.BooleanField(default=True,null=True, blank=True)
    description = models.TextField()
    date_added=models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering=['-date_added',]

    def __str__(self):
        return self.name

    @property
    def imageURL(self):
        try:
            url = self.image.url
        except:
            url = ''
        return url
    
    @property
    def reduction(self):
        return round(abs((self.actualprice-self.reducedprice)*100/self.actualprice),2)
    @property
    def f_reducedprice(self):
        return '{:,.2f}'.format(self.reducedprice)
    @property
    def f_actualprice(self):
        return '{:,.1f}'.format(self.actualprice)
class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    date_ordered = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=100, null=True)
    class Meta:
        ordering=['-date_ordered',]

    def __str__(self):
        return str(self.id)
            
    @property
    def shipping(self):
        shipping = False
        orderitems = self.orderitem_set.all()
        for i in orderitems:
            if i.product.digital == False:
                shipping = True
        return shipping

    @property
    def get_cart_total(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.get_total  for item in orderitems])
        return total 

    @property
    def get_cart_items(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.quantity for item in orderitems])
        return total 

class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField(default=0, null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering=['-date_added',]

    @property
    def get_total(self):
        total = self.product.reducedprice * self.quantity
        return total

class ShippingAddress(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    address = models.CharField(max_length=200, null=False)
    city = models.CharField(max_length=200, null=False)
    state = models.CharField(max_length=200, null=False)
    zipcode = models.CharField(max_length=200, null=False)
    date_added = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering=['-date_added',]

    def __str__(self):
        return self.address

class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.payment_method

class Review(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review_text = models.TextField(max_length=500)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.username} - {self.product.name}"

class Refund(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    reason = models.TextField(max_length=500)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order.customer.username} - {self.order.id}"

 
class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()

    def __str__(self):
        return self.code
 

class Variation(models.Model):
    SIZE_CHOICES = (
        ('XS', 'XS'),
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
        ('XXL', 'XXL'),
        ('XXXL', 'XXXL'),
    )
    COLOR_CHOICES = (
        ('RED', 'Red'),
        ('GREEN', 'Green'),
        ('BLUE', 'Blue'),
        ('YELLOW', 'Yellow'),
        ('ORANGE', 'Orange')
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=5, choices=SIZE_CHOICES, null=True, blank=True)
    color = models.CharField(max_length=10, choices=COLOR_CHOICES, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal('0.01'))])
    stock = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.product.name} - {self.size} - {self.color}"
