from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Party, QueueItem

admin.site.register(User, UserAdmin)


class QueueItemInline(admin.TabularInline):
  model = QueueItem
  readonly_fields = ('identifier', 'title', 'artist_name',
                     'playing_start_time', 'duration_ms', 'user', 'service')
  extra = 0

@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
  fields = ('name', 'playing_item', 'theme', 'users')
  readonly_fields = ('users', )
  inlines = (QueueItemInline, )

  def users(self, obj):
    return ', '.join([user.username for user in obj.users])
