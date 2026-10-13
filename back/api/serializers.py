import random

from api.models import File, Gallery, Promo, Report, Year
from rest_framework import serializers

random.seed()


class GallerySerializer(serializers.ModelSerializer):
    sticker_url = serializers.SerializerMethodField("get_sticker")

    def get_sticker(self, gal):
        files = File.objects.filter(gallery=gal)
        if files.count() >= 1:
            i = random.randint(0, files.count() - 1)
            return files[i].link + "/thumbnails/" + files[i].file_full_name
        else:
            return ""

    class Meta:
        model = Gallery
        fields = [
            "id",
            "name",
            "description",
            "date",
            "visibility",
            "type",
            "year",
            "sticker_url",
            "slug",
            "view",
        ]


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = [
            "id",
            "file_name",
            "file_extension",
            "file_full_name",
            "gallery",
            "link",
        ]


class YearSerializer(serializers.ModelSerializer):
    class Meta:
        model = Year
        fields = ["name"]


class PromoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promo
        fields = ["name", "first_year"]


class ReportSerializer(serializers.ModelSerializer):
    file_full_name = serializers.CharField(source="file.file_full_name", read_only=True)
    reporter_name = serializers.CharField(source="reporter.username", read_only=True)

    class Meta:
        model = Report
        fields = [
            "id",
            "file_full_name",
            "reporter_name",
            "category",
            "message",
            "created_at",
        ]
