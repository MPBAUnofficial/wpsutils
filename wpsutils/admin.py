from django.contrib import admin
from models import WpsServer, Process

class WpsServerAdmin(admin.ModelAdmin):
    prepopulated_fields = {"identifier":("display_name",)}

admin.site.register(WpsServer, WpsServerAdmin)
admin.site.register(Process)

