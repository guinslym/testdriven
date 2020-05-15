"""Tests for Blog Views"""
import json
from functools import partial
from random import randint

from test_plus import APITestCase

from config.test_utils import (
    context_kwarg,
    get_instance_data,
    omit_keys,
    reverse,
)

from ..models import Post
from ..serializers import PostSerializer
from .factories import (
    PostFactory,
    StartupFactory,
    TagFactory,
)

remove_m2m = partial(omit_keys, "tags", "startups")


class PostAPITests(APITestCase):
    """Test API views for Post objects"""

    @property
    def response_json(self):
        """Shortcut to obtain JSON from last response"""
        return json.loads(self.last_response.content)

    def test_list(self):
        """Is there a list of Post objects"""
        url_name = "api-post-list"
        post_list = PostFactory.create_batch(10)
        self.get_check_200(url_name)
        self.assertCountEqual(
            self.response_json,
            PostSerializer(
                post_list,
                many=True,
                **context_kwarg(reverse(url_name)),
            ).data,
        )

    def test_list_404(self):
        """Do we return an empty list if no posts?"""
        self.get_check_200("api-post-list")

    def test_list_create(self):
        """Can we create Posts via the POST to list view?"""
        count = Post.objects.count()
        self.post(
            "api-post-list",
            data=remove_m2m(
                get_instance_data(PostFactory.build())
            ),
        )
        self.response_201()
        self.assertEqual(count + 1, Post.objects.count())

    def test_list_create_m2m(self):
        """Can new Posts be related with tags & startups?"""
        count = Post.objects.count()
        tag_list = TagFactory.create_batch(randint(1, 10))
        tag_urls = [
            reverse("api-tag-detail", slug=tag.slug)
            for tag in tag_list
        ]
        startup_list = StartupFactory.create_batch(
            randint(1, 10)
        )
        startup_urls = [
            reverse("api-startup-detail", slug=startup.slug)
            for startup in startup_list
        ]
        post = PostFactory.build()
        self.post(
            "api-post-list",
            data=dict(
                remove_m2m(get_instance_data(post)),
                tags=tag_urls,
                startups=startup_urls,
            ),
        )
        self.response_201()
        self.assertEqual(count + 1, Post.objects.count())
        post = Post.objects.get(
            slug=post.slug, pub_date=post.pub_date
        )
        self.assertCountEqual(tag_list, post.tags.all())
        self.assertCountEqual(
            startup_list, post.startups.all()
        )

    def test_detail(self):
        """Is there a detail view for a Post object"""
        post = PostFactory()
        url = reverse(
            "api-post-detail",
            year=post.pub_date.year,
            month=post.pub_date.month,
            slug=post.slug,
        )
        self.get_check_200(url)
        self.assertCountEqual(
            self.response_json,
            PostSerializer(post, **context_kwarg(url)).data,
        )

    def test_detail_404(self):
        """Do we generate 404 if post not found?"""
        self.get(
            "api-post-detail",
            year=2018,
            month=8,
            slug="now-recording",
        )
        self.response_404()

    def test_detail_update(self):
        """Can we update a Post via PUT?"""
        post = PostFactory(title="first")
        count = Post.objects.count()
        tag_list = TagFactory.create_batch(randint(1, 10))
        tag_urls = [
            reverse("api-tag-detail", slug=tag.slug)
            for tag in tag_list
        ]
        startup_list = StartupFactory.create_batch(
            randint(1, 10)
        )
        startup_urls = [
            reverse("api-startup-detail", slug=startup.slug)
            for startup in startup_list
        ]
        self.put(
            "api-post-detail",
            year=post.pub_date.year,
            month=post.pub_date.month,
            slug=post.slug,
            data=dict(
                remove_m2m(get_instance_data(post)),
                title="second",
                tags=tag_urls,
                startups=startup_urls,
            ),
        )
        self.response_200()
        self.assertEqual(count, Post.objects.count())
        post.refresh_from_db()
        self.assertEqual("second", post.title)
        self.assertCountEqual(tag_list, post.tags.all())
        self.assertCountEqual(
            startup_list, post.startups.all()
        )

    def test_detail_update_404(self):
        """Do we generate 404 if post not found?"""
        self.put(
            "api-post-detail",
            year=2018,
            month=11,
            slug="post-recording",
        )
        self.response_404()

    def test_detail_partial_update(self):
        """Can we update a Post via PATCH?

        The "gotcha" with patch is that it overwrites
        relations! This may be desirable, or it may be a
        disadvantage when compared to custom viewset
        actions.
        """
        post = PostFactory(
            title="first",
            tags=TagFactory.create_batch(randint(1, 10)),
            startups=StartupFactory.create_batch(
                randint(1, 10)
            ),
        )
        count = Post.objects.count()
        tag_list = TagFactory.create_batch(randint(1, 10))
        tag_urls = [
            reverse("api-tag-detail", slug=tag.slug)
            for tag in tag_list
        ]
        startup_list = StartupFactory.create_batch(
            randint(1, 10)
        )
        startup_urls = [
            reverse("api-startup-detail", slug=startup.slug)
            for startup in startup_list
        ]
        self.patch(
            "api-post-detail",
            year=post.pub_date.year,
            month=post.pub_date.month,
            slug=post.slug,
            data=dict(
                title="second",
                # necessary due to bug in DRF
                # https://github.com/encode/django-rest-framework/issues/6341
                slug=post.slug,
                pub_date=post.pub_date,
                # remove above once DRF fixed
                tags=tag_urls,
                startups=startup_urls,
            ),
        )
        self.response_200()
        self.assertEqual(count, Post.objects.count())
        post.refresh_from_db()
        self.assertEqual("second", post.title)
        self.assertCountEqual(tag_list, post.tags.all())
        self.assertCountEqual(
            startup_list, post.startups.all()
        )

    def test_detail_partial_update_404(self):
        """Do we generate 404 if post not found?"""
        self.patch(
            "api-post-detail",
            year=2018,
            month=11,
            slug="post-recording",
        )
        self.response_404()

    def test_detail_delete(self):
        """Can we delete a post?"""
        post = PostFactory()
        self.delete(
            "api-post-detail",
            year=post.pub_date.year,
            month=post.pub_date.month,
            slug=post.slug,
        )
        self.response_204()
        self.assertFalse(
            Post.objects.filter(pk=post.pk).exists()
        )

    def test_detail_delete_404(self):
        """Do we generate 404 if post not found?"""
        self.delete(
            "api-post-detail",
            year=2018,
            month=11,
            slug="nonexistent",
        )
        self.response_404()
