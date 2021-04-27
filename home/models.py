import django.core.validators as v
from django.db import models
from django.contrib.auth.models import User


# Create your models here.


class Book(models.Model):
    isbn = models.CharField('ISBN', max_length=13, primary_key=True, help_text="13 characters")
    title = models.CharField(max_length=100)
    publisher = models.CharField(max_length=100)
    publication_date = models.DateField()
    subject = models.CharField(max_length=100)
    keywords = models.CharField(max_length=100)
    language = models.CharField(max_length=30)
    page_count = models.IntegerField(validators=[v.MinValueValidator(0)])
    stock_level = models.IntegerField(validators=[v.MinValueValidator(0)])
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[v.MinValueValidator(0)])

    def __str__(self):
        return f'Title:{self.title} ISBN:{self.isbn}'


class Author(models.Model):
    isbn = models.ForeignKey(Book, on_delete=models.RESTRICT)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['isbn', 'first_name', 'last_name'], name='unique record')]

    def __str__(self):
        return f'ISBN:{self.isbn} Name:{self.first_name} {self.last_name}'


class Customer(User):
    address = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=10)
    banned = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.username}'


class BookOrder(models.Model):
    order_number = models.AutoField(primary_key=True)
    username = models.ForeignKey(Customer, on_delete=models.RESTRICT)
    order_time = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'order number:{self.order_time} order_time:{self.order_time}'


class BookInOrder(models.Model):
    order_number = models.ForeignKey(BookOrder, on_delete=models.RESTRICT)
    isbn = models.ForeignKey(Book, on_delete=models.RESTRICT)
    count = models.IntegerField(validators=[v.MinValueValidator(1)])

    def __str__(self):
        return f'order number:{self.order_number} ISBN:{self.isbn} count:{self.count}'


class ShoppingCart(models.Model):
    username = models.ForeignKey(Customer, on_delete=models.RESTRICT)
    isbn = models.ForeignKey(Book, on_delete=models.RESTRICT)
    count = models.IntegerField(validators=[v.MinValueValidator(1)])

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['username', 'isbn'], name='unique item in cart')
        ]

    def __str__(self):
        return f'Username: {self.username} ISBN: {self.isbn} Count: {self.count}'


class Comment(models.Model):
    username = models.ForeignKey(Customer, on_delete=models.RESTRICT)
    isbn = models.ForeignKey(Book, on_delete=models.RESTRICT)
    score = models.IntegerField(validators=[v.MinValueValidator(1), v.MaxValueValidator(10)])
    comment_text = models.TextField(max_length=300)
    time = models.DateTimeField(auto_now_add=True)
    useless_count = models.IntegerField(default=0, validators=[v.MinValueValidator(0)])
    useful_count = models.IntegerField(default=0, validators=[v.MinValueValidator(0)])
    very_useful_count = models.IntegerField(default=0, validators=[v.MinValueValidator(0)])

    class Meta:
        constraints = [models.UniqueConstraint(fields=['username', 'isbn'], name='unique comment')]

    def __str__(self):
        return f'login name:{self.username}\nisbn:{self.isbn}'


class Manager(User):
    def __str__(self):
        return f'{self.username}'


class Offense(models.Model):
    username = models.ForeignKey(Customer, on_delete=models.RESTRICT)
    offense_count = models.IntegerField(validators=[v.MinValueValidator(1)])

    def __str__(self):
        return f'username:{self.username}\ncount:{self.offense_count}'


class Question(models.Model):
    question_id = models.AutoField(primary_key=True)
    username = models.ForeignKey(Customer, on_delete=models.RESTRICT)
    time_asked = models.DateTimeField(auto_now_add=True)
    question = models.TextField(max_length=300)
    answer = models.TextField(max_length=300, default='THIS QUESTION HAS NOT BEEN ANSWERED, PLEASE CHECK BACK LATER')

    def __str__(self):
        return f'question id:{self.question_id}'


class TrustedCustomer(models.Model):
    username = models.ForeignKey(Customer, on_delete=models.RESTRICT, related_name='t_username')
    trusted_username = models.ForeignKey(Customer, on_delete=models.RESTRICT, related_name='t_trusted_username')

    class Meta:
        constraints = [models.UniqueConstraint(fields=['username', 'trusted_username'], name='unique trust pair')]

    def __str__(self):
        return f'{self.username}'


class UntrustedCustomer(models.Model):
    username = models.ForeignKey(Customer, on_delete=models.RESTRICT, related_name='ut_username')
    untrusted_username = models.ForeignKey(Customer, on_delete=models.RESTRICT,
                                           related_name='ut_untrusted_username')

    class Meta:
        constraints = [models.UniqueConstraint(fields=['username', 'untrusted_username'], name='unique untrust pair')]

    def __str__(self):
        return f'{self.username}'
