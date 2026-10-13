from api.models import File, Gallery, Promo, Report, Team, TeamRole, Year
from api.permissions import is_manager
from django import forms
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html


class YearAdmin(admin.ModelAdmin):
    list_display = ("name",)


class GalleryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "description",
        "date",
        "visibility",
        "type",
        "year",
        "view",
    )
    ordering = ("date",)


class FileAdmin(admin.ModelAdmin):
    list_display = ("gallery", "file_full_name", "file_name", "file_extension", "link")
    ordering = ("gallery",)


class PromoAdmin(admin.ModelAdmin):
    list_display = ("name", "first_year")


class ReportAdmin(admin.ModelAdmin):
    list_display = ("file", "reporter", "category", "message", "created_at")
    list_filter = ("category",)
    ordering = ("-created_at",)


class ForManagers:
    """
    Opens a part of the admin to those who run the galleries.

    The admin goes by permissions set account by account, and only superusers
    have them all. The site has one role for running it (api.permissions):
    what belongs to that role is opened here to whoever holds it.
    """

    def has_module_permission(self, request):
        return is_manager(request.user)

    def has_view_permission(self, request, obj=None):
        return is_manager(request.user)

    def has_add_permission(self, request, obj=None):
        return is_manager(request.user)

    def has_change_permission(self, request, obj=None):
        return is_manager(request.user)

    def has_delete_permission(self, request, obj=None):
        return is_manager(request.user)


class TeamRoleInline(ForManagers, admin.TabularInline):
    model = TeamRole
    fields = ("section", "title", "people", "order")
    extra = 3

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "people":
            # Eight photographers do not fit in a one-line field.
            kwargs["widget"] = forms.Textarea(attrs={"rows": 2, "cols": 48})
        return super().formfield_for_dbfield(db_field, request, **kwargs)


class TeamAdmin(ForManagers, admin.ModelAdmin):
    list_display = ("__str__", "current", "people_count", "created_at")
    inlines = [TeamRoleInline]
    readonly_fields = ("photo_preview",)
    # "Enregistrer en tant que nouveau" : the handover starts from last year's
    # team, with its sections and roles already laid out.
    save_as = True
    fieldsets = (
        (
            None,
            {
                "fields": ("name", "photo", "photo_preview", "current"),
                "description": (
                    "<p>La page d'accueil du site affiche l'équipe cochée "
                    "« affichée sur le site » : sa photo, son numéro de "
                    "promotion et ses membres.</p>"
                    "<p><strong>Passation.</strong> Ouvrir l'équipe de l'an "
                    "dernier, changer le numéro de promotion, choisir la "
                    "nouvelle photo, remplacer les noms, puis cliquer sur "
                    "« Enregistrer en tant que nouveau ». L'ancienne équipe "
                    "est conservée, et quitte la page d'accueil dès que la "
                    "nouvelle y est affichée.</p>"
                    "<p>À faire aussi à la rentrée : ajouter l'année scolaire "
                    "(« Années scolaires »), et donner l'accès à la gestion "
                    "aux nouveaux membres (« Utilisateurs », cocher les "
                    "comptes, action « Donner l'accès à la gestion des "
                    "galeries »).</p>"
                ),
            },
        ),
    )

    def save_model(self, request, team, form, change):
        super().save_model(request, team, form, change)
        if team.current and not team.photo:
            # Easily done when starting from last year's team: its picture
            # does not come along, and the home page is left without one.
            self.message_user(
                request,
                "Cette équipe est affichée sur le site sans photo de groupe : "
                "pensez à en choisir une.",
                messages.WARNING,
            )

    @admin.display(description="aperçu")
    def photo_preview(self, team):
        if not team.photo:
            return "Aucune photo pour l'instant."
        return format_html(
            '<img src="{}" alt="" style="max-width: 420px; border-radius: 8px">',
            team.photo.url,
        )

    @admin.display(description="membres")
    def people_count(self, team):
        return sum(
            len(role["people"])
            for s in team.on_display()["sections"]
            for role in s["roles"]
        )


@admin.action(description="Donner l'accès à la gestion des galeries")
def grant_management(modeladmin, request, queryset):
    count = queryset.update(is_staff=True)
    modeladmin.message_user(
        request, f"{count} compte(s) ont maintenant accès à la gestion."
    )


@admin.action(description="Retirer tout accès à la gestion et à l'administration")
def revoke_management(modeladmin, request, queryset):
    # Never the account in use: the last administrator would lock itself out.
    others = queryset.exclude(pk=request.user.pk)
    kept = queryset.count() - others.count()
    count = others.update(is_staff=False, is_superuser=False)
    modeladmin.message_user(
        request, f"{count} compte(s) n'ont plus aucun accès de gestion."
    )
    if kept:
        modeladmin.message_user(
            request,
            "Votre propre compte n'a pas été modifié : un autre administrateur doit le faire.",
            messages.WARNING,
        )


class AccountAdmin(UserAdmin):
    """The accounts, with the two things a handover asks for in one click."""

    actions = [grant_management, revoke_management]


# Register your models here.
admin.site.register(Year, YearAdmin)
admin.site.register(Promo, PromoAdmin)
admin.site.register(Gallery, GalleryAdmin)
admin.site.register(File, FileAdmin)
admin.site.register(Report, ReportAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.unregister(User)
admin.site.register(User, AccountAdmin)
admin.site.site_header = "Administration du Ponthé"
admin.site.site_title = "Ponthé"
admin.site.index_title = "Données du site"
