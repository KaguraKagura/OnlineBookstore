from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Book)
admin.site.register(Author)
admin.site.register(BookOrder)
admin.site.register(BookInOrder)
admin.site.register(Comment)
admin.site.register(Offense)
admin.site.register(Question)
admin.site.register(TrustedCustomer)
admin.site.register(UntrustedCustomer)
