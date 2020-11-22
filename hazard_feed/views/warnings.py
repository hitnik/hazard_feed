from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from ..models import  HazardFeeds, HazardLevels
from ..serializers import HazardWarningsSerializer, HazardLevelModelSerializer
from django_filters import rest_framework as filters


class HazardWarningsPageNumberPagination(PageNumberPagination):
    page_size = 5
    max_page_size = 20
    page_size_query_param = 'page_size'



class HazardLevelsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = HazardLevels.objects.all()
    serializer_class = HazardLevelModelSerializer


class DateFilterSet(filters.FilterSet):
    date_end = filters.DateFromToRangeFilter()
    date_start = filters.DateFromToRangeFilter()

    class Meta:
        model = HazardFeeds
        fields = ['date_end', 'date_start']

class HazardWarningsAPIViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = HazardFeeds.objects.all().order_by('date').reverse()
    serializer_class = HazardWarningsSerializer
    pagination_class = HazardWarningsPageNumberPagination
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = DateFilterSet



