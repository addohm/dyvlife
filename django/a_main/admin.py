from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import CustomerProfile, Appointment, Contact, Content, ContentMedia
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe


class CustomerProfileInline(admin.StackedInline):
    model = CustomerProfile
    can_delete = False
    verbose_name_plural = 'Customer Profile'
    fk_name = 'user'
    fields = (
        'first_contact', 'recent_contact', 'interest',
        'first_session', 'custnotes', 'magic_link'
    )
    readonly_fields = ('first_contact', 'magic_link')

    def magic_link(self, instance):
        if instance.magic_link_token and instance.magic_link_expires:
            return format_html(
                '<a href="{}?token={}" target="_blank">Magic Link</a> (expires {})',
                # You'll need to set up this URL in your urls.py
                reverse('magic_link_view'),
                instance.magic_link_token,
                instance.magic_link_expires.strftime("%Y-%m-%d %H:%M")
            )
        return "Not generated"
    magic_link.short_description = "Magic Link"


class CustomUserAdmin(UserAdmin):
    inlines = (CustomerProfileInline, )
    list_display = ('username', 'email', 'first_name', 'last_name',
                    'is_staff', 'get_interest', 'get_first_contact')
    list_select_related = ('profile', )

    def get_interest(self, instance):
        return instance.profile.interest
    get_interest.short_description = 'Interest'

    def get_first_contact(self, instance):
        return instance.profile.first_contact
    get_first_contact.short_description = 'First Contact'

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_contact', 'recent_contact',
                    'interest', 'first_session')
    list_filter = ('interest', 'first_contact', 'first_session')
    search_fields = ('user__username', 'user__first_name',
                     'user__last_name', 'custnotes')
    raw_id_fields = ('user',)
    date_hierarchy = 'first_contact'

    fieldsets = (
        (None, {
            'fields': ('user', 'first_contact', 'recent_contact')
        }),
        ('Session Info', {
            'fields': ('interest', 'first_session')
        }),
        ('Notes', {
            'fields': ('custnotes',)
        }),
        ('Magic Link', {
            'fields': ('magic_link_token', 'magic_link_expires'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('first_contact',)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('customer', 'date', 'kp_notes_short',
                    'fu_notes_short', 'invoiced', 'paid', 'created_at')
    list_filter = ('invoiced', 'paid', 'date')
    search_fields = ('customer__user__username', 'kp_notes', 'fu_notes')
    raw_id_fields = ('customer',)
    date_hierarchy = 'date'

    fieldsets = (
        (None, {
            'fields': ('customer', 'date')
        }),
        ('Notes', {
            'fields': ('kp_notes', 'fu_notes')
        }),
        ('Payment', {
            'fields': ('invoiced', 'paid')
        }),
    )

    def kp_notes_short(self, obj):
        return obj.kp_notes[:50] + '...' if obj.kp_notes else ''
    kp_notes_short.short_description = 'Key Points'

    def fu_notes_short(self, obj):
        return obj.fu_notes[:50] + '...' if obj.fu_notes else ''
    fu_notes_short.short_description = 'Follow Up'


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'when_sent',
                    'replied', 'when_replied', 'message_short')
    list_filter = ('replied', 'when_sent')
    search_fields = ('name', 'email', 'subject', 'message')
    date_hierarchy = 'when_sent'

    fieldsets = (
        (None, {
            'fields': ('name', 'email', 'subject', 'message')
        }),
        ('Status', {
            'fields': ('replied', 'when_replied')
        }),
    )

    def message_short(self, obj):
        return obj.message[:50] + '...' if obj.message else ''
    message_short.short_description = 'Message'


class ContentMediaInline(admin.TabularInline):
    model = ContentMedia
    extra = 1
    fields = ('file', 'thumbnail_preview', 'media_type', 'caption', 'order')
    readonly_fields = ('thumbnail_preview',)

    def thumbnail_preview(self, obj):
        if obj.file:
            return mark_safe(f'<img src="{obj.thumbnail.url}" width="100" />')
        return ""
    thumbnail_preview.short_description = 'Preview'


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'content_type', 'enabled',
                    'order', 'created_at', 'updated_at')
    list_filter = ('content_type', 'enabled')
    search_fields = ('title', 'description')
    inlines = (ContentMediaInline,)
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'content_type')
        }),
        ('Settings', {
            'fields': ('enabled', 'order')
        }),
    )


@admin.register(ContentMedia)
class ContentMediaAdmin(admin.ModelAdmin):
    list_display = ('content', 'media_type', 'thumbnail_preview',
                    'caption', 'order', 'created_at')
    list_filter = ('media_type',)
    search_fields = ('content__title', 'caption')
    date_hierarchy = 'created_at'

    def thumbnail_preview(self, obj):
        if obj.file:
            return mark_safe(f'<img src="{obj.thumbnail.url}" width="100" />')
        return ""
    thumbnail_preview.short_description = 'Preview'


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
