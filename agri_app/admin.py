from django.contrib import admin
from .models import User, Product, Equipment, NewsUpdate, Notification

# Register your models here so they appear in the Admin Panel
admin.site.register(User)
admin.site.register(Product)
admin.site.register(Equipment)
admin.site.register(NewsUpdate)

# Let's make the Notification panel easy to read
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'is_read', 'created_at')
    list_filter = ('is_read',)

admin.site.register(Notification, NotificationAdmin)