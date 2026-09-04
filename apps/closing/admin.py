from django.contrib import admin

from .models import (
    ActivityEntry,
    ActivityType,
    AnimationAttendance,
    AnimationSession,
    AnimationType,
    DayClosing,
)

admin.site.register(ActivityType)
admin.site.register(ActivityEntry)
admin.site.register(AnimationType)
admin.site.register(AnimationSession)
admin.site.register(AnimationAttendance)
admin.site.register(DayClosing)
