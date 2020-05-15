"""Tests for Serializers in the Organizer App"""
from django.test import TestCase

from config.test_utils import (
    context_kwarg,
    get_instance_data,
    omit_keys,
    reverse,
)

from ..models import Startup, Tag
from ..serializers import (
    NewsLinkSerializer,
    StartupSerializer,
    TagSerializer,
)
from .factories import (
    NewsLinkFactory,
    StartupFactory,
    TagFactory,
)


class TagSerializerTests(TestCase):
    """Test Serialization of Tags in TagSerializer"""

    def test_serialization(self):
        """Does an existing Tag serialize correctly?"""
        tag = TagFactory()
        tag_url = reverse(
            "api-tag-detail", slug=tag.slug, full=True
        )
        s_tag = TagSerializer(tag, **context_kwarg(tag_url))
        self.assertEqual(
            omit_keys("url", s_tag.data),
            omit_keys("id", get_instance_data(tag)),
        )
        self.assertEqual(s_tag.data["url"], tag_url)

    def test_deserialization(self):
        """Can we deserialize data to a Tag model?"""
        tag_data = get_instance_data(TagFactory.build())
        s_tag = TagSerializer(
            data=tag_data, **context_kwarg("/api/v1/tag/")
        )
        self.assertTrue(s_tag.is_valid(), s_tag.errors)
        tag = s_tag.save()
        self.assertTrue(
            Tag.objects.filter(pk=tag.pk).exists()
        )

    def test_invalid_deserialization(self):
        """Does the serializer validate data?"""
        s_tag = TagSerializer(
            data={}, **context_kwarg("/api/v1/tag/")
        )
        self.assertFalse(s_tag.is_valid())


class StartupSerializerTests(TestCase):
    """Test Serialization of Startups in StartupSerializer"""

    def test_serialization(self):
        """Does an existing Startup serialize correctly?"""
        tag_list = TagFactory.create_batch(3)
        startup = StartupFactory(tags=tag_list)
        startup_url = reverse(
            "api-startup-detail",
            slug=startup.slug,
            full=True,
        )
        s_startup = StartupSerializer(
            startup, **context_kwarg(startup_url)
        )
        self.assertEqual(
            omit_keys("url", "tags", s_startup.data),
            omit_keys(
                "id", "tags", get_instance_data(startup)
            ),
        )
        tag_urls = [
            reverse(
                "api-tag-detail", slug=tag.slug, full=True
            )
            for tag in tag_list
        ]
        self.assertCountEqual(
            s_startup.data["tags"], tag_urls
        )
        self.assertEqual(s_startup.data["url"], startup_url)

    def test_deserialization(self):
        """Can we deserialize data to a Startup model?"""
        startup_data = get_instance_data(
            StartupFactory.build()
        )
        tag_urls = [
            reverse("api-tag-detail", slug=tag.slug)
            for tag in TagFactory.build_batch(3)
            + TagFactory.create_batch(2)
        ]
        data = dict(startup_data, tags=tag_urls)
        s_startup = StartupSerializer(
            data=data, **context_kwarg("/api/v1/startup/")
        )
        self.assertTrue(
            s_startup.is_valid(), msg=s_startup.errors
        )
        self.assertEqual(
            Startup.objects.count(),
            0,
            "Unexpected initial condition",
        )
        self.assertEqual(
            Tag.objects.count(),
            2,
            "Unexpected initial condition",
        )
        startup = s_startup.save()
        self.assertEqual(
            Startup.objects.count(),
            1,
            "Serialized Startup not saved",
        )
        self.assertCountEqual(
            startup.tags.values_list("slug", flat=True),
            [],
            "Startup had tags associated with it",
        )
        self.assertEqual(
            Tag.objects.count(), 2, "Serialized Tags saved"
        )

    def test_invalid_deserialization(self):
        """Does the serializer validate data?"""
        s_startup = StartupSerializer(
            data={}, **context_kwarg("/api/v1/startup/")
        )
        self.assertFalse(s_startup.is_valid())


class NewsLinkSerializerTests(TestCase):
    """Test Serialization of NewsLinks in NewsLinkSerializer"""

    def test_serialization(self):
        """Does an existing NewsLink serialize correctly?"""
        nl = NewsLinkFactory()
        nl_url = f"/api/v1/newslink/{nl.slug}"
        s_nl = NewsLinkSerializer(
            nl, **context_kwarg(nl_url)
        )
        self.assertNotIn("id", s_nl.data)
        self.assertIn("url", s_nl.data)
        self.assertEqual(
            omit_keys("url", "startup", s_nl.data),
            omit_keys(
                "id", "startup", get_instance_data(nl)
            ),
        )
        self.assertEqual(
            self.client.get(s_nl.data["url"]).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(
                s_nl.data["startup"]
            ).status_code,
            200,
        )

    def test_deserialization(self):
        """Can we deserialize data to a NewsLink model?"""
        startup_url = reverse(
            "api-startup-detail",
            slug=StartupFactory().slug,
            full=True,
        )
        nl_data = omit_keys(
            "startup",
            get_instance_data(NewsLinkFactory.build()),
        )
        data = dict(**nl_data, startup=startup_url)
        s_nl = NewsLinkSerializer(
            data=data, **context_kwarg("/api/v1/newslink/")
        )
        self.assertTrue(s_nl.is_valid(), msg=s_nl.errors)

    def test_invalid_deserialization(self):
        """Does the serializer validate data?"""
        s_nl = NewsLinkSerializer(
            data={}, **context_kwarg("/api/v1/newslink/")
        )
        self.assertFalse(s_nl.is_valid())
