# -*- coding: utf-8 -*-

import json

from django.http import JsonResponse, Http404
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from schematics.exceptions import ModelValidationError, ModelConversionError

from .serializers import (LinkCreateSerializer, LinkReadSerializer,
                          LinkUpdateSerializer)
from .models import Link, Tag


class CSRFExemptMixin(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(CSRFExemptMixin, self).dispatch(*args, **kwargs)


class LinkListView(CSRFExemptMixin):
    http_method_names = ['post', 'get']

    def post(self, request):
        data = json.loads(request.body.decode())
        try:
            link = LinkCreateSerializer(raw_data=data)
            link.validate()
            kwargs = link.to_native()
            # Pop tags since objects will be created separately
            tags = kwargs.pop('tags', None)

            # Persist the data
            link_obj = Link.objects.create(**kwargs)
            tag_collection = [Tag.objects.get_or_create(title=tag)[0]
                              for tag in tags]
            link_obj.attach_tags(tag_collection)

            # Prepare for response
            return_data = LinkReadSerializer(link_obj.to_dict()).to_native()
            return JsonResponse(data=return_data, status=201)
        except (ModelValidationError, ModelConversionError) as e:
            return JsonResponse(e.messages, status=400)

    def get(self, request):
        # TODO: Add pagination
        links = Link.objects.all()
        items = [LinkReadSerializer(link.to_dict()).to_native()
                 for link in links]
        data = {'items': items, 'total': len(links)}

        return JsonResponse(data=data)


class LinkDetailView(CSRFExemptMixin):
    http_method_names = ['delete', 'get', 'patch']

    def get_or_404(self, pk):
        try:
            return Link.objects.get(pk=pk)
        except Link.DoesNotExist:
            raise Http404("Link doesn't exist")

    def get(self, request, pk):
        link = self.get_or_404(pk=pk)
        return_data = LinkReadSerializer(link.to_dict()).to_native()
        return JsonResponse(return_data)

    def delete(self, request, pk):
        link = self.get_or_404(pk=pk)
        link.delete()
        return JsonResponse(data={}, status=204)

    def patch(self, request, pk):
        data = json.loads(request.body.decode())
        try:
            link = LinkUpdateSerializer(raw_data=data)
            kwargs = link.to_native()
            # We need to make two db calls any way to return Response
            link_obj = self.get_or_404(pk=pk)
            link_obj.update(**kwargs)
            # Prepare response
            data = LinkReadSerializer(link_obj.to_dict()).to_native()
            return JsonResponse(data=data, status=202)
        except ModelConversionError as e:
            # this is raised when fields are missing
            msg = "PATCH not allowed."
            data = {field: msg for field, value in e.messages.items()}
            return JsonResponse(data=data, status=400)
        except ModelValidationError as e:
            return JsonResponse(e.messages, status=400)
